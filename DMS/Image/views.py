from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet, CharFilter
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db import transaction
from django.db.models import Count, F, Q

import os, time, re
from collections import Counter
import django_excel as excel
from djqscsv import render_to_csv_response
from DMS.settings.dev import DATA_SAMBA_IMAGE_LOCATE, DATA_SAMBA_PREX, TRASH_FILE_PATH

from Image.models import Image
from Image.serializers import ImageSerializer, DupImageSerializer
from Case.models import Case
from DiagnoseZhu.models import DiagnoseZhu
from Train.models import TrainedImage

import logging
logger = logging.getLogger('django')


class StatisticView(APIView):
    """
    get: 首页统计信息
    """

    def get(self, request):

        # 1. 病例/大图数量
        case_count = Case.objects.filter(is_delete=False).count()
        image_count = Image.objects.filter(is_delete=False).count()

        # 2. 大图诊断结果标签

        # 查询朱博士诊断不为空或医生诊断不为空的记录
        all_diagnosis_label = Image.objects.filter(
            Q(is_delete=False), Q(diagnosis_label_doctor__isnull=False) | Q(diagnosis_label_zhu__isnull=False)
        )
        # 有医生或朱博士诊断标签的 及 诊断记录均为Null的记录数
        has_diagnosis_count = all_diagnosis_label.count()
        # diagnosis_null_count = image_count - has_diagnosis_count

        # 初始化列表, 用于存储所有的诊断结果, 优先朱博士诊断
        diagnosis_label_list = []
        for diag in all_diagnosis_label:
            if diag.diagnosis_label_zhu:
                # 数据清洗
                # 1.如果诊断结果有LiSIL+ASCUS, 则取+前第一个
                # 2.去除两边的空格 3.统一转换成大写 4.AGC1/AGC2统一为AGC,因此要统一将数字去掉
                diagnosis_label_list.append(diag.diagnosis_label_zhu.split('+')[0].strip().upper().strip('123'))
            else:
                diagnosis_label_list.append(diag.diagnosis_label_doctor.split('+')[0].strip().upper().strip('123'))

        # 统计每个分类的个数
        diag_label_dict = dict(Counter(diagnosis_label_list))
        diag_label_count_list = []
        # 转换成列表字典格式
        for label, count in diag_label_dict.items():
            tmp_dict = {}
            tmp_dict['diagnosis_label'] = label
            tmp_dict['diagnosis_label_count'] = count
            diag_label_count_list.append(tmp_dict)

        # 3.片源

        # 3.1 各类数量：
        # 统计各类标签不含null值的个数
        wp_source_count = Image.objects.filter(is_delete=False, waveplate_source__isnull=False).values(
            'waveplate_source').annotate(
            waveplate_source_count=Count('waveplate_source')
        ).order_by('waveplate_source_count')
        # 统计各类标签为null值的个数
        wp_source_null_count = Image.objects.filter(is_delete=False, waveplate_source__isnull=True).count()
        wp_source_null_dict = {
            'waveplate_source_count': wp_source_null_count,
            'waveplate_source': None
        }

        # 合并并转换成列表
        wp_source_count_list = list(wp_source_count)
        # 如果有空值, 则把空值的统计也添加上, 否则不需要统计空值的个数及占比
        if wp_source_null_count:
            wp_source_count_list.append(wp_source_null_dict)

        # 3.2 各类占比：
        for num in wp_source_count_list:
            num['wp_source_prop'] = '%.3f' % (num['waveplate_source_count'] / case_count * 100) + '%'

        # 4. 倍数

        # 4.1 各类数量：
        # 统计各类倍数不含null值的个数
        resolution_count = Image.objects.filter(is_delete=False, resolution__isnull=False).values(
            'resolution').annotate(
            resolution_count=Count('resolution')
        ).order_by('resolution')

        # 转换成列表
        resolution_count_list = list(resolution_count)

        # 4.2 各类占比：
        for num in resolution_count_list:
            num['label_prop'] = '%.3f' % (num['resolution_count'] / image_count * 100) + '%'

        # ----- 返回结果 ------ #
        result_dict = {
            'case_count': case_count,
            'image_count': image_count,
            'has_diagnosis_count': has_diagnosis_count,
            'diag_label_count': diag_label_count_list,
            'waveplate_source_count': wp_source_count_list,
            'resolution_count': resolution_count_list
        }
        return Response(status=status.HTTP_200_OK, data=result_dict)


