# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: serializers.py
# @time: 18-12-26 下午3:02

from rest_framework import serializers
from .models import Case


class CaseSerializer(serializers.ModelSerializer):
    """查增"""

    class Meta:
        model = Case
        # fields = ('id', 'pathology', 'diagnosis_label_doctor', 'waveplate_source',
        #           'production_date', 'entry_date', 'last_menstruation', 'clinical_observed',
        #           'diagnose_result_doctor')
        fields = '__all__'
