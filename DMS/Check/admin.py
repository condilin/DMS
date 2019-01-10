from django.contrib import admin
from . import models
# Register your models here.


@admin.register(models.Check)
class DiagnosisAdmin(admin.ModelAdmin):

    # ------ 列表页的显示 ------- #

    # 在文章列表页面显示的字段, 不是详情里面的字段
    list_display = ['id', 'check_version_number', 'cells_number', 'class_number', 'image_format',
                    'source', 'is_delete', 'create_time', 'update_time']

    # 设置哪些字段可以点击进入编辑界面
    list_display_links = ('id', 'check_version_number')

    # 每页显示10条记录
    list_per_page = 10
