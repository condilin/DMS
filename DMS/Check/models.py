from django.db import models


class Check(models.Model):
    """审核数据"""

    id = models.AutoField(primary_key=True, verbose_name=u'唯一主键')
    check_version_number = models.CharField(max_length=64, verbose_name=u'审核版本号', null=True, blank=True)
    cells_number = models.IntegerField(verbose_name='细胞数量', default=0)
    class_number = models.IntegerField(verbose_name='分类数量', default=0)
    classify = models.CharField(max_length=256, verbose_name=u'分类', null=True, blank=True)
    storage_path = models.CharField(max_length=128, verbose_name=u'存储路径', null=True, blank=True)
    image_format = models.CharField(max_length=64, verbose_name=u'图像格式', null=True, blank=True)
    source = models.CharField(max_length=128, verbose_name=u'数据来源', null=True, blank=True)

    is_delete = models.BooleanField(verbose_name=u'是否逻辑删除', default=False)
    create_time = models.DateTimeField(verbose_name=u'创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name=u'更新时间', auto_now=True)

    class Meta:
        db_table = 'tb_check_data'  # 自定义数据库表的名称
        verbose_name = '审核数据'  # 在后台admin中显示表的中文名
        verbose_name_plural = verbose_name

    def __str__(self):
        return '审核数据版本号为: %s' % self.check_version_number


class CheckDetail(models.Model):
    """训练详情"""

    id = models.AutoField(primary_key=True, verbose_name=u'唯一主键')
    image = models.CharField(max_length=64, verbose_name=u'大图名称', null=True, blank=True)
    classify = models.CharField(max_length=32, verbose_name=u'分类', null=True, blank=True)
    class_number = models.IntegerField(verbose_name='分类数量', default=0)

    is_delete = models.BooleanField(verbose_name=u'是否逻辑删除', default=False)
    create_time = models.DateTimeField(verbose_name=u'创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name=u'更新时间', auto_now=True)

    class Meta:
        db_table = 'tb_check_detail'  # 自定义数据库表的名称
        verbose_name = '训练详情'  # 在后台admin中显示表的中文名
        verbose_name_plural = verbose_name

    def __str__(self):
        return '大图的名称: %s' % self.image
