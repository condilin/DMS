# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: serializers.py
# @time: 18-12-25 下午2:54

from rest_framework import serializers
from .models import Image


class ImageSerializer(serializers.ModelSerializer):
    """查"""

    class Meta:
        model = Image
        fields = ('id', 'pathology', 'file_name', 'suffix', 'resolution', 'storage_path',
                  'waveplate_source', 'is_learn', 'diagnosis_label_doctor', 'diagnosis_label_zhu',
                  'making_way', 'scan_time', 'quality')


class DupImageSerializer(serializers.ModelSerializer):
    """查询重复记录"""
    dup_count = serializers.CharField(read_only=True)

    class Meta:
        model = Image
        fields = ('id', 'pathology', 'file_name', 'suffix', 'resolution', 'storage_path',
                  'waveplate_source', 'is_learn', 'diagnosis_label_doctor', 'diagnosis_label_zhu',
                  'making_way', 'scan_time', 'quality', 'dup_count')

    # def create(self, validated_data):
    #     """重写create, 当数据库中存在相同文件名,存储路径时,不保存记录"""
    #
    #     file_name = validated_data.get('file_name', None)
    #     storage_path = validated_data.get('storage_path', None)
    #
    #     # 查询数据库
    #     image = Image.objects.filter(file_name=file_name, storage_path=storage_path)
    #     print(image)
    #     # 如果不存在相同文件名&存储路径时, 则保存该记录
    #     if not image:
    #         instance = image.objects.create(**validated_data)
    #         return instance
