# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: urls.py
# @time: 18-12-26 下午1:05


from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^cases/uploads/$', views.UploadFile.as_view()),  # 上传病例数据文件
    url(r'^cases/downloads/$', views.DownloadFile.as_view()),  # 下传病例数据文件
    url(r'^cases/downloads/duppaths/$', views.DownloadDuplicateName.as_view()),  # 下传有重复病理号的病例数据文件
    url(r'^cases/duplicates/$', views.FindDuplicateFileName.as_view()),  # 查找重复的文件名以及重复的次数
    url(r'^cases/(?P<pk>\d+)/$', views.SUDCaseView.as_view()),  # 查询/更新/删除
    url(r'^cases/$', views.SCCaseView.as_view()),  # 查询/新增
]
