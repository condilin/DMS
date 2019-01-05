from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db import transaction
from django.db.models import Count

import shutil
import os
import time
import django_excel as excel
from DMS.settings.dev import DATA_SAMBA_IMAGE_LOCATE, DATA_SAMBA_PREX, TRASH_FILE_PATH

from Image.models import Image
from Image.serializers import ImageSerializer
from Case.models import Case


class StatisticView(APIView):
    """
    get: 首页统计信息
    """

    def get(self, request):
        # ----- 病例信息表 ------ #

        # 1. 病例数量
        case_count = Case.objects.count()

        # 2. 诊断结果标签

        # 2.1 各类数量：
        # 统计各类标签不含null值的个数
        diag_label_count = Case.objects.filter(is_delete=False, diagnosis_label_doctor_filter__isnull=False).values(
            'diagnosis_label_doctor_filter').annotate(
            diagnosis_label_count=Count('diagnosis_label_doctor_filter')
        ).order_by('diagnosis_label_count')

        # 统计各类标签为null值的个数
        label_null_count = Case.objects.filter(is_delete=False, diagnosis_label_doctor_filter__isnull=True).count()
        label_null_dict = {
            'diagnosis_label_count': label_null_count,
            'diagnosis_label_doctor': None
        }

        # 合并并转换成列表
        diag_label_count_list = list(diag_label_count)
        # 如果有空值, 则把空值的统计也添加上, 否则不需要统计空值的个数及占比
        if diag_label_count:
            diag_label_count_list.append(label_null_dict)

        # 2.2 各类占比：
        for num in diag_label_count_list:
            num['label_prop'] = '%.3f' % (num['diagnosis_label_count'] / case_count * 100) + '%'

        # 3.片源

        # 3.1 各类数量：
        # 统计各类标签不含null值的个数
        wp_source_count = Case.objects.filter(is_delete=False, waveplate_source__isnull=False).values(
            'waveplate_source').annotate(
            waveplate_source_count=Count('waveplate_source')
        ).order_by('waveplate_source_count')
        # 统计各类标签为null值的个数
        wp_source_null_count = Case.objects.filter(is_delete=False, waveplate_source__isnull=True).count()
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

        # ----- 大图信息表 ------ #

        # 大图数量
        image_count = Image.objects.count()

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
            dup_count=Count('file_name', 'resolution')).filter(dup_count__gt=1)
        # 转换成列表
        dup_file_name_list = list(dup_file_name)

        # ----- 返回结果 ------ #
        result_dict = {
            "dup_file_name": dup_file_name_list
        }
        return Response(status=status.HTTP_200_OK, data=result_dict)


class DownloadFile(APIView):
    """
    get: 导出csv/excel数据
    :parameter:
        type: 指定下载的格式, csv/xlsx/xls
    :example:
        /api/v1/cases/downloads/?type=csv
    """

    def get(self, request):

        suffix_name = request.GET.get('type', None)
        if not suffix_name:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'msg': '请求参数错误！'})

        if suffix_name not in ['csv', 'xlsx', 'xls']:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'msg': '仅支持下载csv和excel格式！'})

        img_data = Image.objects.values('pathology', 'file_name', 'resolution', 'storage_path', 'waveplate_source',
                                        'making_way', 'is_learn', 'diagnosis_label_zhu', 'diagnosis_label_doctor')

        # 返回对应格式的文件
        return excel.make_response_from_records(img_data, file_type=suffix_name, file_name='大图信息')


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

                # 方案1：先查询出训练数据的详细信息,然后再给下面的is_delete去判断在不在里面,提高效率,不用每次去查询表？？？？？！！！！
                # train_data_file_name = Table.object.filter(file_name=file_name)
                # 方案2：使用F对象

                # 定义列表,存储多条数据库数据对象
                queryset_list = []
                # 遍历0TIFF目录,获取信息,并保存到数据库
                for resolution in ['20X', '40X']:
                    a = os.path.join(DATA_SAMBA_IMAGE_LOCATE, resolution)
                    for root, dirs, files in os.walk(os.path.join(DATA_SAMBA_IMAGE_LOCATE, resolution), topdown=False):
                        # 只遍历文件夹下的所有文件
                        for name in files:
                            # --------------------- 文件名 --------------------- #
                            file_name, suffix_name = os.path.splitext(name)
                            # --------------------- 病理号 --------------------- #
                            pathology = self.rename_file_name(file_name)
                            # --------------- 文件创建时间（扫描时间）------------------ #
                            file_create_time_ts = os.path.getctime(os.path.join(root, name))
                            scan_time = self.timestamp_to_time(file_create_time_ts)
                            # --------------------- 是否学习 --------------------- #
                            # is_learn = True if file_name in train_data_file_name else False
                            # --------------------- 查询病例信息(片源,制式,医生诊断) --------------------- #
                            case = Case.objects.filter(pathology=pathology).values(
                                'waveplate_source', 'diagnosis_label_doctor', 'making_way')
                            if case:
                                if case.count() >= 2:
                                    diagnosis_label_doctor = '?: %s条病例信息' % case.count()
                                    waveplate_source = case.filter(waveplate_source__isnull=False).first().get('waveplate_source')
                                    making_way = case.filter(waveplate_source__isnull=False).first().get('making_way')
                                else:
                                    diagnosis_label_doctor = case.first().get('diagnosis_label_doctor')
                                    waveplate_source = case.first().get('waveplate_source')
                                    making_way = case.first().get('making_way')
                            else:
                                # 匹配不上,则为None
                                diagnosis_label_doctor = None
                                waveplate_source = None
                                making_way = None
                            # 创建一条记录对象, 并添加到列表
                            queryset_list.append(Image(pathology=pathology, file_name=file_name,
                                                       storage_path=root, resolution=resolution,
                                                       diagnosis_label_doctor=diagnosis_label_doctor,
                                                       waveplate_source=waveplate_source, making_way=making_way,
                                                       scan_time=scan_time))

                # 每次save()的时候都会访问一次数据库，导致性能问题。
                # 使用django.db.models.query.QuerySet.bulk_create()批量创建对象，减少SQL查询次数
                Image.objects.bulk_create(queryset_list)

            except Exception as e:
                # 回滚
                transaction.savepoint_rollback(save_id)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'msg': '数据保存到数据库失败！'})

            # 提交事务
            transaction.savepoint_commit(save_id)

            end_time = time.time()
            cost_time = '%.2f' % (end_time - start_time)

            return Response(status=status.HTTP_201_CREATED, data={'msg': '数据库更新成功！', 'cost_time': cost_time})


