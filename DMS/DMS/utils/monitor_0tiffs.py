# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: monitor_0tiffs.py
# @time: 19-1-15 下午2:54

import pyinotify
from pyinotify import IN_CREATE, IN_MOVED_TO, IN_DELETE, IN_MOVED_FROM, IN_MOVE_SELF
import os
import re
import time
import logging
import requests
import json


# 配置日志/初始化变量
class ConfigLog(object):
    def __init__(self):
        # 日志输出的位置
        self.log_name = './monitor_0tiffs.log'
        # 输出格式
        self.log_format = '%(levelname)s [%(asctime)s] %(message)s'

        # logging配置
        logging.basicConfig(
            level=logging.INFO,
            format=self.log_format,
            filename=self.log_name,
        )


# 事件回调函数
class EvenHandle(pyinotify.ProcessEvent):
    """事件处理"""

    def my_init(self, **kargs):
        # dms地址
        self.host = '192.168.2.179'
        # 监控路径
        self.path = '/home/data_samba/LCT_DATA/0TIFF'
        # self.path = '/home/data_samba/TMP/test_monitor'
        # 创建队列1, 存储文件修改名字前的文件名
        self.in_move_from_old_file_name = []
        # 创建队列2, 存储文件修改名字前的文件名的存储路径
        self.in_move_from_old_storage_path = []
        # 状态开关, 用于确定使用的是复制监控还是剪切监控
        self.use_in_move_to = True

    def query_exist_record(self, type=None, **kwargs):
        """查询记录在数据库中是否存在"""

        # 查询大图文件名在数据库中是否存在
        if type == 'image':
            # 同时根据文件名和存储路径, 可以查询出唯一的一张大图, 查询该大图在数据库中的id
            # 注意：in_move_to此时获取到的名字是已重命名之后的, 因此通过此文件名去数据库中查询id是查不到的
            # 需要通过旧文件名和旧的存储路径才能查询到
            query_url = 'http://%s/api/v1/images/?file_name=%s&storage_path=%s' % (
                self.host, kwargs['old_file_name'], kwargs['old_storage_path']
            )
        # 查询病例中对应的病理号在数据库中是否存在
        elif type == 'case':
            query_url = 'http://%s/api/v1/cases/?pathology=%s' % (self.host, kwargs['pathology'])
        # 查询朱博士诊断中对应的病理号在数据库中是否存在
        else:
            query_url = 'http://%s/api/v1/diagnosis/?pathology=%s' % (self.host, kwargs['pathology'])
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

    @staticmethod
    def waveplate_source_extra(file_name):
        """通过病理号提取出片源"""

        # 将完整的文件名，去掉后缀
        upper_pathology = file_name.split('_')[0].upper()

        if upper_pathology.startswith('TJ') or upper_pathology.startswith(
                'TB') or upper_pathology.startswith('TC') or upper_pathology.startswith(
                'TD') or upper_pathology.startswith('DS') or upper_pathology.startswith('CA'):
            waveplate_source = '华银'

        elif upper_pathology.startswith('T'):
            waveplate_source = '泉州'

        elif upper_pathology.startswith('NJ'):
            waveplate_source = '华银南京'

        elif upper_pathology.startswith('SPH') or upper_pathology.startswith('SZH'):
            waveplate_source = '深圳人民医院'

        elif upper_pathology.startswith('EL') or upper_pathology.startswith('L'):
            waveplate_source = '郑大一附属医院'

        elif upper_pathology.startswith('GZY'):
            waveplate_source = '广州军区总医院'

        elif upper_pathology.startswith('BD') or upper_pathology.startswith('XB') or upper_pathology.startswith(
                'FX') or upper_pathology.startswith('BV') or upper_pathology.startswith(
                'ZA') or upper_pathology.isdigit():
            waveplate_source = '南方医院'

        elif re.match('\d{4}-\d{2}-\d{2}', upper_pathology):
            waveplate_source = '南方医院或华银'

        else:
            waveplate_source = 'unknown'

        return waveplate_source

    def process_IN_CREATE(self, event):
        """
        1.文件被手动'复制'文件到监控文件夹内
        2.手动在监控文件夹中'创建'文件
        """
        # 如果是创建文件夹, 则不需要在dms中保存该记录, 直接结束
        if event.dir:
            logging.warning('IN_CREATE: 创建一个新的文件夹：%s' % event.pathname)
            return

        # 将状态改为Flase
        self.use_in_move_to = False
        # 调用process_IN_MOVED_TO的方法创建一条新的记录
        self.process_IN_MOVED_TO(event)

    def process_IN_MOVED_TO(self, event):
        """
        1.通过命令mv'剪切'文件到监控文件夹内
        2.文件被手动'剪切'文件到监控文件夹内
        3.手动/使用命令mv在监控文件夹中修改文件名（先删除再'创建'）
        """

        # 如果是修改文件夹的名称, 则不需要在dms中保存该记录, 直接结束
        if event.dir:
            logging.warning('IN_MOVED_TO：文件夹修改名字后为：%s' % event.pathname)
            return

        # --------------------- 新的文件名 --------------------- #
        new_file_name, suffix_name = os.path.splitext(event.name)
        # --------------------- 病理号 --------------------- #
        pathology = self.rename_file_name(new_file_name)
        # --------------------- 片源 ----------------------- #
        waveplate_source = self.waveplate_source_extra(new_file_name)
        # --------------------- 新的存储路径 --------------------- #
        new_storage_path = event.path.replace('/home/', '')

        try:
            # 如果是触发process_IN_CREATE方法, 则手动抛出异常
            if not self.use_in_move_to:
                raise Exception('用户是通过复制创建内容, 而不是通过剪切！')

            # 如果可以从队列中获取到大图的原文件名, 说明用户的操作是：修改文件名或移动图片路径（in_move_from和in_move_to操作)
            old_file_name = self.in_move_from_old_file_name.pop(0)
            old_storage_path = self.in_move_from_old_storage_path.pop(0)
            # 如果旧的文件名和新的文件名不一样, 说明用户在修改文件名, 需要在数据库修改文件名和病理号以及片源
            if old_file_name != new_file_name:
                image = {
                    'file_name': new_file_name,
                    'pathology': pathology,
                    'waveplate_source': waveplate_source
                }
                # 根据旧文件名和旧存储路径, 查询该大图在数据库中是否存在
                image_results = self.query_exist_record(type='image', old_file_name=old_file_name,
                                                        old_storage_path=old_storage_path)
            else:
                # 否则说明用户是进行文件的移动, 是修改文件存储路径即可
                image = {
                    'storage_path': new_storage_path
                }
                # 根据旧文件名和旧存储路径, 查询该大图在数据库中是否存在
                image_results = self.query_exist_record(type='image', old_file_name=old_file_name,
                                                        old_storage_path=old_storage_path)

            # 获取该大图的id值
            image_id = image_results[0]['id']

            # 发送patch请求, 修改文件名和病理号
            response = requests.patch('http://%s/api/v1/images/%s/' % (self.host, image_id), json=image)
            if response.status_code != 200:
                logging.error('dms数据库修改数据失败：%s' % response.text)
                return

            logging.warning('原文件名为：%s, 修改后的文件名为：%s' % (image_results[0]['file_name'], new_file_name))

        except Exception as e:
            # 否则是新剪切进来的大图, 因此新增一条记录

            # --------------------- 倍数 --------------------- #
            resolution = event.pathname.split(self.path)[1].split('/')[1]
            # --------------- 文件创建时间（扫描时间）------------------ #
            file_create_time_ts = os.path.getctime(event.pathname)
            scan_time = self.timestamp_to_time(file_create_time_ts)
            # --------------------- 是否学习 --------------------- #
            # is_learn = True if file_name in train_data_file_name else False
            # --------------------- 查询病例信息(制式,医生诊断) --------------------- #
            case_results = self.query_exist_record(type='case', pathology=pathology)
            if case_results:
                if len(case_results) >= 2:
                    # 根据病理号, 查询所有的医生诊断标签, 并使用,号进行拼接
                    diagnosis_label_doctor_list = [i['diagnosis_label_doctor'] for i in case_results if
                                                   i['diagnosis_label_doctor'] is not None]
                    diagnosis_label_doctor_str = '+'.join(
                        diagnosis_label_doctor_list) if diagnosis_label_doctor_list else None

                    diagnosis_label_doctor = diagnosis_label_doctor_str
                    making_way = [i['making_way'] for i in case_results if i['making_way']][0]
                else:
                    diagnosis_label_doctor = case_results[0]['diagnosis_label_doctor']
                    making_way = case_results[0]['making_way']
            else:
                # 匹配不上,则为None
                diagnosis_label_doctor = None
                making_way = None
            # --------------------- 朱博士最新诊断标签 --------------------- #
            diagnosis_results = self.query_exist_record(type='diagnosis', pathology=pathology)
            if diagnosis_results:
                diagnosis_label_zhu = diagnosis_results[0]['his_diagnosis_label'].split(',')[0]
            else:
                diagnosis_label_zhu = None

            # 新增数据
            image = {
                'resolution': resolution,
                'file_name': new_file_name,
                'suffix': suffix_name,
                'pathology': pathology,
                'storage_path': new_storage_path,
                'scan_time': scan_time,
                'diagnosis_label_doctor': diagnosis_label_doctor,
                'waveplate_source': waveplate_source,
                'making_way': making_way,
                'diagnosis_label_zhu': diagnosis_label_zhu
            }

            # 发送post请求, 新增一条大图记录
            response = requests.post('http://%s/api/v1/images/' % self.host, json=image)
            if response.status_code != 201:
                logging.error('dms数据库新增数据失败：%s' % response.text)
                return

            # 修改回状态, 保持use_in_move_to为True
            self.use_in_move_to = True
            logging.info('dms数据库新增一条大图记录, 大图名为：%s' % event.name)

        logging.info('IN_MOVED_TO: 监控文件夹下新增文件: %s' % event.pathname)

    def process_IN_DELETE(self, event):
        """
        1.通过命令rm将监控文件夹中的文件'删除'
        2.手动'delete'监控文件夹中的文件
        """

        # 根据文件名和存储路径, 查询该大图在数据库中是否存在
        delete_file_name, _ = os.path.splitext(event.name)
        # 为了能和数据库中的路径进行匹配, 要去掉'/home/'
        delete_storage_path = event.path.replace('/home/', '')
        results = self.query_exist_record(type='image', old_file_name=delete_file_name,
                                          old_storage_path=delete_storage_path)

        # 如果不存在, 返回即可, 反正该条记录也是要删除, 不存在最好
        if not results:
            logging.error('dms数据库中不存在该条记录：%s' % event.pathname)
            return

        # 获取该大图的id值
        image_id = results[0]['id']
        # 删除dms数据库中该大图的记录
        response = requests.delete('http://%s/api/v1/images/%s/' % (self.host, image_id))
        if response.status_code != 204:
            logging.error('dms数据库删除数据失败：%s' % response.text)
            return

        logging.warning('IN_DELETE: 监控文件夹下删除文件: %s' % event.pathname)

    def process_IN_MOVED_FROM(self, event):
        """
        1.手动从监控文件夹中将文件移动到废纸娄
        2.手动从监控文件夹中将文件通过剪切方式移走
        3.手动/使用命令mv在监控文件夹中修改文件名（先'删除'再创建）
        """

        # 如果是移动文件夹, 则不需要在dms中记录, 直接结束
        if event.dir:
            logging.info('IN_MOVED_FROM: 文件夹名称修改前为：%s' % event.pathname)
            return

        # 原大图的文件名以及存储路径
        old_file_name, _ = os.path.splitext(event.name)
        # 为了能和数据库中的路径进行匹配, 要去掉'/home/'
        old_storage_path = event.path.replace('/home/', '')
        # 将文件修改前的名字保存到队列
        self.in_move_from_old_file_name.append(old_file_name)
        # 将文件修改前的名字保存到队列
        self.in_move_from_old_storage_path.append(old_storage_path)

        logging.warning('IN_MOVED_FROM: 监控文件夹下移走文件: %s' % event.pathname)