class FindDuplicateFileName(APIView):
    """查找大图中出现重复的文件名"""

    def get(self, request):
        # 查询（文件名和倍数）分组，查找出现的次数大于1的记录
        dup_file_name = Image.objects.filter(is_delete=False).values('file_name', 'resolution').annotate(
            dup_count=Count('id')).filter(dup_count__gt=1).order_by('-dup_count')

        # 创建分页对象
        pg = LimitOffsetPagination()

        # 获取分页的数据
        page_roles = pg.paginate_queryset(queryset=dup_file_name, request=request, view=self)

        # 序列化返回
        # 查询多条重复记录, 因此需要指定many=True, 并指定instance
        serializer = DupImageSerializer(instance=page_roles, many=True)

        # 不含上一页和下一页，要手动的在url中传参limit和offset来控制第几页
        # return Response(status=status.HTTP_200_OK, data=serializer.data)
        # 使用get_paginated_response, 则含上一页和下一页
        return pg.get_paginated_response(data=serializer.data)


class DownloadFile(APIView):
    """
    get: 导出csv/excel数据
    :parameter:
        type: 指定下载的格式, csv/xlsx/xls
    :example:
        /api/v1/images/downloads/?type=csv
    """

    def get(self, request):

        suffix_name = request.GET.get('type', None)
        if not suffix_name:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'msg': '请求参数错误！'})

        if suffix_name not in ['csv', 'xlsx', 'xls']:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'msg': '仅支持下载csv和excel格式！'})

        # 通过指定字段的别名, 指定返回的格式顺序, 下载时默认按字母进行排序
        img_data = Image.objects.filter(is_delete=False).annotate(
            c1_病理号=F('pathology'), c2_文件名=F('file_name'),
            c3_分辨率=F('resolution'), c4_存储路径=F('storage_path'),
            c5_片源=F('waveplate_source'), c6_切片制式=F('making_way'),
            c7_是否学习=F('is_learn'), c8_医生诊断标签=F('diagnosis_label_doctor'),
            c9_朱博士诊断标签=F('diagnosis_label_zhu')).values(
            'c1_病理号', 'c2_文件名', 'c3_分辨率', 'c4_存储路径', 'c5_片源',
            'c6_切片制式', 'c7_是否学习', 'c8_医生诊断标签', 'c9_朱博士诊断标签')

        # 命名返回文件名字(django-queryset-csv插件使用中文名字返回时会去掉, 使用英文则不会)
        file_name_add_date = 'image_' + time.strftime('%Y_%m_%d_%H_%M_%S') + '.{}'.format(suffix_name)

        # 返回对应格式的文件
        # 返回csv格式使用make_response_from_records会出现中文乱码,
        # pyexcel主要用于上传下载excel类型的数据,因此要改用其它框架django-queryset-csv
        if suffix_name == 'csv':
            # 指定返回字段的顺序
            field_name_list = sorted(list(img_data[0].keys()))
            return render_to_csv_response(img_data, filename=file_name_add_date, field_order=field_name_list)
        else:
            return excel.make_response_from_records(img_data, file_type=suffix_name, file_name=file_name_add_date)


