from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet, CharFilter
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db import transaction
from django.db.models import Count, F

import os
import time
import pandas as pd
import django_excel as excel
from djqscsv import render_to_csv_response
from sqlalchemy import create_engine
from DMS.settings.dev import UPLOAD_DB_ENGINE
from DMS.utils.uploads import save_upload_file

from FileRenameRecord.models import FileRenameRecord
from FileRenameRecord.serializers import RenameSerializer

import logging
logger = logging.getLogger('django')


class UploadFile(APIView):
    """
    post: 上传csv/excel格式的数据
    """

    def post(self, request):

        # 获取上传的文件, 'file'值是前端页面input框的name属性的值
        _file = request.FILES.get('file', None)
        # 如果获取不到内容, 则说明上传失败
        if not _file:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"msg": '文件上传失败！'})

        # ---------- 保存上传文件 ---------- #

        # 获取文件的后缀名, 判断上传文件是否符合格式要求
        suffix_name = os.path.splitext(_file.name)[1]
        if suffix_name in ['.csv', '.xls', '.xlsx']:
            upload_file_rename = save_upload_file(_file)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"msg": '请上传csv或excel格式的文件！'})

        # ---------- 读取上传文件数据 ---------- #
        # excel格式
        if suffix_name in ['.xls', '.xlsx']:
            data = pd.read_excel(upload_file_rename)
        # csv格式
        else:
            data = pd.read_csv(upload_file_rename)

        # ---------- 删除上传文件数据 ---------- #
        os.remove(upload_file_rename)

        try:
            # ---------- 自定义列名以及增加列字段值 ---------- #
            # 重新定义表中字段的列名, 因为插入数据库时，时按表中的字段对应一一插入到数据库中的，因此列名要与数据库中保持一致
            column_name = ['pathology', 'current_file_name', 'his_name1', 'his_name2',
                           'his_name3', 'his_name4', 'his_name5']
            data.columns = column_name

            # 保存到数据库前，手动添加is_delete列与时间列
            data['is_delete'] = False
            data['create_time'] = time.strftime("%Y-%m-%d %H:%M:%S")
            data['update_time'] = time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(e)
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"msg": '上传数据的字段必须和文件更名信息页面中的字段一一对应！'})

        # ----------- 保存结果到数据库 ----------- #
        # 开启事务
        with transaction.atomic():
            # 创建保存点
            save_id = transaction.savepoint()

            try:
                # 删除表中没有逻辑删除的记录,那些已逻辑删除的要保存记录下来
                # FileRenameRecord.objects.filter(is_delete=False).delete()

                # 将数据写入mysql的数据库，但需要先通过sqlalchemy.create_engine建立连接,且字符编码设置为utf8，否则有些latin字符不能处理
                con = create_engine(UPLOAD_DB_ENGINE)
                # chunksize:
                # 如果data的数据量太大，数据库无法响应可能会报错，这时候就可以设置chunksize，比如chunksize = 1000，data就会一次1000的循环写入数据库。
                # if_exists:
                # 如果表中有数据，则追加
                # index:
                # index=False，则不将dataframe中的index列保存到数据库
                data.to_sql('tb_rename', con, if_exists='append', index=False, chunksize=1000)
            except Exception as e:
                logger.error(e)
                transaction.savepoint_rollback(save_id)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"msg": '导入数据库失败！'})

            # 提交事务
            transaction.savepoint_commit(save_id)

            return Response(status=status.HTTP_201_CREATED, data={"msg": '上传成功！'})


