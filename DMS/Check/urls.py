# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: urls.py
# @time: 19-1-9 下午4:42

from django.conf.urls import url

from . import views

urlpatterns = [
    # url(r'^temp/$', views.base_view),
    # url(r'^echo/$', views.echo),
    url(r'^checks/details/downloads/$', views.DownloadFile.as_view()),  # 下传更新审核详细数据记录
    url(r'^checks/updates/$', views.UpdateCheck.as_view()),  # 更新审核数据记录
    url(r'^checks/(?P<pk>\d+)/$', views.SUDCheckView.as_view()),  # 查询/更新/删除
    url(r'^checks/$', views.SCCheckView.as_view()),  # 查询/新增
]