class UpdateDataBase(APIView):
    """
    post: 更新数据库中的大图数据表
    :parameter:
        update_type: 指定更新类型
    :example:
        请求体中带上 {“update_type”: “db”}
    """

    @staticmethod
    def timestamp_to_time(timestamp):
        """将时间戳类型转换成时间类型"""

        time_struct = time.localtime(timestamp)
        return time.strftime('%Y-%m-%d %H:%M:%S', time_struct)

    @staticmethod
    def rename_file_name(file_name):
        """修改文件名(根据病理号)"""

        # 如果文件名是长度为19的话，则说明是日期，则病理号等于文件名
        # 如果文件夹中没有下划线,则返回原字符串,否则会切分字符串超过2个, 但是也取第一个,因此匹配到还是匹配不到都取第一个
        pathology = file_name if len(file_name) == 19 else file_name.split('_')[0]
        return pathology

    @staticmethod
    def waveplate_source_extra(file_name):
        """通过病理号提取出片源"""

        upper_pathology = file_name.split('_')[0].upper()

        if upper_pathology.startswith('TJ') or upper_pathology.startswith(
                'TB') or upper_pathology.startswith('TC') or upper_pathology.startswith(
                'TD') or upper_pathology.startswith('DS') or upper_pathology.startswith('CA'):
            waveplate_source = '华银'

        elif upper_pathology.startswith('T'):
            waveplate_source = '泉州'

        elif upper_pathology.startswith('NJ'):
            waveplate_source = '华银南京'

        elif upper_pathology.startswith('SPH') or upper_pathology.startswith('SZH'):
            waveplate_source = '深圳人民医院'

        elif upper_pathology.startswith('EL') or upper_pathology.startswith('L'):
            waveplate_source = '郑大一附属医院'

        elif upper_pathology.startswith('GZY'):
            waveplate_source = '广州军区总医院'

        elif upper_pathology.startswith('BD') or upper_pathology.startswith('XB') or upper_pathology.startswith(
                'FX') or upper_pathology.startswith('BV') or upper_pathology.startswith(
                'ZA') or upper_pathology.isdigit():
            waveplate_source = '南方医院'

        elif re.match('\d{4}-\d{2}-\d{2}', upper_pathology):
            waveplate_source = '南方医院或华银'

        else:
            waveplate_source = 'unknown'

        return waveplate_source

    def post(self, request):

        start_time = time.time()

        # 获取请求体数据
        update_type = request.POST.get('update_type', None)
        if update_type != 'db':
            return Response(status=status.HTTP_403_FORBIDDEN, data={'msg': '请求参数错误！'})

        # 开启事务
        with transaction.atomic():
            # 创建保存点
            save_id = transaction.savepoint()

            try:
                # 删除表中没有逻辑删除的记录,那些已逻辑删除的要保存记录下来
                Image.objects.filter(is_delete=False).delete()

                # 方案1：先查询出已训练数据,然后再给下面的is_delete去判断在不在里面,提高效率,不用每次去查询表
                train_data_file_name = list(TrainedImage.objects.values_list('file_name', flat=True))

                # 定义列表,存储多条数据库数据对象
                queryset_list = []
                # 遍历0TIFF目录,获取信息,并保存到数据库
                for resolution in ['20X', '40X']:
                    for root, dirs, files in os.walk(
                            os.path.join(DATA_SAMBA_PREX, DATA_SAMBA_IMAGE_LOCATE, resolution), topdown=False):
                        # 只遍历文件夹下的所有文件
                        for name in files:
                            # --------------------- 文件名 --------------------- #
                            file_name, suffix_name = os.path.splitext(name)
                            # --------------------- 病理号 --------------------- #
                            pathology = self.rename_file_name(file_name)
                            # --------------------- 片源 ----------------------- #
                            waveplate_source = self.waveplate_source_extra(file_name)
                            # --------------------- 存储路径 --------------------- #
                            storage_path = root.split('=')[2]
                            # --------------- 文件创建时间（扫描时间）------------------ #
                            file_create_time_ts = os.path.getctime(os.path.join(root, name))
                            scan_time = self.timestamp_to_time(file_create_time_ts)
                            # --------------------- 是否学习 --------------------- #
                            is_learn = True if file_name in train_data_file_name else False
                            # --------------------- 查询病例信息(片源,制式,医生诊断) --------------------- #
                            case = Case.objects.filter(pathology=pathology, is_delete=False).values(
                                'waveplate_source', 'diagnosis_label_doctor', 'making_way')
                            if case:
                                if case.count() >= 2:
                                    # 拼接病理号相同的诊断结果
                                    diagnosis_label_doctor_list = [i['diagnosis_label_doctor'] for i in case if
                                                                   i['diagnosis_label_doctor'] is not None]
                                    diagnosis_label_doctor = '+'.join(
                                        diagnosis_label_doctor_list) if diagnosis_label_doctor_list else None
                                    making_way = case.filter(making_way__isnull=False).first().get('making_way')
                                else:
                                    diagnosis_label_doctor = case.first().get('diagnosis_label_doctor')
                                    making_way = case.first().get('making_way')
                            else:
                                # 匹配不上,则为None
                                diagnosis_label_doctor = None
                                making_way = None
                            # --------------------- 朱博士最新诊断标签 --------------------- #
                            try:
                                diag = DiagnoseZhu.objects.filter(pathology=pathology).order_by('-create_time')
                                diagnosis_label_zhu = [i.his_diagnosis_label.split(',')[0] for i in diag][0]
                            except Exception as e:
                                diagnosis_label_zhu = None

                            # 创建一条记录对象, 并添加到列表
                            queryset_list.append(Image(pathology=pathology, file_name=file_name, suffix=suffix_name,
                                                       storage_path=storage_path, resolution=resolution,
                                                       diagnosis_label_doctor=diagnosis_label_doctor,
                                                       diagnosis_label_zhu=diagnosis_label_zhu, is_learn=is_learn,
                                                       waveplate_source=waveplate_source, making_way=making_way,
                                                       scan_time=scan_time))

                # 每次save()的时候都会访问一次数据库，导致性能问题。
                # 使用django.db.models.query.QuerySet.bulk_create()批量创建对象，减少SQL查询次数
                Image.objects.bulk_create(queryset_list)

            except Exception as e:
                logger.error(e)
                transaction.savepoint_rollback(save_id)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'msg': '数据保存到数据库失败！'})

            # 提交事务
            transaction.savepoint_commit(save_id)

            end_time = time.time()
            cost_time = '%.2f' % (end_time - start_time)

            return Response(status=status.HTTP_201_CREATED, data={'msg': '数据库更新成功！', 'cost_time': cost_time})


