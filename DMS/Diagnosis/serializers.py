# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: serializers.py
# @time: 19-1-5 上午11:20

from rest_framework import serializers
from .models import Diagnosis


class DiagnoseSerializer(serializers.ModelSerializer):
    """查增"""

    class Meta:
        model = Diagnosis
        fields = ('id', 'pathology', 'diagnosis_label_lastest', 'his_diagnosis_label1',
                  'his_diagnosis_label2', 'his_diagnosis_label3', 'his_diagnosis_label4')
