# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: urls.py
# @time: 18-12-25 下午2:23

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^images/uploads/$', views.UploadFile.as_view()),  # 上传大图数据文件
    url(r'^images/statistics/$', views.StatisticView.as_view()),  # 数据统计
    url(r'^images/duplicates/$', views.FindDuplicateFileName.as_view()),  # 查找重复的文件名以及重复的次数
    url(r'^images/(?P<pk>\d+)/$', views.SUDImageView.as_view()),  # 查询/更新/删除
    url(r'^images/$', views.SCImageView.as_view()),  # 查询/新增
]
