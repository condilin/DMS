from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import FilterSet, CharFilter
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db.models import Count, F
from django.db import transaction

import os
import time
import pandas as pd
from sqlalchemy import create_engine
from DMS.settings.dev import UPLOAD_DB_ENGINE
import django_excel as excel
from DMS.utils.uploads import save_upload_file

from Case.models import Case
from Case.serializers import CaseSerializer, SearchDupCaseSerializer
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
        if suffix_name not in ['.csv', '.xls', '.xlsx']:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"msg": '请上传csv或excel格式的文件！'})

        upload_file_rename = save_upload_file(_file)
        # ---------- 读取上传文件数据 ---------- #
        # excel格式
        if suffix_name in ['.xls', '.xlsx']:
            data = pd.read_excel(upload_file_rename)
        # csv格式
        else:
            data = pd.read_csv(upload_file_rename)

        # ---------- 删除上传文件数据 ---------- #
        os.remove(upload_file_rename)

        # 自定义列名
        # 重新定义表中字段的列名, 因为插入数据库时，时按表中的字段对应一一插入到数据库中的，因此列名要与数据库中保持一致
        column_name = ['pathology', 'diagnosis_label_doctor', 'waveplate_source', 'making_way', 'check_date',
                       'diagnosis_date', 'last_menstruation', 'clinical_observed']
        data.columns = column_name

        # 保存到数据库前, 手动添加is_delete列与时间列, 以及对诊断标签进行处理
        data['is_delete'] = False
        data['create_time'] = time.strftime("%Y-%m-%d %H:%M:%S")
        data['update_time'] = time.strftime("%Y-%m-%d %H:%M:%S")
        data['diagnosis_label_doctor_filter'] = data.diagnosis_label_doctor.str.extract(r'(\w+)')

        # ----------- 保存结果到数据库 ----------- #
        # 开启事务
        with transaction.atomic():
            # 创建保存点
            save_id = transaction.savepoint()

            try:
                # 删除表中没有逻辑删除的记录,那些已逻辑删除的要保存记录下来
                Case.objects.filter(is_delete=False).delete()

                # 将数据写入mysql的数据库，但需要先通过sqlalchemy.create_engine建立连接,且字符编码设置为utf8，否则有些latin字符不能处理
                con = create_engine(UPLOAD_DB_ENGINE)
                # chunksize:
                # 如果data的数据量太大，数据库无法响应可能会报错，这时候就可以设置chunksize，比如chunksize = 1000，data就会一次1000的循环写入数据库。
                # if_exists:
                # 如果表中有数据，则追加
                # index:
                # index=False，则不将dataframe中的index列保存到数据库
                data.to_sql('tb_case_info', con, if_exists='append', index=False, chunksize=1000)
            except Exception as e:
                logger.error(e)
                transaction.savepoint_rollback(save_id)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"msg": '导入数据库失败！'})

            # 提交事务
            transaction.savepoint_commit(save_id)

            return Response(status=status.HTTP_201_CREATED, data={"msg": '上传成功！'})


