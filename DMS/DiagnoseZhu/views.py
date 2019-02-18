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
import django_excel as excel
from djqscsv import render_to_csv_response
import pandas as pd
from sqlalchemy import create_engine
from django.forms.models import model_to_dict
from DMS.settings.dev import UPLOAD_DB_ENGINE
from DMS.utils.uploads import save_upload_file

from DiagnoseZhu.models import DiagnoseZhu, DiagnoseZhuTmp
from DiagnoseZhu.serializers import SDiagnoseSerializer, CDiagnoseSerializer
from Image.models import Image

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

        # ---------- 自定义列名以及增加列字段值 ---------- #
        # 重新定义表中字段的列名, 因为插入数据库时，时按表中的字段对应一一插入到数据库中的，因此列名要与数据库中保持一致
        column_name = ['pathology', 'his_diagnosis_label']
        data.columns = column_name

        # 保存到数据库前，手动添加is_delete列与时间列
        data['is_delete'] = False
        data['create_time'] = time.strftime("%Y-%m-%d %H:%M:%S")

        # ----------- 保存结果到数据库 ----------- #
        # 开启事务
        with transaction.atomic():
            # 创建保存点
            save_id = transaction.savepoint()

            try:
                # 删除表中没有逻辑删除的记录,那些已逻辑删除的要保存记录下来
                # DiagnoseZhu.objects.filter(is_delete=False).delete()

                # 将数据写入mysql的数据库，但需要先通过sqlalchemy.create_engine建立连接,且字符编码设置为utf8，否则有些latin字符不能处理
                con = create_engine(UPLOAD_DB_ENGINE)
                # chunksize:
                # 如果data的数据量太大，数据库无法响应可能会报错，这时候就可以设置chunksize，比如chunksize = 1000，data就会一次1000的循环写入数据库。
                # if_exists:
                # 如果表中有数据，则追加
                # index:
                # index=False，则不将dataframe中的index列保存到数据库
                data.to_sql('tb_diagnose_zhu', con, if_exists='append', index=False, chunksize=1000)
            except Exception as e:
                logger.error(e)
                transaction.savepoint_rollback(save_id)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"msg": '导入数据库失败！'})

            # 提交事务
            transaction.savepoint_commit(save_id)

        # ------- 更新大图信息中的朱博士诊断 -------- #
        # 遍历df中的每一条记录
        for index, row in data.iterrows():
            # 如何筛选出来有多条大图记录, 则只更新第一条大图记录
            # 注意这里要使用文件名, 而不能使用病理号, 因此有病理号为TC17001535, 而文件名可能为:TC17001535,TC17001535_1等
            image = Image.objects.filter(is_delete=False, file_name=row['pathology'])
            # ------- 更新大图信息中的朱博士诊断 -------- #
            # 如何筛选出来有多条大图记录, 则只更新第一条大图记录
            if image:
                image1 = image[0]
                image1.diagnosis_label_zhu = row['his_diagnosis_label']
                image1.save()

            # ------- 查询DiagnoseZhu中的数据，经处理后，保存在DiagnoseZhuTmp表中 ------- #
            # 获取没有逻辑删除的数据, 并按病理号, 创建时间降序排序
            # 上一步已上传了记录, 并且commit, 数据是存在的, 因此可以进行合并
            raw_queryset = DiagnoseZhu.objects.filter(is_delete=False, pathology=row['pathology']).order_by(
                'pathology', '-create_time')

            # 将queryset类型转换成dict
            res_list = []
            for i in raw_queryset:
                res_list.append(model_to_dict(i))
            # 转换成df
            res_df = pd.DataFrame(res_list)
            # 分组合并
            res_df_gb = res_df.groupby(by='pathology').apply(lambda x: ','.join(x['his_diagnosis_label']))
            res_dict = res_df_gb.to_dict()

            # 先删除DiagnoseZhuTmp已存在的记录然后再创建
            DiagnoseZhuTmp.objects.filter(is_delete=False, pathology=row['pathology']).delete()
            for k, v in res_dict.items():
                diagnose_tmp = DiagnoseZhuTmp(pathology=k, his_diagnosis_label=v)
                diagnose_tmp.save()

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
        diagnosezhu_data = DiagnoseZhuTmp.objects.filter(is_delete=False).annotate(
            c1_病理号=F('pathology'), c2_历史诊断标签列表=F('his_diagnosis_label')).values(
            'c1_病理号', 'c2_历史诊断标签列表').order_by('pathology', '-create_time')

        # 命名返回文件名字(django-queryset-csv插件使用中文名字返回时会去掉, 使用英文则不会)
        file_name_add_date = 'diagnose_zhu_' + time.strftime('%Y_%m_%d_%H_%M_%S') + '.{}'.format(suffix_name)

        # 返回对应格式的文件
        # 返回csv格式使用make_response_from_records会出现中文乱码,
        # pyexcel主要用于上传下载excel类型的数据,因此要改用其它框架django-queryset-csv
        if suffix_name == 'csv':
            # 指定返回字段的顺序
            field_name_list = sorted(list(diagnosezhu_data[0].keys()))
            return render_to_csv_response(diagnosezhu_data, filename=file_name_add_date, field_order=field_name_list)
        else:
            return excel.make_response_from_records(diagnosezhu_data, file_type=suffix_name, file_name=file_name_add_date)


