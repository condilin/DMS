from django.db import models


class Train(models.Model):
    """训练数据信息"""

    id = models.AutoField(primary_key=True, verbose_name=u'唯一主键')
    # 基本数据
    train_version = models.CharField(max_length=32, verbose_name=u'训练数据版本', null=True, blank=True)
    train_dataset = models.CharField(max_length=32, verbose_name=u'训练数据集', null=True, blank=True)
    cells_classify_num = models.IntegerField(verbose_name=u'细胞分类数量', default=0)
    dataset_cells_num = models.IntegerField(verbose_name=u'原始数据集细胞数量', default=0)
    weight = models.CharField(max_length=64, verbose_name=u'使用的权重', null=True, blank=True)
    target_model = models.CharField(max_length=128, verbose_name=u'目标模型', null=True, blank=True)
    # 数据预处理
    saturation = models.CharField(max_length=32, verbose_name=u'饱和度', null=True, blank=True)
    lightness = models.CharField(max_length=32, verbose_name=u'亮度', null=True, blank=True)
    rotation = models.CharField(max_length=32, verbose_name=u'旋转', null=True, blank=True)


    diagnosis_label_doctor = models.CharField(max_length=64, verbose_name=u'医生诊断标签', null=True, blank=True)
    waveplate_source = models.CharField(max_length=64, verbose_name=u'片源', null=True, blank=True)
    making_way = models.CharField(max_length=64, verbose_name=u'切片制式', null=True, blank=True)
    check_date = models.CharField(max_length=128, verbose_name=u'采样/检查时间', blank=True, null=True)
    diagnosis_date = models.CharField(max_length=128, verbose_name=u"诊断时间", blank=True, null=True)
    last_menstruation = models.CharField(max_length=128, verbose_name=u'末次经期时间', blank=True, null=True)
    clinical_observed = models.CharField(max_length=256, verbose_name=u"临床所见", null=True, blank=True)
    diagnosis_label_doctor_filter = models.CharField(max_length=64, verbose_name=u'医生诊断标签筛选', null=True, blank=True)

    is_delete = models.BooleanField(verbose_name='是否逻辑删除', default=False)
    create_time = models.DateTimeField(verbose_name=u'创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name=u'更新时间', auto_now=True)

    class Meta:
        db_table = 'tb_train_info'  # 自定义数据库表的名称
        verbose_name = '训练数据'  # 在后台admin中显示表的中文名
        verbose_name_plural = verbose_name

    def __str__(self):
        return '训练数据版本为：%s' % self.train_version
