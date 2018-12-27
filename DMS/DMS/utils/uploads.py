# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: uploads.py
# @time: 18-12-26 下午1:29

import time
import os


def save_upload_file(_file, save_folder='upload_files'):
    """
    :param _file: 上传的文件对象
    :param save_folder: 上传的文件保存的目录
    :return: 返回重命名后的文件路径
    """

    # ----------- 定义保存数据到新文件的路径 ----------- #
    main_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_file_name = os.path.join(main_path, save_folder, _file.name)

    # ----------- 读取上传文件的内容并保存到一个新的文件中 ----------- #
    with open(upload_file_name, 'wb') as f:
        for chunk in _file.chunks():
            f.write(chunk)

    # ----------- 重命名上传文件 ----------- #
    file_name_split = os.path.splitext(_file.name)
    file_name_add_date = file_name_split[0] + '_' + time.strftime('%Y_%m_%d_%H_%M_%S') + file_name_split[1]
    upload_file_rename = os.path.join(main_path, save_folder, file_name_add_date)
    os.rename(upload_file_name, upload_file_rename)

    return upload_file_rename
