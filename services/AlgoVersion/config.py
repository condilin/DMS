# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: config.py
# @time: 19-6-11 上午11:58


class Config:

    DEBUG = None
    SECRET_KEY = 'JfqhApfTNHFJbeRnxNtkC330B4Yp4Vyo1d74lKh19mX6NlqbgsVvrw=='

    # Mongodb uri
    MONGO_HOST = 'localhost'
    MONGO_PORT = '27017'
    MONGO_DBNAME = 'algorithm_version'
    MONGO_URI = 'mongodb://{}:{}/{}'.format(MONGO_HOST, MONGO_PORT, MONGO_DBNAME)


# config of development
class DevelopConfig(Config):
    DEBUG = True


# config of production
class ProductConfig(Config):
    DEBUG = False


# mapping the config
project_config = {
    'development': DevelopConfig,
    'product': ProductConfig
}
