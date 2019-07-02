# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: __init__.py.py
# @time: 19-6-28 下午3:12

import logging
from flask import Flask
from flask_pymongo import PyMongo

from .config import Config, project_config

# initial mongodb object
mongo_algo = PyMongo()


# log configure
class ConfigLog(object):
    def __init__(self):
        self.log_name = '/home/kyfq/MyPython/PycharmProjects/dms/DMS/DMS/logs/algo_version_server.log'
        self.log_format = '%(levelname)s [%(asctime)s] %(message)s'

        logging.basicConfig(
            level=logging.WARNING,
            format=self.log_format,
            filename=self.log_name,
        )


# factory mode
def create_app(config_name):

    app = Flask(__name__)
    app.config.from_object(project_config[config_name])
    mongo_algo.init_app(app)

    return app