class FSmonitor(object):

    def __init__(self):
        # 所有大图的后缀类型
        self.suffix_type = {'.kfb', '.tiff', '.TMAP', '.tmap', '.mds'}
        # 监控的文件夹
        self.dir_type = {'20X', '40X'}
        # 监控路径
        self.path = '/home/data_samba/LCT_DATA/0TIFF'
        # self.path = '/home/data_samba/TMP/test_monitor'

    def suffix_filter(self, event):
        """监视dir中指定的后缀文件及目录"""

        # 判断后缀是否为{'.kfb', '.tiff', '.TMAP', '.tmap'}
        suffix_name = os.path.splitext(event.name)[1]
        # 判断文件夹是否为20X或40X
        dir_name = event.pathname.split(self.path)[1].split('/')[1]

        # return True to stop processing of event (to "stop chaining")
        # 1.如果监控的文件夹的名称不在{'20X', '40X'}, 则停止chaining
        if dir_name not in self.dir_type:
            return True
        # 2.满足条件1, 如果监控的文件后缀不在{'.kfb', '.tiff', '.TMAP'}, 则停止chaining
        elif suffix_name not in self.suffix_type:
            return True
        # 3.同时满足条件1, 2, 则return False
        else:
            return False

    def monitor(self):
        # 创建WatchManager对象
        wm = pyinotify.WatchManager()

        # 监控事件
        # 加上IN_MOVE_SELF监控事件, 可以对新建的文件夹, 同时修改其文件夹名称, 再将文件(a.txt)移入进去之后, 得到a.txt所在的正确路径
        mask = IN_CREATE | IN_MOVED_TO | IN_DELETE | IN_MOVED_FROM | IN_MOVE_SELF
        # 添加监控：指定需要监控的目录, 指定需要监控的事件
        wm.add_watch(self.path, mask, auto_add=True, rec=True)

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

    # 开启监控
    monitor_samba_0tiff = FSmonitor()

    logging.info('----------- start monitor：%s -----------' % monitor_samba_0tiff.path)

    monitor_samba_0tiff.monitor()

    logging.info('=========== stop monitor：%s ============\n\n\n' % monitor_samba_0tiff.path)
