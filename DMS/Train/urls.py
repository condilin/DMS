# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: urls.py
# @time: 19-1-10 下午4:17

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^trains/uploads/$', views.UploadFile.as_view()),  # 上传训练数据文件
    url(r'^trains/downloads/$', views.DownloadFile.as_view()),  # 文件下载
    url(r'^trains/(?P<pk>\d+)/$', views.SUDTrainView.as_view()),  # 查询/更新/删除
    url(r'^trains/$', views.SCTrainView.as_view()),  # 查询/新增
]
