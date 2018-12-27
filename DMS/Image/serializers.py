# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: serializers.py
# @time: 18-12-25 下午2:54

from rest_framework import serializers
from .models import Image
import re


class ImageSerializer(serializers.ModelSerializer):
    """查增"""

    class Meta:
        model = Image
        fields = ('id', 'pathology', 'file_name', 'resolution', 'storage_path',
                  'waveplate_source', 'is_learn', 'diagnosis_label_doctor',
                  'diagnosis_label_zhu', 'making_way')

    def create(self, validated_data):
        """重写create方法, 自动通过文件名获取病理号"""

        # 获取验证后的数据
        pathology = validated_data.get('pathology', None)
        file_name = validated_data.get('file_name', None)
        resolution = validated_data.get('resolution', None)
        storage_path = validated_data.get('storage_path', None)
        waveplate_source = validated_data.get('waveplate_source', None)
        is_learn = validated_data.get('is_learn', None)
        diagnosis_label_doctor = validated_data.get('diagnosis_label_doctor', None)
        diagnosis_label_zhu = validated_data.get('diagnosis_label_zhu', None)
        making_way = validated_data.get('making_way', None)

        # 如果新增记录时, 如果有带上病理号, 则使用该病理号, 否则从文件名中自动获取
        if not pathology:
            # 通过文件名获取病理号, 如果获取不到则病理号等于文件名, 需要手动修改
            new_match = re.match(r'(.+?)[-_](.+)', file_name)
            if new_match:
                pathology = new_match.group(1)
            else:
                pathology = file_name

        # 创建记录并保存
        image = Image.objects.create(
            pathology=pathology,
            file_name=file_name,
            resolution=resolution,
            storage_path=storage_path,
            waveplate_source=waveplate_source,
            is_learn=is_learn,
            diagnosis_label_doctor=diagnosis_label_doctor,
            diagnosis_label_zhu=diagnosis_label_zhu,
            making_way=making_way
        )
        image.save()

        # 返回文件更名对象
        return image
