# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: serializers.py
# @time: 18-12-27 上午10:49


from rest_framework import serializers
from .models import FileRenameRecord
import re


class RenameSerializer(serializers.ModelSerializer):
    """查增"""

    class Meta:
        model = FileRenameRecord
        fields = ('id', 'pathology', 'current_file_name', 'his_name1',
                  'his_name2', 'his_name3', 'his_name4', 'his_name5')

    def create(self, validated_data):
        """重写create方法, 自动通过文件名获取病理号"""

        # 获取验证后的数据
        pathology = validated_data.get('pathology', None)
        current_file_name = validated_data.get('current_file_name', None)
        his_name1 = validated_data.get('his_name1', None)
        his_name2 = validated_data.get('his_name2', None)
        his_name3 = validated_data.get('his_name3', None)
        his_name4 = validated_data.get('his_name4', None)
        his_name5 = validated_data.get('his_name5', None)

        # 如果新增记录时, 如果有带上病理号, 则使用该病理号, 否则从文件名中自动获取
        if not pathology:
            # 通过文件名获取病理号, 如果获取不到则病理号等于文件名, 需要手动修改
            new_match = re.match(r'(.+?)[-_](.+)', current_file_name)
            if new_match:
                pathology = new_match.group(1)
            else:
                pathology = current_file_name

        # 创建记录并保存
        file_rename = FileRenameRecord.objects.create(
            pathology=pathology,
            current_file_name=current_file_name,
            his_name1=his_name1,
            his_name2=his_name2,
            his_name3=his_name3,
            his_name4=his_name4,
            his_name5=his_name5
        )
        file_rename.save()

        # 返回文件更名对象
        return file_rename
