# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: urls.py
# @time: 19-1-10 下午4:17

from django.conf.urls import url
from . import views

urlpatterns = [
    # url(r'^diagnosis/uploads/$', views.UploadFile.as_view()),  # 上传大图数据文件
    # url(r'^diagnosis/duplicates/$', views.FindDuplicatePathology.as_view()),  # 查找重复的病理号以及重复的次数
    # url(r'^diagnosis/(?P<pk>\d+)/$', views.SUDDiagnosisView.as_view()),  # 查询/更新/删除
    # url(r'^diagnosis/$', views.SCDiagnosisView.as_view()),  # 查询/新增
]
