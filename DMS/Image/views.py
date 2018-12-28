from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db.models import Count
import shutil
from DMS import settings

import os
import re
import time
import pandas as pd
from sqlalchemy import create_engine
from DMS.utils.uploads import save_upload_file

from Image.models import Image
from Image.serializers import ImageSerializer


class UploadFile(APIView):
    """保存上传文件的内容, 读取内容并写入数据库"""

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

        # 自定义列名
        # 重新定义表中字段的列名, 因为插入数据库时，时按表中的字段对应一一插入到数据库中的，因此列名要与数据库中保持一致
        column_name = ['pathology', 'file_name', 'resolution', 'storage_path', 'waveplate_source',
                       'is_learn', 'diagnosis_label_doctor', 'diagnosis_label_zhu', 'making_way']
        data.columns = column_name

        # 保存到数据库前，手动添加is_delete列与时间列
        data['is_delete'] = False
        data['create_time'] = time.strftime("%Y-%m-%d %H:%M:%S")
        data['update_time'] = time.strftime("%Y-%m-%d %H:%M:%S")

        # ----------- 保存结果到数据库 ----------- #

        try:
            # 将数据写入mysql的数据库，但需要先通过sqlalchemy.create_engine建立连接,且字符编码设置为utf8，否则有些latin字符不能处理
            con = create_engine('mysql+mysqldb://root:kyfq@localhost:3306/dms?charset=utf8')
            # chunksize:
            # 如果data的数据量太大，数据库无法响应可能会报错，这时候就可以设置chunksize，比如chunksize = 1000，data就会一次1000的循环写入数据库。
            # if_exists:
            # 如果表中有数据，则追加
            # index:
            # index=False，则不将dataframe中的index列保存到数据库
            data.to_sql('tb_big_image_info', con, if_exists='append', index=False, chunksize=1000)
        except Exception as e:
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"msg": '导入数据库失败！'})

        return Response(status=status.HTTP_201_CREATED, data={"msg": '上传成功！'})


class StatisticView(APIView):
    """获取统计信息"""

    def get(self, request):
        # ----- 切片总数, 统计数据库内病例数量 ----- #
        image_count = Image.objects.count()

        # ----- 各倍数数量, 占比 ----- #
        resolution_count = Image.objects.filter(is_delete=False).values('resolution').annotate(
            res_count=Count('resolution'))
        # 转换成列表
        resolution_count_list = list(resolution_count)
        # 添加倍数占比
        for i in resolution_count_list:
            i['res_prop'] = '%.2f' % (i['res_count'] / image_count * 100) + '%'

        # ----- 返回结果 ------ #
        result_dict = {
            'image_count': image_count,
            'resolution_count': resolution_count_list
        }
        return Response(status=status.HTTP_200_OK, data=result_dict)


class FindDuplicateFileName(APIView):
    """查找大图中出现重复的文件名"""

    def get(self, request):
        # 查询文件名出现的次数大于1的记录
        dup_file_name = Image.objects.filter(is_delete=False).values('file_name').annotate(
            dup_count=Count('file_name')).filter(dup_count__gt=1)
        # 转换成列表
        dup_file_name_list = list(dup_file_name)

        # ----- 返回结果 ------ #
        result_dict = {
            "dup_file_name": dup_file_name_list
        }
        return Response(status=status.HTTP_200_OK, data=result_dict)


class SCImageView(ListCreateAPIView):
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
    filter_fields = ('id', 'pathology',)


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
