# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: validation.py
# @time: 19-6-25 上午11:07

# form validation
from wtforms import Form, StringField
from wtforms.validators import Length, DataRequired, Regexp, NumberRange, AnyOf, Optional


class BaseInfoPaginateForm(Form):
    """verify paginate form """

    limit = StringField(
        validators=[
            DataRequired(message='字段不能为空'),
            # use Regexp function, precondition is must be use StringField !
            Regexp(regex='[1-9]', message='字段必须为数值且不为0')
        ]
    )
    offset = StringField(
        validators=[
            DataRequired(message='字段不能为空'),
            # use Regexp function, precondition is must be use StringField !
            Regexp(regex='\d+', message='字段必须为数值')
        ]
    )

    # customer function to verify params
    # def validate_limit(self, field):
    #     if not field.data.isdigit():
    #         raise ValidationError('the prams of limit must be an integer')
    #
    # def validate_offset(self, field):
    #     if not field.data.isdigit():
    #         raise ValidationError('the prams of offset must be an integer')


class BaseInfoPostForm(Form):

    version_name = StringField(
        validators=[
            DataRequired(message='字段不能为空'),
            Length(max=10, min=1, message='长度必须在%(min)s～%(max)s之间')

        ]
    )
    version_num = StringField(
        validators=[
            DataRequired(message='字段不能为空'),
            Length(max=10, min=1, message='长度必须在%(min)s～%(max)s之间')

        ]
    )
    responsible_people = StringField(
        validators=[
            DataRequired(message='字段不能为空'),
            Length(max=10, min=1, message='长度必须在%(min)s～%(max)s之间')

        ]
    )
    functional = StringField(
        validators=[
            DataRequired(message='字段不能为空'),
            Length(max=100, message='长度不能超过%(max)s个字符')
        ]
    )
    gitlab_link = StringField(
        validators=[
            Optional(),
            Length(max=50, message='长度不能超过%(max)s个字符')
        ]
    )
    remark = StringField(
        validators=[
            Optional(),
            Length(max=100, message='长度不能超过%(max)s个字符')

        ]
    )

    @property
    def save_column(self):
        return [i for i in BaseInfoPostForm.__dict__.keys() if i != 'meta' and not i.startswith('_')]


class DataSectionPostForm(Form):

    id = StringField(
        validators=[
            Optional(),
        ]
    )
    classify_num = StringField(
        validators=[
            Optional(),
            Length(max=4, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )
    specific_type = StringField(
        validators=[
            Optional()
        ]
    )
    preprocess = StringField(
        validators=[
            Optional()
        ]
    )
    label = StringField(
        validators=[
            Optional()
        ]
    )
    train_set = StringField(
        validators=[
            Optional()
        ]
    )
    test_set = StringField(
        validators=[
            Optional()
        ]
    )
    validate_set = StringField(
        validators=[
            Optional()
        ]
    )

    @property
    def save_column(self):
        return [i for i in DataSectionPostForm.__dict__.keys() if i != 'meta' and not i.startswith('_')]


class ModelSectionPostForm(Form):

    model = StringField(
        validators=[
            Optional(),
            Length(max=32, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )
    loss_function = StringField(
        validators=[
            Optional()
        ]
    )

    @property
    def save_column(self):
        return [i for i in ModelSectionPostForm.__dict__.keys() if i != 'meta' and not i.startswith('_')]


class HyperParamsPostForm(Form):

    optimizer = StringField(
        validators=[
            Optional(),
            Length(max=16, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )
    batch_size = StringField(
        validators=[
            Optional(),
            Length(max=8, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )
    total_epochs = StringField(
        validators=[
            Optional(),
            Length(max=8, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )
    dense_block_and_transition_layers = StringField(
        validators=[
            Optional(),
            Length(max=16, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )
    learning_rate = StringField(
        validators=[
            Optional(),
            Length(max=8, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )
    dropout_rate = StringField(
        validators=[
            Optional(),
            Length(max=8, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )
    nesterov_momentum = StringField(
        validators=[
            Optional(),
            Length(max=16, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )
    weight_decay = StringField(
        validators=[
            Optional(),
            Length(max=16, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )

    @property
    def save_column(self):
        return [i for i in HyperParamsPostForm.__dict__.keys() if i != 'meta' and not i.startswith('_')]


class AlgoPerformancePostForm(Form):

    best_epoch = StringField(
        validators=[
            Optional(),
            Length(max=8, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )
    train_loss = StringField(
        validators=[
            Optional(),
            Length(max=8, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )
    test_loss = StringField(
        validators=[
            Optional(),
            Length(max=8, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )
    test_accuracy = StringField(
        validators=[
            Optional(),
            Length(max=8, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )
    test_loss_average = StringField(
        validators=[
            Optional(),
            Length(max=8, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )
    false_negative = StringField(
        validators=[
            Optional(),
            Length(max=8, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )
    false_positive = StringField(
        validators=[
            Optional(),
            Length(max=8, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )

    @property
    def save_column(self):
        return [i for i in AlgoPerformancePostForm.__dict__.keys() if i != 'meta' and not i.startswith('_')]


class AlgoWeaknessPostForm(Form):

    algo_weakness = StringField(
        validators=[
            Optional(),
            Length(max=128, min=1, message='长度必须在%(min)s～%(max)s之间')
        ]
    )

    @property
    def save_column(self):
        return [i for i in AlgoWeaknessPostForm.__dict__.keys() if i != 'meta' and not i.startswith('_')]