class DownloadFile(APIView):
    """
    get: 导出csv/excel数据
    :parameter:
        type: 指定下载的格式, csv/xlsx/xls
    :example:
        /api/v1/renames/downloads/?type=csv
    """

    def get(self, request):

        suffix_name = request.GET.get('type', None)
        if not suffix_name:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'msg': '请求参数错误！'})

        if suffix_name not in ['csv', 'xlsx', 'xls']:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'msg': '仅支持下载csv和excel格式！'})

        # 通过指定字段的别名, 指定返回的格式顺序, 下载时默认按字母进行排序
        rename_data = FileRenameRecord.objects.filter(is_delete=False).annotate(
            c1_病理号=F('pathology'), c2_当前文件名=F('current_file_name'),
            c3_历史曾用名1=F('his_name1'), c4_历史曾用名2=F('his_name2'),
            c5_历史曾用名3=F('his_name3'), c6_历史曾用名4=F('his_name4'),
            c7_历史曾用名5=F('his_name5')).values(
            'c1_病理号', 'c2_当前文件名', 'c3_历史曾用名1', 'c4_历史曾用名2',
            'c5_历史曾用名3', 'c6_历史曾用名4', 'c7_历史曾用名5')

        # 命名返回文件名字(django-queryset-csv插件使用中文名字返回时会去掉, 使用英文则不会)
        file_name_add_date = 'rename_record_' + time.strftime('%Y_%m_%d_%H_%M_%S') + '.{}'.format(suffix_name)

        # 返回对应格式的文件
        # 返回csv格式使用make_response_from_records会出现中文乱码,
        # pyexcel主要用于上传下载excel类型的数据,因此要改用其它框架django-queryset-csv
        if suffix_name == 'csv':
            # 指定返回字段的顺序
            field_name_list = sorted(list(rename_data[0].keys()))
            return render_to_csv_response(rename_data, filename=file_name_add_date, field_order=field_name_list)
        else:
            return excel.make_response_from_records(rename_data, file_type=suffix_name, file_name=file_name_add_date)


class FindDuplicateFileName(APIView):
    """
    get: 查找更名记录中出现重复的文件名
    """

    def get(self, request):
        # 查询文件名出现的次数大于1的记录
        dup_file_name = FileRenameRecord.objects.filter(is_delete=False).values('current_file_name').annotate(
            dup_count=Count('current_file_name')).filter(dup_count__gt=1)
        # 转换成列表
        dup_file_name_list = list(dup_file_name)

        # ----- 返回结果 ------ #
        result_dict = {
            "dup_file_name": dup_file_name_list
        }
        return Response(status=status.HTTP_200_OK, data=result_dict)


class RenameFilter(FilterSet):
    """搜索类"""

    pathology = CharFilter(lookup_expr='icontains')  # 模糊查询（包含），并且忽略大小写
    current_file_name = CharFilter(lookup_expr='icontains')  # 模糊查询（包含），并且忽略大小写

    class Meta:
        model = FileRenameRecord
        fields = ['pathology', 'current_file_name']


class SCRenameView(ListCreateAPIView):
    """
    get: 查询更名记录列表
    post: 创建一条更新记录
    """

    # 指定查询集, 获取没有逻辑删除的数据
    queryset = FileRenameRecord.objects.filter(is_delete=False)

    # 指定序列化器
    serializer_class = RenameSerializer

    # OrderingFilter：指定排序的过滤器,可以按任意字段排序,通过在路由中通过ordering参数控制,如：?ordering=id
    # DjangoFilterBackend对应filter_fields属性，做相等查询
    # SearchFilter对应search_fields，对应模糊查询
    filter_backends = [OrderingFilter, DjangoFilterBackend, SearchFilter]
    # 默认指定按哪个字段进行排序
    ordering_fields = ('pathology',)
    # 指定搜索字段
    filter_class = RenameFilter


class SUDRenameView(APIView):
    """
    get: 查询一条更名记录
    patch: 更新一条更名记录
    """

    def get(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            image = FileRenameRecord.objects.get(id=pk, is_delete=False)
        except FileRenameRecord.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})

        # 序列化返回
        serializer = RenameSerializer(image)
        return Response(serializer.data)

    def patch(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            image = FileRenameRecord.objects.get(id=pk, is_delete=False)
        except FileRenameRecord.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})

        # 获取参数, 校验参数, 保存结果
        serializer = RenameSerializer(image, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    # def delete(self, request, pk):
    #     # 根据id, 查询数据库对象
    #     try:
    #         image = FileRenameRecord.objects.get(id=pk, is_delete=False)
    #     except FileRenameRecord.DoesNotExist:
    #         return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})
    #
    #     # 逻辑删除, .save方法适合于单条记录的保存, 而.update方法适用于批量数据的保存
    #     image.is_delete = True
    #     image.save()
    #
    #     return Response(status=status.HTTP_204_NO_CONTENT, data={'msg': '删除成功！'})

