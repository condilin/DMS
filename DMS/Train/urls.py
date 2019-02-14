# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: urls.py
# @time: 19-1-10 下午4:17

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^trains/uploads/$', views.UploadModelInfoFile.as_view()),  # 上传模型训练文件
    url(r'^trains/uploads/trained/$', views.UploadTrainedImageFile.as_view()),  # 上传已训练大图数据文件

    url(r'^trains/downloads/$', views.DownloadModelInfoFile.as_view()),  # 模型训练下载
    url(r'^trains/downloads/trained/$', views.DownloadTrainedImageFile.as_view()),  # 已训练大图数据文件下载

    url(r'^trains/(?P<pk>\d+)/$', views.SUDTrainView.as_view()),  # 查询/更新/删除

    url(r'^trains/$', views.SCTrainView.as_view()),  # 查询/新增
    url(r'^trains/trained/$', views.STrainedImageView.as_view()),  # 查询
]
