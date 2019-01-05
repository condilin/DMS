"""DMS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import include
from rest_framework_swagger.views import get_swagger_view

schema_view = get_swagger_view(title='DMS接口文档')

urlpatterns = [
    url(r'^api/v1/admin/', admin.site.urls),  # 后台管理员
    url(r'^api/v1/docs/', schema_view),  # 接口文档
    url(r'^api/v1/', include('Case.urls')),  # 病例信息
    url(r'^api/v1/', include('Image.urls')),  # 大图信息
    url(r'^api/v1/', include('FileRenameRecord.urls')),  # 文件更名信息
    url(r'^api/v1/', include('Diagnosis.urls')),  # 朱博士诊断信息
]
