from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db import transaction
from django.db.models import Count, F

import os
import time
import django_excel as excel
import pandas as pd
from sqlalchemy import create_engine
from DMS.utils.uploads import save_upload_file

from Diagnosis.models import Diagnosis
from Diagnosis.serializers import DiagnoseSerializer


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

        # ---------- 自定义列名以及增加列字段值 ---------- #
        # 重新定义表中字段的列名, 因为插入数据库时，时按表中的字段对应一一插入到数据库中的，因此列名要与数据库中保持一致
        column_name = ['pathology', 'diagnosis_label_lastest', 'his_diagnosis_label1',
                       'his_diagnosis_label2', 'his_diagnosis_label3', 'his_diagnosis_label4']
        data.columns = column_name

        # 保存到数据库前，手动添加is_delete列与时间列
        data['is_delete'] = False
        data['create_time'] = time.strftime("%Y-%m-%d %H:%M:%S")
        data['update_time'] = time.strftime("%Y-%m-%d %H:%M:%S")

        # ----------- 保存结果到数据库 ----------- #
        # 开启事务
        with transaction.atomic():
            # 创建保存点
            save_id = transaction.savepoint()

            try:
                # 删除表中没有逻辑删除的记录,那些已逻辑删除的要保存记录下来
                Diagnosis.objects.filter(is_delete=False).delete()

                # 将数据写入mysql的数据库，但需要先通过sqlalchemy.create_engine建立连接,且字符编码设置为utf8，否则有些latin字符不能处理
                con = create_engine('mysql+mysqldb://root:kyfq@localhost:3306/dms?charset=utf8')
                # chunksize:
                # 如果data的数据量太大，数据库无法响应可能会报错，这时候就可以设置chunksize，比如chunksize = 1000，data就会一次1000的循环写入数据库。
                # if_exists:
                # 如果表中有数据，则追加
                # index:
                # index=False，则不将dataframe中的index列保存到数据库
                data.to_sql('tb_image_diagnosis_zhu', con, if_exists='append', index=False, chunksize=1000)
            except Exception as e:
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
        /api/v1/diagnosis/downloads/?type=csv
    """

    def get(self, request):

        suffix_name = request.GET.get('type', None)
        if not suffix_name:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'msg': '请求参数错误！'})

        if suffix_name not in ['csv', 'xlsx', 'xls']:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'msg': '仅支持下载csv和excel格式！'})

        # 通过指定字段的别名, 指定返回的格式顺序, 下载时默认按字母进行排序
        img_data = Diagnosis.objects.filter(is_delete=False).annotate(
            c1_病理号=F('pathology'), c2_最新诊断标签=F('diagnosis_label_lastest'),
            c3_历史诊断标签1=F('his_diagnosis_label1'), c4_历史诊断标签2=F('his_diagnosis_label2'),
            c5_历史诊断标签3=F('his_diagnosis_label3'), c6_历史诊断标签4=F('his_diagnosis_label4'),
            c7_历史诊断标签5=F('his_diagnosis_label5')).values(
            'c1_病理号', 'c2_最新诊断标签', 'c3_历史诊断标签1', 'c4_历史诊断标签2',
            'c5_历史诊断标签3', 'c6_历史诊断标签4', 'c7_历史诊断标签5')

        # 命名返回文件名字
        file_name_add_date = '朱博士诊断信息_' + time.strftime('%Y_%m_%d_%H_%M_%S') + '.{}'.format(suffix_name)
        # 返回对应格式的文件
        return excel.make_response_from_records(img_data, file_type=suffix_name, file_name=file_name_add_date)


class FindDuplicatePathology(APIView):
    """
    get: 查找朱博士诊断记录中出现重复的病理号
    """

    def get(self, request):
        # 查询病理号出现的次数大于1的记录
        dup_pathology = Diagnosis.objects.filter(is_delete=False).values('pathology').annotate(
            dup_count=Count('pathology')).filter(dup_count__gt=1)
        # 转换成列表
        dup_pathology_list = list(dup_pathology)

        # ----- 返回结果 ------ #
        result_dict = {
            "dup_pathology": dup_pathology_list
        }
        return Response(status=status.HTTP_200_OK, data=result_dict)


class SCDiagnosisView(ListCreateAPIView):
    """
    get: 查询朱博士诊断记录列表
    post: 创建一条朱博士诊断记录
    """

    # 指定查询集, 获取没有逻辑删除的数据
    queryset = Diagnosis.objects.filter(is_delete=False)

    # 指定序列化器
    serializer_class = DiagnoseSerializer

    # OrderingFilter：指定排序的过滤器,可以按任意字段排序,通过在路由中通过ordering参数控制,如：?ordering=id
    # DjangoFilterBackend对应filter_fields属性，做相等查询
    # SearchFilter对应search_fields，对应模糊查询
    filter_backends = [OrderingFilter, DjangoFilterBackend, SearchFilter]
    # 默认指定按哪个字段进行排序
    ordering_fields = ('pathology',)
    # 指定可以被搜索字段, 如在路由中通过?id=2查询id为2的记录
    filter_fields = ('id', 'pathology')


class SUDDiagnosisView(APIView):
    """
    get: 查询一条朱博士诊断记录
    patch: 更新一条朱博士诊断记录
    """

    def get(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            diagnose = Diagnosis.objects.get(id=pk, is_delete=False)
        except Diagnosis.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})

        # 序列化返回
        serializer = DiagnoseSerializer(diagnose)
        return Response(serializer.data)

    def patch(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            diagnose = Diagnosis.objects.get(id=pk, is_delete=False)
        except Diagnosis.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})

        # 获取参数, 校验参数, 保存结果
        serializer = DiagnoseSerializer(diagnose, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    # def delete(self, request, pk):
    #     # 根据id, 查询数据库对象
    #     try:
    #         diagnose = Diagnosis.objects.get(id=pk, is_delete=False)
    #     except Diagnosis.DoesNotExist:
    #         return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})
    #
    #     # 逻辑删除, .save方法适合于单条记录的保存, 而.update方法适用于批量数据的保存
    #     diagnose.is_delete = True
    #     diagnose.save()
    #
    #     return Response(status=status.HTTP_204_NO_CONTENT, data={'msg': '删除成功！'})
