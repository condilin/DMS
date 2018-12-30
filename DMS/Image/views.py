from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db import transaction
from django.db.models import Count

import re
import os
import time
from DMS.settings.dev import DATA_SAMBA_IMAGE_LOCATE

from Image.models import Image
from Image.serializers import ImageSerializer
from Case.models import Case


class StatisticView(APIView):
    """获取统计信息"""

    def get(self, request):
        # ----- 病例信息 ------ #

        # 1. 病例数量
        case_count = Case.objects.count()

        # 2. 诊断结果标签

        # 2.1 各类数量：
        # 统计各类标签不含null值的个数
        diag_label_count = Case.objects.filter(is_delete=False, diagnosis_label_doctor__isnull=False).values(
            'diagnosis_label_doctor').annotate(
            diagnosis_label_count=Count('diagnosis_label_doctor')
        ).order_by('diagnosis_label_count')
        # 统计各类标签为null值的个数
        label_null_count = Case.objects.filter(is_delete=False, diagnosis_label_doctor__isnull=True).count()
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

        # ----- 大图信息 ------ #

        # # ----- 各倍数数量, 占比 ----- #
        # resolution_count = Image.objects.filter(is_delete=False).values('resolution').annotate(
        #     res_count=Count('resolution')
        # )
        # # 转换成列表
        # resolution_count_list = list(resolution_count)
        # # 添加倍数占比
        # for i in resolution_count_list:
        #     i['res_prop'] = '%.2f' % (i['res_count'] / case_count * 100) + '%'

        # ----- 返回结果 ------ #
        result_dict = {
            'case_count': case_count,
            'diag_label_count': diag_label_count_list,
            'waveplate_source_count': wp_source_count_list
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


class UpdateDataBase(APIView):
    """更新数据库中的大图信息表"""

    @staticmethod
    def timestamp_to_time(timestamp):
        time_struct = time.localtime(timestamp)
        return time.strftime('%Y-%m-%d %H:%M:%S', time_struct)

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
                # 删除表中的记录
                Image.objects.all().delete()

                # 先查询出训练数据的详细信息,然后再给下面的is_delete去判断在不在里面,提高效率,不用每次去查询表？？？？？！！！！
                # train_data_file_name = Table.object.filter(file_name=file_name)

                # 定义列表,存储多条数据库数据对象
                queryset_list = []
                # 遍历0TIFF目录,获取信息,并保存到数据库
                for resolution in ['20X', '40X']:
                    for root, dirs, files in os.walk(os.path.join(DATA_SAMBA_IMAGE_LOCATE, resolution)):
                        # 只遍历文件夹下的所有文件
                        for name in files:
                            # 文件名
                            file_name, suffix_name = os.path.splitext(name)
                            # 病理号（通过正则匹配，这个正则不太规范，要重写）
                            new_match = re.match(r'(.+)[-_]*(.*)', file_name)
                            pathology = new_match.group(1) if new_match else ''
                            # 文件创建时间（扫描时间）
                            file_create_time_ts = os.path.getctime(os.path.join(root, name))
                            # 是否学习
                            # is_learn = True if file_name in train_data_file_name else False
                            # 创建一条记录对象, 并添加到列表
                            queryset_list.append(Image(pathology=pathology, file_name=file_name,
                                                       storage_path=root, resolution=resolution,
                                                       scan_time=self.timestamp_to_time(file_create_time_ts)))

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

            return Response(status=status.HTTP_200_OK, data={'msg': '数据库更新成功！', 'cost_time': cost_time})


class SImageView(ListAPIView):
    """查询大图记录，创建大图记录"""

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


# ---------------------------------------------------- waiting ---------------------------------------------- #

class SUDImageView(APIView):
    """查询一条数据，更新大图数据，逻辑删除大图数据"""

    def get(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            image = Image.objects.get(id=pk, is_delete=False)
        except Image.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # 序列化返回
        serializer = ImageSerializer(image)
        return Response(serializer.data)

    def patch(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            image = Image.objects.get(id=pk, is_delete=False)
        except Image.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # 获取参数, 校验参数, 保存结果
        serializer = ImageSerializer(image, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 如果修改了文件名, 则同步修改病理号
        get_file_name = request.data.get('file_name', None)
        if get_file_name:
            new_match = re.match(r'(.+?)[-_](.+)', get_file_name)
            if new_match:
                image.pathology = new_match.group(1)
                image.save()

        return Response(serializer.data)

    def delete(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            image = Image.objects.get(id=pk, is_delete=False)
        except Image.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # 在data_samba中将该大图移动到临时的文件(新建一个作为垃圾桶)
        # image_full_path = os.path.join(settings.DATA_SAMBA_PREX, image.storage_path)
        # trash_full_path = os.path.join(settings.DATA_SAMBA_PREX, settings.TRASH_FILE_PATH)
        # shutil.move(image_full_path, trash_full_path)

        # 逻辑删除, .save方法适合于单条记录的保存, 而.update方法适用于批量数据的保存
        image.is_delete = True
        image.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
