# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: urls.py
# @time: 18-12-27 上午10:03

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^renames/uploads/$', views.UploadFile.as_view()),  # 上传大图数据文件
    url(r'^renames/duplicates/$', views.FindDuplicateFileName.as_view()),  # 查找重复的文件名以及重复的次数
    url(r'^renames/(?P<pk>\d+)/$', views.SUDRenameView.as_view()),  # 查询/更新/删除
    url(r'^renames/$', views.SCRenameView.as_view()),  # 查询/新增
]
