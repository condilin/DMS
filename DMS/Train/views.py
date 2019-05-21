from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, ListCreateAPIView
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

from Train.models import Train, TrainedImage
from Train.serializers import TrainSerializer, TrainedImageSerializer
from Image.models import Image

import logging
logger = logging.getLogger('django')


class UploadModelInfoFile(APIView):
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
            column_name = ['train_version', 'train_dataset', 'cells_classify_num',
                           'dataset_cells_num', 'weight', 'target_model', 'saturation',
                           'lightness', 'rotation', 'padding', 'size', 'background', 'init_lr',
                           'decay', 'epoch', 'batch', 'final_step', 'loss', 'accuracy', 'best_epoch']
            data.columns = column_name

            # 保存到数据库前，手动添加is_delete列与时间列
            data['is_delete'] = False
            data['create_time'] = time.strftime("%Y-%m-%d %H:%M:%S")
            data['update_time'] = time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(e)
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"msg": '上传数据的字段必须和训练信息页面中的字段一一对应！'})

        # ----------- 保存结果到数据库 ----------- #
        # 开启事务
        with transaction.atomic():
            # 创建保存点
            save_id = transaction.savepoint()

            try:
                # 删除表中没有逻辑删除的记录,那些已逻辑删除的要保存记录下来
                # Train.objects.filter(is_delete=False).delete()

                # 将数据写入mysql的数据库，但需要先通过sqlalchemy.create_engine建立连接,且字符编码设置为utf8，否则有些latin字符不能处理
                con = create_engine(UPLOAD_DB_ENGINE)
                # chunksize:
                # 如果data的数据量太大，数据库无法响应可能会报错，这时候就可以设置chunksize，比如chunksize = 1000，data就会一次1000的循环写入数据库。
                # if_exists:
                # 如果表中有数据，则追加
                # index:
                # index=False，则不将dataframe中的index列保存到数据库
                data.to_sql('tb_train_info', con, if_exists='append', index=False, chunksize=1000)
            except Exception as e:
                logging.error(e)
                transaction.savepoint_rollback(save_id)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"msg": '导入数据库失败！'})

            # 提交事务
            transaction.savepoint_commit(save_id)

            return Response(status=status.HTTP_201_CREATED, data={"msg": '上传成功！'})


