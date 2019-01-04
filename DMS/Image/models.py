from django.db import models
from Case.models import Case
from Diagnosis.models import Diagnosis


class Image(models.Model):
    """大图信息"""

    # 自动扫描DATA/0TIFF文件夹获取
    id = models.AutoField(primary_key=True, verbose_name=u'唯一主键')
    pathology = models.CharField(max_length=128, verbose_name=u'病理号', null=True, blank=True)
    file_name = models.CharField(max_length=128, verbose_name=u'文件名', null=True, blank=True)
    resolution = models.CharField(max_length=8, verbose_name=u'分辨率', null=True, blank=True)
    storage_path = models.CharField(max_length=256, verbose_name=u'存储路径', null=True, blank=True)
    waveplate_source = models.CharField(max_length=64, verbose_name=u'片源', null=True, blank=True)
    is_learn = models.BooleanField(verbose_name=u'是否学习', default=False)
    diagnosis_label_doctor = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'医生诊断标签')
    diagnosis_label_zhu = models.CharField(max_length=128, blank=True, null=True, verbose_name=u'朱博士诊断标签')
    making_way = models.CharField(max_length=64, verbose_name=u'切片制式', null=True, blank=True)
    scan_time = models.CharField(max_length=64, verbose_name=u'扫描时间', null=True, blank=True)

    is_delete = models.BooleanField(verbose_name=u'是否逻辑删除', default=False)
    create_time = models.DateTimeField(verbose_name=u'创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name=u'更新时间', auto_now=True)

    class Meta:
        db_table = 'tb_big_image_info'  # 自定义数据库表的名称
        verbose_name = '大图信息'  # 在后台admin中显示表的中文名
        verbose_name_plural = verbose_name

    def __str__(self):
        return '病理号为：%s, 当前文件名为：%s' % (self.pathology, self.file_name)