class SImageView(ListAPIView):
    """
    get: 查询大图列表
    """

    # 指定查询集, 获取没有逻辑删除的数据
    queryset = Image.objects.filter(is_delete=False)

    # 指定序列化器
    serializer_class = ImageSerializer

    # OrderingFilter：指定排序的过滤器,可以按任意字段排序,通过在路由中通过ordering参数控制,如：?ordering=id
    # DjangoFilterBackend对应filter_fields属性，做相等查询
    # SearchFilter对应search_fields，对应模糊查询
    filter_backends = [OrderingFilter, DjangoFilterBackend, SearchFilter]
    # 默认指定按哪个字段进行排序
    ordering = ('pathology',)
    # 指定可以被搜索字段, 如在路由中通过?id=2查询id为2的记录
    filter_fields = ('id', 'pathology', 'file_name')


class SUDImageView(APIView):
    """
    get: 查询一条大图数据
    patch: 更新一条大图数据
    delete: 删除一条大图数据
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

        # 获取参数
        form_file_name = request.data.get('file_name', None)
        form_pathology = request.data.get('pathology', None)

        # 保存结果
        if form_file_name:
            try:
                # 更新data_samba中大图的文件名
                image_full_path = os.path.join(image.storage_path, image.file_name + '.kfb')
                image_rename = os.path.join(image.storage_path, form_file_name + '.kfb')
                shutil.move(image_full_path, image_rename)
                # 更新数据库中大图的文件名
                image.file_name = form_file_name
                image.save()
            except Exception as e:
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'msg', '更新文件名失败！'})
        elif form_pathology:
            try:
                # 判断要修改的病理号和文件名是否一样
                if form_pathology != image.file_name:
                    return Response(status=status.HTTP_400_BAD_REQUEST, data={'msg': '病理号与文件名不一样！'})
                # 修改病理号
                image.pathology = form_pathology
                image.save()
            except Exception as e:
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={'msg': '更新病理号失败！'})
        else:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'msg': '参数错误, 只能修改文件名或病理号！'})

        # 返回更新的那条数据
        res = Image.objects.get(id=pk, is_delete=False)
        return Response(status=status.HTTP_200_OK, data={'pathology': res.pathology, 'file_name': res.file_name})

    def delete(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            image = Image.objects.get(id=pk, is_delete=False)
        except Image.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})

        try:
            # 在data_samba中将该大图移动到临时的文件(/TMP/GARBAGE)
            image_full_path = os.path.join(image.storage_path, image.file_name + '.kfb')
            trash_full_path = os.path.join(DATA_SAMBA_PREX, TRASH_FILE_PATH)
            # 如果目录不存在, 则创建
            if not os.path.exists(trash_full_path):
                os.mkdir(trash_full_path)
            shutil.move(image_full_path, trash_full_path)

            # 数据库中逻辑删除
            image.is_delete = True
            image.save()

        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            data={'msg': '移动图片到data_samba/TMP/IMAGE_GARBAGE失败, 可能原因是该图片不是.kfb图片！'})

        return Response(status=status.HTTP_204_NO_CONTENT, data={'msg': '删除成功！'})