class ImageFilter(FilterSet):
    """搜索类"""

    id = CharFilter(lookup_expr='iexact')  # 精确查询
    pathology = CharFilter(lookup_expr='icontains')  # 模糊查询（包含），并且忽略大小写
    file_name = CharFilter(lookup_expr='icontains')  # 模糊查询（包含），并且忽略大小写
    resolution = CharFilter(lookup_expr='iexact')  # 精确查询
    storage_path = CharFilter(lookup_expr='iexact')  # 精确查询
    waveplate_source = CharFilter(lookup_expr='icontains')  # 模糊查询（包含），并且忽略大小写
    diagnosis_label_doctor = CharFilter(lookup_expr='icontains')  # 模糊查询（包含），并且忽略大小写
    diagnosis_label_zhu = CharFilter(lookup_expr='icontains')  # 模糊查询（包含），并且忽略大小写
    is_learn = CharFilter(lookup_expr='iexact')  # 精确查询

    class Meta:
        model = Image
        fields = ['id', 'pathology', 'file_name', 'resolution', 'storage_path', 'waveplate_source',
                  'diagnosis_label_doctor', 'diagnosis_label_zhu', 'is_learn']


class ExactImageFilter(FilterSet):
    """搜索类"""

    id = CharFilter(lookup_expr='iexact')  # 精确查询
    file_name = CharFilter(lookup_expr='iexact')  # 精确查询，并且忽略大小写
    storage_path = CharFilter(lookup_expr='iexact')  # 精确查询，并且忽略大小写

    class Meta:
        model = Image
        fields = ['id', 'file_name', 'storage_path']


class SImageView(ListAPIView):
    """
    get: 查询大图列表
    """

    # 指定查询集, 获取没有逻辑删除的数据
    queryset = Image.objects.filter(is_delete=False).order_by('-scan_time')

    # 指定序列化器
    serializer_class = ImageSerializer

    # OrderingFilter：指定排序的过滤器,可以按任意字段排序,通过在路由中通过ordering参数控制,如：?ordering=id
    # DjangoFilterBackend对应filter_fields属性，做相等查询
    # SearchFilter对应search_fields，对应模糊查询
    filter_backends = [OrderingFilter, DjangoFilterBackend, SearchFilter]
    # 默认指定按哪个字段进行排序
    ordering_fields = ('pathology', )
    # 指定可以被搜索字段
    filter_class = ExactImageFilter


