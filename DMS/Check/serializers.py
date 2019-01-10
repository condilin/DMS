# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: serializers.py
# @time: 19-1-9 下午4:45

from rest_framework import serializers
from .models import Check


class CheckSerializer(serializers.ModelSerializer):
    """查增"""

    class Meta:
        model = Check
        fields = ('id', 'check_version_number', 'cells_number', 'class_number',
                  'image_format', 'source')
