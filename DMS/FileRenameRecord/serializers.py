# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: serializers.py
# @time: 18-12-27 上午10:49


from rest_framework import serializers
from .models import FileRenameRecord


class RenameSerializer(serializers.ModelSerializer):
    """查增"""

    class Meta:
        model = FileRenameRecord
        fields = ('id', 'pathology', 'current_file_name', 'his_name1',
                  'his_name2', 'his_name3', 'his_name4', 'his_name5')
