# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: monitor_0tiffs.py
# @time: 19-1-15 下午2:54

import pyinotify
import os
import time
from DMS.utils import variable
import logging
import requests
import json


# 配置日志
class ConfigLog(object):
    def __init__(self):
        # logging配置
        logging.basicConfig(
            level=logging.INFO,
            format=variable.LOG_FORMAT,
            filename=variable.LOG_NAME,
        )


# 事件回调函数
class EvenHandle(pyinotify.ProcessEvent):
    """事件处理"""

    def query_exist_record(self, type=None, event=None, pathology=None):
        """查询记录在数据库中是否存在"""

        # 查询大图文件名在数据库中是否存在
        if type == 'image':
            # 同时根据文件名和存储路径, 可以查询出唯一的一张大图, 查询该大图在数据库中的id
            file_name = os.path.splitext(event.name)[0]
            # 为了能和数据库中的路径进行匹配, 要去掉'/home/'
            samba_storage_path = event.path.replace('/home/', '')
            query_url = 'http://%s/api/v1/images/?file_name=%s&storage_path=%s' % (
                variable.SERVER_HOST, file_name, samba_storage_path
            )
        # 查询病例中对应的病理号在数据库中是否存在
        elif type == 'case':
            query_url = 'http://%s/api/v1/cases/?pathology=%s' % (variable.SERVER_HOST, pathology)
        # 查询朱博士诊断中对应的病理号在数据库中是否存在
        else:
            query_url = 'http://%s/api/v1/diagnosis/?pathology=%s' % (variable.SERVER_HOST, pathology)
        response = requests.get(query_url)
        # 转换成dict
        response_dict = json.loads(response.text)
        # 获取results
        results = response_dict.get('results', None)
        return results

    @staticmethod
    def timestamp_to_time(timestamp):
        """将时间戳类型转换成时间类型"""

        time_struct = time.localtime(timestamp)
        return time.strftime('%Y-%m-%d %H:%M:%S', time_struct)

    @staticmethod
    def rename_file_name(file_name):
        """修改文件名(根据病理号)"""

        # 如果文件名是长度为19的话，则说明是日期，则病理号等于文件名
        # 如果文件夹中没有下划线,则返回原字符串,否则会切分字符串超过2个, 但是也取第一个,因此匹配到还是匹配不到都取第一个
        pathology = file_name if len(file_name) == 19 else file_name.split('_')[0]
        return pathology

    def process_IN_CREATE(self, event):
        """
        1.文件被手动'复制'文件到监控文件夹内
        2.手动在监控文件夹中'创建'文件
        """
        print('IN_CREATE')
        logging.info('IN_CREATE: 监控文件夹下新增文件: %s' % event.pathname)

    def process_IN_MOVED_TO(self, event):
        """
        1.通过命令mv'剪切'文件到监控文件夹内
        2.文件被手动'剪切'文件到监控文件夹内
        3.手动/使用命令mv在监控文件夹中修改文件名（先删除再'创建'）
        """

        # 根据文件名和存储路径, 查询该大图在数据库中是否存在
        image_results = self.query_exist_record(type='image', event=event)

        # 如果存在, 则修改该记录的文件名, 否则新增一条记录
        if image_results:
            # 获取该大图的id值
            image_id = image_results[0]['id']
            # 文件名
            new_file_name = os.path.splitext(event.name)[0]

            # 修改数据
            image = {
                'file_name': new_file_name,
                'pathology': self.rename_file_name(new_file_name)
            }

            # 发送patch请求, 修改文件名和病理号
            patch_url = 'http://%s/api/v1/images/%s/' % (variable.SERVER_HOST, image_id)
            response = requests.patch(patch_url, json=image)
            if response.status_code != 200:
                logging.error('dms数据库修改数据失败：%s' % response.text)
                return

            print('IN_MOVED_TO: 修改')
            logging.warning('原文件名为：%s, 修改后的文件名为：%s' % (image_results[0]['file_name'], new_file_name))
        else:
            # --------------------- 倍数 --------------------- #
            resolution = event.pathname.split(variable.PATH)[1].split('/')[1]
            # --------------------- 文件名 --------------------- #
            file_name = os.path.splitext(event.name)[0]
            # --------------------- 病理号 --------------------- #
            pathology = self.rename_file_name(file_name)
            # --------------------- 存储路径 --------------------- #
            samba_storage_path = event.path.replace('/home/', '')
            # --------------- 文件创建时间（扫描时间）------------------ #
            file_create_time_ts = os.path.getctime(event.pathname)
            scan_time = self.timestamp_to_time(file_create_time_ts)
            # --------------------- 是否学习 --------------------- #
            # is_learn = True if file_name in train_data_file_name else False
            # --------------------- 查询病例信息(片源,制式,医生诊断) --------------------- #
            case_results = self.query_exist_record(type='case', pathology=pathology)
            if case_results:
                if len(case_results) >= 2:
                    diagnosis_label_doctor = '?: %s条病例信息' % len(case_results)
                    waveplate_source = [i['waveplate_source'] for i in case_results if i['waveplate_source']][0]
                    making_way = [i['making_way'] for i in case_results if i['making_way']][0]
                else:
                    diagnosis_label_doctor = case_results[0]['diagnosis_label_doctor']
                    waveplate_source = case_results[0]['waveplate_source']
                    making_way = case_results[0]['making_way']
            else:
                # 匹配不上,则为None
                diagnosis_label_doctor = None
                waveplate_source = None
                making_way = None
            # --------------------- 朱博士最新诊断标签 --------------------- #
            diagnosis_results = self.query_exist_record(type='diagnosis', pathology=pathology)
            if diagnosis_results:
                diagnosis_label_zhu = diagnosis_results[0]['diagnosis_label_lastest']
            else:
                diagnosis_label_zhu = None

            # 新增数据
            image = {
                'resolution': resolution,
                'file_name': file_name,
                'pathology': pathology,
                'storage_path': samba_storage_path,
                'scan_time': scan_time,
                'diagnosis_label_doctor': diagnosis_label_doctor,
                'waveplate_source': waveplate_source,
                'making_way': making_way,
                'diagnosis_label_zhu': diagnosis_label_zhu
            }

            # 发送post请求, 新增一条大图记录
            post_url = 'http://%s/api/v1/images/' % variable.SERVER_HOST
            response = requests.post(post_url, json=image)
            if response.status_code != 201:
                logging.error('dms数据库新增数据失败：%s' % response.text)
                return

            logging.info('dms数据库新增一条大图记录, 大图名为：%s' % event.name)

        print('IN_MOVED_TO: 新增')
        logging.info('IN_MOVED_TO: 监控文件夹下新增文件: %s' % event.pathname)

    def process_IN_DELETE(self, event):
        """
        1.通过命令rm将监控文件夹中的文件'删除'
        2.手动'delete'监控文件夹中的文件
        """

        # 根据文件名和倍数, 查询该大图在数据库中是否存在
        results = self.query_exist_record(type='image', event=event)

        # 如果不存在, 返回即可, 反正该条记录也是要删除, 不存在最好
        if not results:
            logging.error('dms数据库中不存在该条记录：%s' % event.pathname)
            return

        # 获取该大图的id值
        image_id = results[0]['id']
        # 删除dms数据库中该大图的记录
        response = requests.delete('http://%s/api/v1/images/%s/' % (variable.SERVER_HOST, image_id))
        if response.status_code != 204:
            logging.error('dms数据库删除数据失败：%s' % response.text)
            return

        print('IN_DELETE')
        logging.warning('IN_DELETE: 监控文件夹下删除文件: %s' % event.pathname)

    def process_IN_MOVED_FROM(self, event):
        """
        1.手动从监控文件夹中将文件移动到废纸娄
        2.手动从监控文件夹中将文件通过剪切方式移走
        3.手动/使用命令mv在监控文件夹中修改文件名（先'删除'再创建）
        """
        print('IN_MOVED_FROM')
        logging.warning('IN_MOVED_FROM: 监控文件夹下移走文件: %s' % event.pathname)