class SelectExactImageView(ListAPIView):
    """
    get: 根据病理号精确查询病例记录列表
    """

    # 指定查询集, 获取没有逻辑删除的数据
    queryset = Image.objects.filter(is_delete=False).order_by('-scan_time')

    # 指定序列化器
    serializer_class = ImageSerializer

    # OrderingFilter：指定排序的过滤器,可以按任意字段排序,通过在路由中通过ordering参数控制,如：?ordering=id
    # DjangoFilterBackend对应filter_fields属性，做相等查询
    # SearchFilter对应search_fields，对应模糊查询
    filter_backends = [OrderingFilter, DjangoFilterBackend, SearchFilter]
    # 默认指定按哪个字段进行排序
    ordering_fields = ('pathology', )
    # 指定可以被搜索字段
    filter_class = ImageFilter


class SDoctorZhuDiagnoseView(APIView):
    """
    get: 查询朱博士或医生有诊断标签的大图记录
    """

    def get(self, request, diagnose_label):

        # 查询朱博士或医生有诊断标签的大图记录
        image = Image.objects.filter(
            Q(is_delete=False),
            Q(diagnosis_label_doctor__icontains=diagnose_label) | Q(diagnosis_label_zhu__icontains=diagnose_label)
        )

        if not image:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '该诊断标签不存在！'})

        # 创建分页对象
        pg = LimitOffsetPagination()

        # 获取分页的数据
        page_roles = pg.paginate_queryset(queryset=image, request=request, view=self)

        # 序列化返回
        # 查询多条重复记录, 因此需要指定many=True, 并指定instance
        serializer = ImageSerializer(instance=page_roles, many=True)

        # 不含上一页和下一页，要手动的在url中传参limit和offset来控制第几页
        # return Response(status=status.HTTP_200_OK, data=serializer.data)
        # 使用get_paginated_response, 则含上一页和下一页
        return pg.get_paginated_response(data=serializer.data)


class SUDImageView(APIView):
    """
    get: 查询一条大图数据
    patch: 更新一条大图数据
    delete: 逻辑删除一条大图数据
    """

    def get(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            image = Image.objects.get(id=pk, is_delete=False)
        except Image.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})

        # 序列化返回
        serializer = ImageSerializer(image)
        return Response(serializer.data)

    def patch(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            image = Image.objects.get(id=pk, is_delete=False)
        except Image.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})

        # 获取参数, 校验参数, 保存结果
        serializer = ImageSerializer(image, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def delete(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            image = Image.objects.get(id=pk, is_delete=False)
        except Image.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})

        try:
            # 数据库中逻辑删除
            image.is_delete = True
            image.save()
        except Exception as e:
            logger.warning(e)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'msg': '数据库删除失败！'})

        return Response(status=status.HTTP_204_NO_CONTENT, data={'msg': '删除成功！'})


class UUpdateQuality(APIView):

    """
    patch: 更新大图质量字段
    """

    def patch(self, request):

        # 获取大图病理号, 及质量字段
        file_name = request.data.get('pathology', None)
        img_quality = request.data.get('image_quality', None)
        if not img_quality or not file_name:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'msg': '参数错误！'})

        # 通过文件名进行查询(会忽略大小写, 同时去除两边的空格)
        img = Image.objects.filter(file_name=file_name.strip(), is_delete=False)
        if not img:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '该病理号不存在！'})

        # 修改图像质量
        img.update(quality=img_quality)
        # 序列化修改成功的数据返回, 使用filter查询出来可能有多少, 因此要加many=True, 而使用get只能有一条, 可不加
        ser = ImageSerializer(img, many=True)

        return Response(status=status.HTTP_200_OK, data={'results': ser.data})
