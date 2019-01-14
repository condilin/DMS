from django.db import models


class Train(models.Model):
    """训练数据信息"""

    id = models.AutoField(primary_key=True, verbose_name=u'唯一主键')
    # 基本数据
    train_version = models.CharField(max_length=32, verbose_name=u'训练数据版本', null=True, blank=True)
    train_dataset = models.CharField(max_length=32, verbose_name=u'训练数据集', null=True, blank=True)
    cells_classify_num = models.CharField(max_length=4, verbose_name=u'细胞分类数量', null=True, blank=True)
    dataset_cells_num = models.CharField(max_length=16, verbose_name=u'原始数据集细胞数量', null=True, blank=True)
    weight = models.CharField(max_length=64, verbose_name=u'使用的权重', null=True, blank=True)
    target_model = models.CharField(max_length=128, verbose_name=u'目标模型', null=True, blank=True)
    # 数据预处理
    saturation = models.CharField(max_length=32, verbose_name=u'饱和度', null=True, blank=True)
    lightness = models.CharField(max_length=32, verbose_name=u'亮度', null=True, blank=True)
    rotation = models.CharField(max_length=32, verbose_name=u'旋转', null=True, blank=True)
    padding = models.CharField(max_length=16, verbose_name=u'贴边', null=True, blank=True)
    size = models.CharField(max_length=32, verbose_name=u'尺寸', null=True, blank=True)
    background = models.CharField(max_length=128, verbose_name=u'背景', null=True, blank=True)
    # 训练
    init_lr = models.CharField(max_length=128, verbose_name=u'初始学习率', null=True, blank=True)
    decay = models.CharField(max_length=128, verbose_name=u'衰减率', null=True, blank=True)
    epoch = models.CharField(max_length=8, verbose_name=u'轮数', null=True, blank=True)
    batch = models.CharField(max_length=8, verbose_name=u'批数', null=True, blank=True)
    final_step = models.CharField(max_length=16, verbose_name=u'训练步数', null=True, blank=True)
    # 验证表现最好的结果
    loss = models.FloatField(max_length=16, verbose_name='损失', null=True, blank=True)
    accuracy = models.FloatField(max_length=16, verbose_name='准确率', null=True, blank=True)
    best_epoch = models.CharField(max_length=8, verbose_name=u'最好的轮数', null=True, blank=True)

    is_delete = models.BooleanField(verbose_name='是否逻辑删除', default=False)
    create_time = models.DateTimeField(verbose_name=u'创建时间', auto_now_add=True)
    update_time = models.DateTimeField(verbose_name=u'更新时间', auto_now=True)

    class Meta:
        db_table = 'tb_train_info'  # 自定义数据库表的名称
        verbose_name = '训练数据'  # 在后台admin中显示表的中文名
        verbose_name_plural = verbose_name

    def __str__(self):
        return '训练数据版本为：%s' % self.train_version
