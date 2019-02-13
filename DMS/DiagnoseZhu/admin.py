from django.contrib import admin
from . import models


@admin.register(models.DiagnoseZhu)
class DiagnosisAdmin(admin.ModelAdmin):

    # ------ 列表页的显示 ------- #

    # 定义函数，获取一对一/一对多关键表中的某个值
    # def get_pathology(self, obj):
    #     """获取病理号"""
    #     return obj.image_info_diagnosis.pathology

    # 在文章列表页面显示的字段, 不是详情里面的字段
    list_display = ['id', 'pathology', 'his_diagnosis_label', 'create_time']

    # 设置哪些字段可以点击进入编辑界面
    list_display_links = ('id', 'pathology')

    # 每页显示10条记录
    list_per_page = 10

    # 按最新创建的时间排序. ordering设置默认排序字段，负号表示降序排序
    ordering = ('-create_time',)

    # 搜索栏
    search_fields = ['pathology']
