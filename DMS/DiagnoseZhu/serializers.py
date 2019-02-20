# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: serializers.py
# @time: 19-1-5 上午11:20

from rest_framework import serializers
from .models import DiagnoseZhu, DiagnoseZhuTmp
from Image.models import Image
import pandas as pd
from django.forms.models import model_to_dict


class SDiagnoseSerializer(serializers.ModelSerializer):
    """查"""

    class Meta:
        model = DiagnoseZhuTmp
        fields = ('id', 'pathology', 'his_diagnosis_label')


class CDiagnoseSerializer(serializers.ModelSerializer):
    """增"""
    # 格式化时间格式！
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    class Meta:
        model = DiagnoseZhu
        # 新增时, 不检验id, 因为不需要用到
        fields = ('pathology', 'his_diagnosis_label', 'create_time')

    def create(self, validated_data):

        # 调用父类的方法向DiagnoseZhu表中添加一条记录
        diagnose = super().create(validated_data)

        # ------- 更新大图信息中的朱博士诊断 -------- #
        image = Image.objects.filter(is_delete=False, pathology=diagnose.pathology)
        if image:
            # 如何筛选出来有多条大图记录, 则只更新第一条大图记录
            image[0].diagnosis_label_zhu = diagnose.his_diagnosis_label
            image.save()

        # ------- 查询DiagnoseZhu中的数据，经处理后，保存在DiagnoseZhuTmp表中 ------- #
        # 获取没有逻辑删除的数据, 并按病理号, 创建时间降序排序
        # 因为上一步已新增了记录, 因此此查询必存在结果, 获取新增病理号所有的记录进行合并
        raw_queryset = DiagnoseZhu.objects.filter(is_delete=False, pathology=diagnose.pathology).order_by(
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
        DiagnoseZhuTmp.objects.filter(is_delete=False, pathology=diagnose.pathology).delete()
        for k, v in res_dict.items():
            diagnose_tmp = DiagnoseZhuTmp(pathology=k, his_diagnosis_label=v)
            diagnose_tmp.save()

        # 返回创建成功的记录
        return diagnose