class DownloadFile(APIView):
    """
    get: 导出全部的病例csv/excel数据
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

        # 通过指定字段的别名, 指定返回的格式顺序, 下载时默认按字母进行排序
        case_data = Case.objects.filter(is_delete=False).annotate(
            c1_病理号=F('pathology'), c2_医生诊断=F('diagnosis_label_doctor'),
            c3_片源=F('waveplate_source'), c4_切片制式=F('making_way'),
            c5_采样_检查时间=F('check_date'), c6_诊断时间=F('diagnosis_date'),
            c7_末次经期时间=F('last_menstruation'), c8_临床所见=F('clinical_observed')).values(
            'c1_病理号', 'c2_医生诊断', 'c3_片源', 'c4_切片制式', 'c5_采样_检查时间',
            'c6_诊断时间', 'c7_末次经期时间', 'c8_临床所见')

        # 命名返回文件名字
        file_name_add_date = '病例信息_' + time.strftime('%Y_%m_%d_%H_%M_%S') + '.{}'.format(suffix_name)

        # 返回对应格式的文件
        # 返回csv格式使用make_response_from_records会出现中文乱码, 而使用make_response_from_query_sets则没问题
        if suffix_name == 'csv':
            return excel.make_response_from_query_sets(case_data, file_type=suffix_name, file_name=file_name_add_date)
        else:
            return excel.make_response_from_records(case_data, file_type=suffix_name, file_name=file_name_add_date)


class DownloadDuplicateName(APIView):
    """
    get: 导出重复病理号的病例csv/excel数据
    :parameter:
        type: 指定下载的格式, csv/xlsx/xls
    :example:
        /api/v1/cases/downloads/duppaths/?type=csv
    """

    def get(self, request):

        suffix_name = request.GET.get('type', None)
        if not suffix_name:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'msg': '请求参数错误！'})

        if suffix_name not in ['csv', 'xlsx', 'xls']:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'msg': '仅支持下载csv和excel格式！'})

        # 查询病理号出现的次数大于1的记录的病理号值
        dup_file_name = Case.objects.filter(is_delete=False).values('pathology').annotate(
            dup_count=Count('pathology')).filter(dup_count__gt=1).values_list('pathology', flat=True)

        # 通过指定字段的别名, 指定返回的格式顺序, 下载时默认按字母进行排序
        duplicate_case_data = Case.objects.filter(pathology__in=list(dup_file_name)).annotate(
            c1_病理号=F('pathology'), c2_医生诊断=F('diagnosis_label_doctor'),
            c3_片源=F('waveplate_source'), c4_切片制式=F('making_way'),
            c5_采样_检查时间=F('check_date'), c6_诊断时间=F('diagnosis_date'),
            c7_末次经期时间=F('last_menstruation'), c8_临床所见=F('clinical_observed')).values(
            'c1_病理号', 'c2_医生诊断', 'c3_片源', 'c4_切片制式', 'c5_采样_检查时间',
            'c6_诊断时间', 'c7_末次经期时间', 'c8_临床所见')

        # 命名返回文件名字
        file_name_add_date = '重复病理号记录_' + time.strftime('%Y_%m_%d_%H_%M_%S') + '.{}'.format(suffix_name)

        # 返回对应格式的文件
        # 返回csv格式使用make_response_from_records会出现中文乱码, 而使用make_response_from_query_sets则没问题
        if suffix_name == 'csv':
            return excel.make_response_from_query_sets(duplicate_case_data, file_type=suffix_name, file_name=file_name_add_date)
        else:
            return excel.make_response_from_records(duplicate_case_data, file_type=suffix_name, file_name=file_name_add_date)


class FindDuplicateFileName(APIView):
    """
    get: 查找病例中出现重复的病理号及重复的次数
    """

    def get(self, request):
        # 查询病理号出现的次数大于1的记录
        dup_file_name = Case.objects.filter(is_delete=False).values('pathology').annotate(
            dup_count=Count('pathology')).filter(dup_count__gt=1).order_by('-dup_count')

        # 创建分页对象
        pg = LimitOffsetPagination()

        # 获取分页的数据
        page_roles = pg.paginate_queryset(queryset=dup_file_name, request=request, view=self)

        # 序列化返回
        # 查询多条重复记录, 因此需要指定many=True, 并指定instance
        serializer = CaseSerializer(instance=page_roles, many=True)

        # 不含上一页和下一页，要手动的在url中传参limit和offset来控制第几页
        # return Response(status=status.HTTP_200_OK, data=serializer.data)
        # 使用get_paginated_response, 则含上一页和下一页
        return pg.get_paginated_response(data=serializer.data)


class CaseFilter(FilterSet):
    """搜索类"""

    pathology = CharFilter(lookup_expr='icontains')  # 模糊查询（包含），并且忽略大小写
    diagnosis_label_doctor = CharFilter(lookup_expr='iexact')  # 精确匹配

    class Meta:
        model = Case
        fields = ['pathology', 'diagnosis_label_doctor']


class SearchDuplicateFileName(ListAPIView):
    """
    get: 搜索病例中出现重复的病理号
    """

    # 指定查询集, 获取病理号出现的次数大于1的记录
    queryset = Case.objects.filter(is_delete=False).values('pathology').annotate(
            dup_count=Count('pathology')).filter(dup_count__gt=1)

    # 指定序列化器
    serializer_class = SearchDupCaseSerializer

    # OrderingFilter：指定排序的过滤器,可以按任意字段排序,通过在路由中通过ordering参数控制,如：?ordering=id
    # DjangoFilterBackend对应filter_fields属性，做相等查询
    # SearchFilter对应search_fields，对应模糊查询
    filter_backends = [OrderingFilter, DjangoFilterBackend, SearchFilter]
    # 默认指定按哪个字段进行排序
    ordering_fields = ('pathology',)
    # 指定可以被搜索字段
    filter_class = CaseFilter


class SCCaseView(ListCreateAPIView):
    """
    get: 查询病例记录列表
    post: 新增一条病例记录
    """

    # 指定查询集, 获取没有逻辑删除的数据
    queryset = Case.objects.filter(is_delete=False)

    # 指定序列化器
    serializer_class = CaseSerializer

    # OrderingFilter：指定排序的过滤器,可以按任意字段排序,通过在路由中通过ordering参数控制,如：?ordering=id
    # DjangoFilterBackend对应filter_fields属性，做相等查询
    # SearchFilter对应search_fields，对应模糊查询
    filter_backends = [OrderingFilter, DjangoFilterBackend, SearchFilter]
    # 默认指定按哪个字段进行排序
    ordering_fields = ('pathology',)
    # 指定可以被搜索字段
    filter_class = CaseFilter


class SUDCaseView(APIView):
    """
    get: 查询一条病例记录
    patch: 修改一条病例记录
    delete: 删除一条病例数据
    """

    def get(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            case = Case.objects.get(id=pk, is_delete=False)
        except Case.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})

        # 序列化返回
        serializer = CaseSerializer(case)
        return Response(serializer.data)

    def patch(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            diagnose = Case.objects.get(id=pk, is_delete=False)
        except Case.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})

        # 获取参数, 校验参数, 保存结果
        serializer = CaseSerializer(diagnose, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # ----- 医生的诊断标签同步到大图表中 ----- #
        # 获取病理号
        case_pathology = request.data['pathology']
        # 根据病理号, 查询所有的医生诊断标签, 并使用,号进行拼接
        case_res = Case.objects.filter(pathology=case_pathology, is_delete=False)
        diagnosis_label_doctor_list = [i.diagnosis_label_doctor for i in case_res if i.diagnosis_label_doctor is not None]
        diagnosis_label_doctor_str = '+'.join(diagnosis_label_doctor_list) if diagnosis_label_doctor_list else None

        # 根据病理号查询大图记录
        image = Image.objects.filter(pathology=case_pathology, is_delete=False)
        # 如果在大图中匹配到病例信息中的病理号, 则同步修改大图; 如果有多条, 则全部修改成一样
        if image:
            for i in image:
                i.diagnosis_label_doctor = diagnosis_label_doctor_str
                i.save()

        return Response(serializer.data)

    def delete(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            case = Case.objects.get(id=pk, is_delete=False)
        except Case.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})

        # 逻辑删除, .save方法适合于单条记录的保存, 而.update方法适用于批量数据的保存
        case.is_delete = True
        case.save()

        # ----- 医生的诊断标签同步到大图表中 ----- #
        # 获取病理号
        case_pathology = case.pathology
        # 根据病理号, 查询所有的医生诊断标签, 并使用,号进行拼接
        case_res = Case.objects.filter(pathology=case_pathology, is_delete=False)
        diagnosis_label_doctor_list = [i.diagnosis_label_doctor for i in case_res if i.diagnosis_label_doctor is not None]
        diagnosis_label_doctor_str = '+'.join(diagnosis_label_doctor_list) if diagnosis_label_doctor_list else None

        # 根据病理号查询大图记录
        image = Image.objects.filter(pathology=case_pathology, is_delete=False)
        # 如果在大图中匹配到病例信息中的病理号, 则同步修改大图; 如果有多条, 则全部修改成一样
        if image:
            for i in image:
                i.diagnosis_label_doctor = diagnosis_label_doctor_str
                i.save()

        return Response(status=status.HTTP_204_NO_CONTENT, data={'msg': '删除成功！'})


class BatchUpdateCaseView(APIView):
    """
    post: 批量删除
    """

    def post(self, request):
        # 获取要删除的id列表
        delete_id_str = request.POST.get('idList', None)
        if not delete_id_str:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'msg': '你妹的，没有idlist！'})

        # 根据id列表, 查询数据库对象
        try:
            _delete_id_list = delete_id_str.split(',')
            case = Case.objects.filter(id__in=_delete_id_list, is_delete=False)
        except Case.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '列表中含有不存在的数据！'})

        # 批量更新，.save方法适合于单条记录的保存, 而.update方法适用于批量数据的保存
        case.update(is_delete=True)

        return Response(status=status.HTTP_204_NO_CONTENT, data={'msg': '批量删除成功！'})
