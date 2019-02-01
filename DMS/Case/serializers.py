# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: serializers.py
# @time: 18-12-26 下午3:02

from rest_framework import serializers
from .models import Case


class CaseSerializer(serializers.ModelSerializer):
    """查增"""
    dup_count = serializers.CharField(read_only=True)

    class Meta:
        model = Case
        fields = ('id', 'pathology', 'diagnosis_label_doctor', 'waveplate_source',
                  'making_way', 'check_date', 'diagnosis_date', 'last_menstruation',
                  'clinical_observed', 'dup_count')


class SearchDupCaseSerializer(serializers.ModelSerializer):
    """查"""
    dup_count = serializers.CharField(read_only=True)

    class Meta:
        model = Case
        # 序列化返回只有两个字段
        fields = ('pathology', 'dup_count')
