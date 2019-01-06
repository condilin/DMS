from django.contrib import admin
from . import models
# Register your models here.


@admin.register(models.Case)
class CaseAdmin(admin.ModelAdmin):

    # ------ 列表页的显示 ------- #

    # 在文章列表页面显示的字段, 不是详情里面的字段
    # 将show_tags函指定到列表中即可显示多对多字段的结果!!
    list_display = ['id', 'pathology', 'diagnosis_label_doctor', 'waveplate_source',
                    'making_way', 'create_time', 'update_time']

    # 设置哪些字段可以点击进入编辑界面
    list_display_links = ('id', 'pathology')

    # 每页显示10条记录
    list_per_page = 10

    # 按最新创建的时间排序. ordering设置默认排序字段，负号表示降序排序
    ordering = ('-update_time',)

    # 搜索栏
    search_fields = ['pathology']

    # 过滤器
    list_filter = ['waveplate_source', 'making_way']
