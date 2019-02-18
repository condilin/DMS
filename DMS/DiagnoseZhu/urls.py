# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: urls.py
# @time: 19-1-5 上午11:28

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^diagnosis/uploads/$', views.UploadFile.as_view()),  # 上传朱博士诊断标签数据文件
    url(r'^diagnosis/downloads/$', views.DownloadFile.as_view()),  # 下传朱博士诊断标签数据文件
    # url(r'^diagnosis/duplicates/$', views.FindDuplicatePathology.as_view()),  # 查找重复的病理号以及重复的次数
    # url(r'^diagnosis/(?P<pathology>\w+)/$', views.SUDDiagnosisView.as_view()),  # 查询/更新/删除
    url(r'^diagnosis/$', views.SCDiagnosisView.as_view()),  # 查询新增
]