class UploadTrainedImageFile(APIView):
    """
    post: 上传txt/csv/excel格式的数据
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
        if suffix_name in ['.txt', '.csv', '.xls', '.xlsx']:
            upload_file_rename = save_upload_file(_file)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"msg": '请上传txt或csv或excel格式的文件！'})

        # ---------- 读取上传文件数据 ---------- #
        # excel格式
        if suffix_name in ['.xls', '.xlsx']:
            data = pd.read_excel(upload_file_rename)
        # csv格式
        elif suffix_name == '.csv':
            data = pd.read_csv(upload_file_rename)
        # txt格式
        else:
            data = pd.read_table(upload_file_rename)

        # ---------- 删除上传文件数据 ---------- #
        os.remove(upload_file_rename)

        try:
            # ---------- 自定义列名以及增加列字段值 ---------- #
            # 重新定义表中字段的列名, 因为插入数据库时，时按表中的字段对应一一插入到数据库中的，因此列名要与数据库中保持一致
            column_name = ['file_name']
            data.columns = column_name

            # 保存到数据库前，手动添加is_delete列与时间列
            data['is_delete'] = False
            data['create_time'] = time.strftime("%Y-%m-%d %H:%M:%S")
            data['update_time'] = time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(e)
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={"msg": '上传数据的字段必须和训练信息页面中的字段一一对应！'})

        # ----------- 保存结果到数据库 ----------- #
        # 开启事务
        with transaction.atomic():
            # 创建保存点
            save_id = transaction.savepoint()

            try:
                # 删除表中没有逻辑删除的记录,那些已逻辑删除的要保存记录下来
                # TrainedImage.objects.filter(is_delete=False).delete()

                # 将数据写入mysql的数据库，但需要先通过sqlalchemy.create_engine建立连接,且字符编码设置为utf8，否则有些latin字符不能处理
                con = create_engine(UPLOAD_DB_ENGINE)
                # chunksize:
                # 如果data的数据量太大，数据库无法响应可能会报错，这时候就可以设置chunksize，比如chunksize = 1000，data就会一次1000的循环写入数据库。
                # if_exists:
                # 如果表中有数据，则追加
                # index:
                # index=False，则不将dataframe中的index列保存到数据库
                data.to_sql('tb_trained_image', con, if_exists='append', index=False, chunksize=1000)

                # 同时更新大图中的是否学习字段
                # 已训练的大图列表
                trained_image_set = set(list(data['file_name']))
                # 查询大图表中的大图
                image_file_name = Image.objects.values('file_name')
                image_file_name_set = set([i['file_name'] for i in image_file_name])
                # 已训练的大图哪些在大图中(求交集)
                intersect_image = trained_image_set.intersection(image_file_name_set)

                # 批量更新, 将匹配到的大图中的is_learn改为True
                # 注意这里要使用文件名, 而不能使用病理号, 因此有病理号为TC17001535, 而文件名可能为:TC17001535,TC17001535_1等
                Image.objects.filter(file_name__in=intersect_image).update(is_learn=True)

            except Exception as e:
                logging.error(e)
                transaction.savepoint_rollback(save_id)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"msg": '导入数据库失败！'})

            # 提交事务
            transaction.savepoint_commit(save_id)

            return Response(status=status.HTTP_201_CREATED, data={"msg": '上传成功！'})


class DownloadModelInfoFile(APIView):
    """
    get: 导出csv/excel数据
    :parameter:
        type: 指定下载的格式, csv/xlsx/xls
    :example:
        /api/v1/trains/downloads/?type=csv
    """

    def get(self, request):

        suffix_name = request.GET.get('type', None)
        if not suffix_name:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'msg': '请求参数错误！'})

        if suffix_name not in ['csv', 'xlsx', 'xls']:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'msg': '仅支持下载csv和excel格式！'})

        # 通过指定字段的别名, 指定返回的格式顺序, 下载时默认按字母进行排序
        train_data = Train.objects.filter(is_delete=False).annotate(
            c11_训练数据版本=F('train_version'), c12_训练数据集=F('train_dataset'),
            c13_细胞分类数量=F('cells_classify_num'), c14_原始数据集细胞数量=F('dataset_cells_num'),
            c15_使用的权重=F('weight'), c16_目标模型=F('target_model'), c17_饱和度=F('saturation'),
            c18_亮度=F('lightness'), c19_旋转=F('rotation'), c20_贴边=F('padding'),
            c21_尺寸=F('size'), c22_背景=F('background'), c23_初始学习率=F('init_lr'),
            c24_衰减率=F('decay'), c25_轮数=F('epoch'), c26_批数=F('batch'),
            c27_训练步数=F('final_step'), c28_损失=F('loss'), c29_准确率=F('accuracy'),
            c30_最好的轮数=F('best_epoch')).values(
            'c11_训练数据版本', 'c12_训练数据集', 'c13_细胞分类数量', 'c14_原始数据集细胞数量',
            'c15_使用的权重', 'c16_目标模型', 'c17_饱和度', 'c18_亮度', 'c19_旋转', 'c20_贴边',
            'c21_尺寸', 'c22_背景', 'c23_初始学习率', 'c24_衰减率', 'c25_轮数', 'c26_批数',
            'c27_训练步数', 'c28_损失', 'c29_准确率', 'c30_最好的轮数')

        # 命名返回文件名字(django-queryset-csv插件使用中文名字返回时会去掉, 使用英文则不会)
        file_name_add_date = 'model_info_' + time.strftime('%Y_%m_%d_%H_%M_%S') + '.{}'.format(suffix_name)

        # 返回对应格式的文件
        # 返回csv格式使用make_response_from_records会出现中文乱码,
        # pyexcel主要用于上传下载excel类型的数据,因此要改用其它框架django-queryset-csv
        if suffix_name == 'csv':
            # 指定返回字段的顺序
            field_name_list = sorted(list(train_data[0].keys()))
            return render_to_csv_response(train_data, filename=file_name_add_date, field_order=field_name_list)
        else:
            return excel.make_response_from_records(train_data, file_type=suffix_name, file_name=file_name_add_date)


class DownloadTrainedImageFile(APIView):
    """
    get: 导出csv/excel数据
    :parameter:
        type: 指定下载的格式, csv/xlsx/xls
    :example:
        /api/v1/trains/downloads/trained/?type=csv
    """

    def get(self, request):

        suffix_name = request.GET.get('type', None)
        if not suffix_name:
            return Response(status=status.HTTP_403_FORBIDDEN, data={'msg': '请求参数错误！'})

        if suffix_name not in ['csv', 'xlsx', 'xls']:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'msg': '仅支持下载csv和excel格式！'})

        # 通过指定字段的别名, 指定返回的格式顺序, 下载时默认按字母进行排序
        trained_data = TrainedImage.objects.filter(is_delete=False).annotate(
            image_file_name=F('file_name')).values('image_file_name')

        # 命名返回文件名字
        file_name_add_date = '已训练的大图列表_' + time.strftime('%Y_%m_%d_%H_%M_%S') + '.{}'.format(suffix_name)
        # 返回对应格式的文件
        return excel.make_response_from_records(trained_data, file_type=suffix_name, file_name=file_name_add_date)


class TrainFilter(FilterSet):
    """搜索类"""

    train_version = CharFilter(lookup_expr='icontains')  # 模糊搜索

    class Meta:
        model = Train
        fields = ['train_version']


class TrainedImageFilter(FilterSet):
    """搜索类"""

    file_name = CharFilter(lookup_expr='icontains')  # 模糊搜索

    class Meta:
        model = TrainedImage
        fields = ['file_name']


class SCTrainView(ListCreateAPIView):
    """
    get: 查询模型训练信息记录列表
    post: 创建一条模型训练信息记录
    """

    # 指定查询集, 获取没有逻辑删除的数据
    queryset = Train.objects.filter(is_delete=False)

    # 指定序列化器
    serializer_class = TrainSerializer

    # OrderingFilter：指定排序的过滤器,可以按任意字段排序,通过在路由中通过ordering参数控制,如：?ordering=id
    # DjangoFilterBackend对应filter_fields属性，做相等查询
    # SearchFilter对应search_fields，对应模糊查询
    filter_backends = [OrderingFilter, DjangoFilterBackend, SearchFilter]
    # 默认指定按哪个字段进行排序
    ordering_fields = ('train_version',)
    # 指定可以被搜索字段
    filter_class = TrainFilter


class STrainedImageView(ListAPIView):
    """
    get: 查询已训练大图数据记录列表
    """

    # 指定查询集, 获取没有逻辑删除的数据
    queryset = TrainedImage.objects.filter(is_delete=False)

    # 指定序列化器
    serializer_class = TrainedImageSerializer

    # OrderingFilter：指定排序的过滤器,可以按任意字段排序,通过在路由中通过ordering参数控制,如：?ordering=id
    # DjangoFilterBackend对应filter_fields属性，做相等查询
    # SearchFilter对应search_fields，对应模糊查询
    filter_backends = [OrderingFilter, DjangoFilterBackend, SearchFilter]
    # 默认指定按哪个字段进行排序
    ordering_fields = ('file_name',)
    # 指定可以被搜索字段
    filter_class = TrainedImageFilter


class SUDTrainView(APIView):
    """
    get: 查询一条训练数据记录
    patch: 更新一条训练数据记录
    """

    def get(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            train = Train.objects.get(id=pk, is_delete=False)
        except Train.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})

        # 序列化返回
        serializer = TrainSerializer(train)
        return Response(serializer.data)

    def patch(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            train = Train.objects.get(id=pk, is_delete=False)
        except Train.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})

        # 获取参数, 校验参数, 保存结果
        serializer = TrainSerializer(train, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    # def delete(self, request, pk):
    #     # 根据id, 查询数据库对象
    #     try:
    #         diagnose = Train.objects.get(id=pk, is_delete=False)
    #     except Train.DoesNotExist:
    #         return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})
    #
    #     # 逻辑删除, .save方法适合于单条记录的保存, 而.update方法适用于批量数据的保存
    #     diagnose.is_delete = True
    #     diagnose.save()
    #
    #     return Response(status=status.HTTP_204_NO_CONTENT, data={'msg': '删除成功！'})

