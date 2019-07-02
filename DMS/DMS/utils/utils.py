# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: utils.py
# @time: 19-7-2 上午11:09


from threading import Thread


def async_call(func):

    def wrapper(*args, **kwargs):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
    return wrapper