class FSmonitor(object):

    @staticmethod
    def suffix_filter(event):
        """监视dir中指定的后缀文件及目录"""

        # 判断后缀是否为{'.kfb', '.tiff', 'txt'}
        suffix_name = os.path.splitext(event.name)[1]
        # 判断文件夹是否为20X或40X
        dir_name = event.pathname.split(variable.PATH)[1].split('/')[1]

        # return True to stop processing of event (to "stop chaining")
        # 不符合其中一个条件, 则返回True, 停止chaining
        if suffix_name not in variable.SUFFIX_TYPE or dir_name not in variable.DIR_TYPE:
            return True
        else:
            return False

    def monitor(self):
        # 创建WatchManager对象
        wm = pyinotify.WatchManager()

        # 监控事件
        mask = pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO | pyinotify.IN_DELETE | pyinotify.IN_MOVED_FROM
        # 添加监控：指定需要监控的目录, 指定需要监控的事件
        wm.add_watch(variable.PATH, mask, auto_add=True, rec=True)

        # 交给Notifier进行处理:
        # 指定处理类：EvenHandle, pevent参数：指定钩子函数, 筛选指定监视的后缀文件
        notifier = pyinotify.Notifier(wm, EvenHandle(pevent=self.suffix_filter))
        # 循环处理
        notifier.loop()
        # while True:
        #     try:
        #         notifier.process_events()
        #         if notifier.check_events():
        #             notifier.read_events()
        #     except KeyboardInterrupt:
        #         notifier.stop()
        #         break


if __name__ == '__main__':
    # 开启日志
    ConfigLog()

    logging.info('----------- start monitor：%s -----------' % variable.PATH)

    # 开启监控
    monitor_samba_0tiff = FSmonitor()
    monitor_samba_0tiff.monitor()

    logging.info('=========== stop monitor：%s ============\n\n\n' % variable.PATH)
