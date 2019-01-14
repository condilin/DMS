# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: serializers.py
# @time: 19-1-10 下午4:17


from rest_framework import serializers
from .models import Train


class TrainSerializer(serializers.ModelSerializer):
    """查增"""

    class Meta:
        model = Train
        fields = ('id', 'train_version', 'train_dataset', 'cells_classify_num',
                  'dataset_cells_num', 'weight', 'target_model', 'saturation',
                  'lightness', 'rotation', 'padding', 'size', 'background', 'init_lr',
                  'decay', 'epoch', 'batch', 'final_step', 'loss', 'accuracy', 'best_epoch')
