# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: monitor_0tiffs.py
# @time: 19-1-15 下午2:54

import pyinotify
import os
import logging
from DMS import settings


# 配置日志
class ConfigLog(object):
    def __init__(self):
        # 日志输出的位置
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.log_name = os.path.join(self.base_dir, 'logs/monitor_0tiffs.log')
        self.format = '%(levelname)s [%(asctime)s] %(message)s'
        # logging配置
        logging.basicConfig(
            level=logging.INFO,
            format=self.format,
            filename=self.log_name,
        )


# 事件回调函数
class EvenHandle(pyinotify.ProcessEvent):
    """事件处理"""

    def process_IN_CREATE(self, event):
        """
        1.手动复制文件到监控文件夹
        2.手动剪切文件到监控文件夹
        3.手动在监控文件夹中创建文件
        """
        logging.info('监控文件夹下新增文件: %s' % event.name)

    def process_IN_MOVED_TO(self, event):
        """
        1.通过命令mv剪切文件到监控文件夹中
        """
        logging.info('监控文件夹下新增文件: %s' % event.name)

    def process_IN_DELETE(self, event):
        """
        1.通过命令rm将监控文件夹中的文件删除
        """
        logging.warning('监控文件夹下移走文件: %s' % event.name)

    def process_IN_MOVED_FROM(self, event):
        """
        1.手动从监控文件夹中将文件移动到废纸娄
        2.手动从监控文件夹中将文件通过剪切方式移走
        """
        logging.warning('监控文件夹下移走文件: %s' % event.name)

    def process_IN_MODIFY(self, event):
        """
        1.手动修改文件名
        """
        logging.warning('监控文件夹下修改了文件名: %s' % event.name)


def tiffs_monitor(path='.'):
    # 创建WatchManager对象
    wm = pyinotify.WatchManager()

    # 监控事件
    mask = pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO | pyinotify.IN_DELETE | pyinotify.IN_MOVED_FROM | pyinotify.IN_MODIFY
    # 添加监控：指定需要监控的目录, 指定需要监控的事件
    wm.add_watch(path, mask, auto_add=True, rec=True)

    # 交给Notifier进行处理: 指定处理函数
    notifier = pyinotify.Notifier(wm, EvenHandle())
    # 循环处理
    notifier.loop()


if __name__ == '__main__':
    # 开启日志
    ConfigLog()

    # 开启监控
    # monitor_path = os.path.join(settings.DATA_SAMBA_PREX, settings.DATA_SAMBA_IMAGE_LOCATE)
    monitor_path = '.'
    logging.info('----------- start monitor：%s -----------' % monitor_path)

    tiffs_monitor(path=monitor_path)

    logging.info('=========== stop monitor：%s ============\n\n\n' % monitor_path)
