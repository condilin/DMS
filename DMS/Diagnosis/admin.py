from django.contrib import admin
from . import models
# Register your models here.


@admin.register(models.Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):

    # ------ 列表页的显示 ------- #

    # 定义函数，获取一对一/一对多关键表中的某个值
    # def get_pathology(self, obj):
    #     """获取病理号"""
    #     return obj.image_info_diagnosis.pathology

    # 在文章列表页面显示的字段, 不是详情里面的字段
    # list_display = ['id', 'get_pathology', 'his_diagnosis_label', 'create_time', 'update_time']
    list_display = ['id', 'his_diagnosis_label', 'create_time', 'update_time']

    # 设置哪些字段可以点击进入编辑界面
    # list_display_links = ('id', 'get_pathology')
    list_display_links = ('id', )

    # ------- 详情页信息 --------- #

    # 详情页显示的字段