# class FindDuplicatePathology(APIView):
#     """
#     get: 查找朱博士诊断记录中出现重复的病理号
#     """
#
#     def get(self, request):
#         # 查询病理号出现的次数大于1的记录
#         dup_pathology = DiagnoseZhu.objects.filter(is_delete=False).values('pathology').annotate(
#             dup_count=Count('pathology')).filter(dup_count__gt=1)
#         # 转换成列表
#         dup_pathology_list = list(dup_pathology)
#
#         # ----- 返回结果 ------ #
#         result_dict = {
#             "dup_pathology": dup_pathology_list
#         }
#         return Response(status=status.HTTP_200_OK, data=result_dict)


class DiagnosisFilter(FilterSet):
    """搜索类"""

    pathology = CharFilter(lookup_expr='icontains')  # 模糊查询（包含），并且忽略大小写

    class Meta:
        model = DiagnoseZhuTmp
        fields = ['pathology']


class SCDiagnosisView(ListCreateAPIView):
    """
    get: 查询朱博士诊断记录列表
    post: 新增一条朱博士诊断记录
    """

    # 指定查询集
    def get_queryset(self):
        """返回经过数据合并处理后的记录"""

        return DiagnoseZhuTmp.objects.filter(is_delete=False).order_by('pathology')

    # 指定序列化器
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return SDiagnoseSerializer

        return CDiagnoseSerializer

    # OrderingFilter：指定排序的过滤器,可以按任意字段排序,通过在路由中通过ordering参数控制,如：?ordering=id
    # DjangoFilterBackend对应filter_fields属性，做相等查询
    # SearchFilter对应search_fields，对应模糊查询
    filter_backends = [OrderingFilter, DjangoFilterBackend, SearchFilter]
    # 默认指定按哪个字段进行排序
    ordering_fields = ('pathology',)
    # 指定可以被搜索字段
    filter_class = DiagnosisFilter


# class SUDDiagnosisView(APIView):
#     """
#     get: 查询一条朱博士诊断记录
#     patch: 更新一条朱博士诊断记录
#     """
#
#     def get(self, request, pathology):
#         # 根据id, 查询数据库对象
#         try:
#             diagnose = DiagnoseZhu.objects.filter(pathology=pathology, is_delete=False)
#         except DiagnoseZhu.DoesNotExist:
#             return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})
#
#         # 序列化返回
#         serializer = CDiagnoseSerializer(diagnose)
#         return Response(serializer.data)
#
#     def patch(self, request, pathology):
#         # 根据id, 查询数据库对象
#         try:
#             diagnose = DiagnoseZhu.objects.filter(pathology=pathology, is_delete=False)
#         except DiagnoseZhu.DoesNotExist:
#             return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})
#
#         # 获取参数, 校验参数, 保存结果
#         serializer = CDiagnoseSerializer(diagnose, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#
#         return Response(serializer.data)

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

