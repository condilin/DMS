from django.db import models


class DiagnoseZhu(models.Model):
    """朱博士对大图的诊断标签"""
    id = models.AutoField(primary_key=True, verbose_name=u'唯一主键')
    pathology = models.CharField(max_length=128, verbose_name=u'病理号', null=True, blank=True)
    his_diagnosis_label = models.CharField(max_length=64, verbose_name=u'朱博士历史诊断标签', null=True, blank=True)

    is_delete = models.BooleanField(verbose_name=u'是否逻辑删除', default=False)
    create_time = models.DateTimeField(verbose_name=u'创建时间', auto_now_add=True)

    class Meta:
        db_table = 'tb_diagnose_zhu'  # 自定义数据库表的名称
        verbose_name = '朱博士历史诊断标签'  # 在后台admin中显示表的中文名
        verbose_name_plural = verbose_name

    def __str__(self):
        return '病理号为: %s' % self.pathology


class DiagnoseZhuTmp(models.Model):
    """朱博士对大图的诊断标签"""
    id = models.AutoField(primary_key=True, verbose_name=u'唯一主键')
    pathology = models.CharField(max_length=128, verbose_name=u'病理号', null=True, blank=True)
    his_diagnosis_label = models.CharField(max_length=256, verbose_name=u'朱博士历史诊断标签', null=True, blank=True)

    is_delete = models.BooleanField(verbose_name=u'是否逻辑删除', default=False)
    create_time = models.DateTimeField(verbose_name=u'创建时间', auto_now_add=True)

    class Meta:
        db_table = 'tb_diagnose_zhu_tmp'  # 自定义数据库表的名称
        verbose_name = '朱博士历史诊断标签临时表'  # 在后台admin中显示表的中文名
        verbose_name_plural = verbose_name

    def __str__(self):
        return '病理号为: %s' % self.pathology
