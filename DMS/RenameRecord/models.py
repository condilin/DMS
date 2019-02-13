# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: nm.py
# @time: 19-2-13 下午12:15


from django.db import models


class RenameRecord(models.Model):
    """文件更名记录"""

    id = models.AutoField(primary_key=True, verbose_name=u'唯一主键')
    pathology = models.CharField(max_length=128, verbose_name=u'病理号', null=True, blank=True)
    his_file_name = models.CharField(max_length=128, verbose_name=u'曾用文件名', null=True, blank=True)
    is_delete = models.BooleanField(verbose_name='是否逻辑删除', default=False)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    class Meta:
        db_table = 'tb_rename_record'  # 自定义数据库表的名称
        verbose_name = '更名记录'  # 在后台admin中显示表的中文名
        verbose_name_plural = verbose_name

    def __str__(self):
        return '病理号为：%s' % self.pathology
