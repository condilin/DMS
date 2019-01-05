# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: serializers.py
# @time: 18-12-25 下午2:54

from rest_framework import serializers
from .models import Image


class ImageSerializer(serializers.ModelSerializer):
    """查增"""

    class Meta:
        model = Image
        fields = ('id', 'pathology', 'file_name', 'resolution', 'storage_path',
                  'waveplate_source', 'is_learn', 'diagnosis_label_doctor',
                  'diagnosis_label_zhu', 'making_way', 'scan_time')
