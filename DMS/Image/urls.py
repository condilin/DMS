# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: urls.py
# @time: 18-12-25 下午2:23

from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^images/statistics/$', views.StatisticView.as_view()),  # 数据统计
    url(r'^images/duplicates/$', views.FindDuplicateFileName.as_view()),  # 查找重复的文件名以及重复的次数
    url(r'^images/downloads/$', views.DownloadFile.as_view()),  # 文件下载
    url(r'^images/updates/quality/$', views.UUpdateQuality.as_view()),  # 更新大图质量字段
    # url(r'^images/updates/$', views.UpdateDataBase.as_view()),  # 更新数据库

    url(r'^images/exact/$', views.SelectExactImageView.as_view()),  # 精确查询病理号(在SDoctorZhuDiagnoseView的路由前)

    url(r'^images/(?P<pk>\d+)/$', views.SUDImageView.as_view()),  # 查询/更新/删除
    url(r'^images/(?P<diagnose_label>\w+)/$', views.SDoctorZhuDiagnoseView.as_view()),  # 查询朱博士或医生有诊断标签的大图

    url(r'^images/$', views.SImageView.as_view()),  # 查询列表/新增一条记录
]
