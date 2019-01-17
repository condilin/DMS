# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: variable.py
# @time: 19-1-16 下午2:56


# 日志输出的位置
LOG_NAME = '/home/data_samba/TMP/jinquan/monitor_0tiffs.log/monitor_0tiffs.log'
# 输出格式
LOG_FORMAT = '%(levelname)s [%(asctime)s] %(message)s'


# 所有大图的后缀类型
SUFFIX_TYPE = {'.kfb', '.tiff', 'txt'}
# 监控的文件夹
DIR_TYPE = {'20X', '40X'}
# 监控路径
PATH = '/home/data_samba/LCT_DATA/0TIFF'


# dms地址
SERVER_HOST = '192.168.2.179'


# 请求头信息
headers = {'Content-Type': 'application/json'}


