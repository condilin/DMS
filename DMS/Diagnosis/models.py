from django.db import models
from Image.models import Image

# Create your models here.


class Diagnosis(models.Model):
    """朱博士对大图的诊断标签"""
    id = models.AutoField(primary_key=True, verbose_name=u'唯一主键')
    # pathology = models.CharField(max_length=128, verbose_name=u'病理号', null=True, blank=True)
    # file_name = models.CharField(max_length=128, verbose_name=u'文件名', null=True, blank=True)
    # diagnosis_label_lastest = models.CharField(max_length=64, verbose_name=u'朱博士最新诊断标签', null=True, blank=True)
    # image_info_diagnosis = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='image_info_diagnosis',
    #                                          blank=True, null=True, verbose_name=u'大图信息')
    his_diagnosis_label = models.CharField(max_length=64, verbose_name=u'朱博士历史诊断标签', null=True, blank=True)

    create_time = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    update_time = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    class Meta:
        db_table = 'tb_image_diagnosis_zhu'  # 自定义数据库表的名称
        verbose_name = '朱博士历史诊断标签'  # 在后台admin中显示表的中文名
        verbose_name_plural = verbose_name

    def __str__(self):
        return '历史诊断标签为: %s' % self.his_diagnosis_label
