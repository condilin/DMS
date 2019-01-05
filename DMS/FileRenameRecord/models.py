from django.db import models


class FileRenameRecord(models.Model):
    """文件更名记录"""

    id = models.AutoField(primary_key=True, verbose_name=u'唯一主键')
    pathology = models.CharField(max_length=128, verbose_name=u'病理号', null=True, blank=True)
    current_file_name = models.CharField(max_length=128, verbose_name=u'当前文件名', null=True, blank=True)
    his_name1 = models.CharField(max_length=128, verbose_name=u'曾用名1', null=True, blank=True)
    his_name2 = models.CharField(max_length=128, verbose_name=u'曾用名2', null=True, blank=True)
    his_name3 = models.CharField(max_length=128, verbose_name=u'曾用名3', null=True, blank=True)
    his_name4 = models.CharField(max_length=128, verbose_name=u'曾用名4', null=True, blank=True)
    his_name5 = models.CharField(max_length=128, verbose_name=u'曾用名5', null=True, blank=True)

    is_delete = models.BooleanField(verbose_name='是否逻辑删除', default=False)
    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        db_table = 'tb_rename'  # 自定义数据库表的名称
        verbose_name = '文件更名记录'  # 在后台admin中显示表的中文名
        verbose_name_plural = verbose_name

    def __str__(self):
        return '当前的文件名为：%s, 病理号为：%s' % (self.current_file_name, self.pathology)
