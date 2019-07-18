# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: views.py
# @time: 19-6-15 下午6:54

import bson
import time
import logging
from flask import request
from flask_pymongo import DESCENDING

from flask_restful import Resource
from .validation import BaseInfoPostForm, BaseInfoPaginateForm, DataSectionPostForm, \
    ModelSectionPostForm, HyperParamsPostForm, AlgoPerformancePostForm, AlgoWeaknessPostForm
from AlgoVersion import mongo_algo


class BaseInfoViews(Resource):

    def get(self):
        """
        base info list to display
        :return:
        """

        # verification
        args_form = BaseInfoPaginateForm(request.args)
        if not args_form.validate():
            return {'msg': args_form.errors}, 400

        # through verification and then get params
        limit_params = int(request.args['limit'])
        offset_params = int(request.args['offset'])

        base_info_list = mongo_algo.db.algo_info.find({}).limit(
            limit_params).skip(offset_params).sort('create_time', DESCENDING)
        results = []
        for record in base_info_list:
            record['_id'] = str(record['_id'])
            results.append(record)

        return {'results': results}, 200

    def post(self):
        """
        add an base info record
        :return:
        """

        # verification
        post_form = BaseInfoPostForm(request.form)
        if not post_form.validate():
            return {'msg': post_form.errors}, 400

        # get register params
        form_data = request.form.to_dict()

        # save to mongodb
        form_data = {k: v for k, v in form_data.items() if k in post_form.save_column}
        # can use datetime module to transform the type of string to type of datetime, so can calculate interval
        form_data.update({'type': 'base_info'})
        algo_info_id = mongo_algo.db.algo_info.insert({
            'base_info': form_data,
            'create_time': time.strftime("%Y-%m-%d %H:%M:%S"),
            'update_time': time.strftime("%Y-%m-%d %H:%M:%S")
        })

        # select and return except the pwd
        algo_info_one = mongo_algo.db.algo_info.find_one({'_id': algo_info_id})
        algo_info_one['_id'] = str(algo_info_one['_id'])

        return {'results': algo_info_one}, 201

    def put(self):
        """
        update algo info record
        :return:
        """

        # verification
        _id = request.args.get('id', None)
        if not _id:
            return {'msg': 'params error !'}, 400

        # update base info, it will return a modified_count property without throwing exception,
        # the property of modified_count will return greater than 0 on success or equal 0 on faild
        try:
            mongo_algo.db.algo_info.update_one(
                {'_id': bson.ObjectId(_id)},
                {'$set': {
                    'base_info': request.get_json(),
                    'update_time': time.strftime("%Y-%m-%d %H:%M:%S")
                }},
                # to do update if exist, else insert
                upsert=True
            )
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        # select the record which is modified
        base_info_one = mongo_algo.db.algo_info.find_one({'_id': bson.ObjectId(_id)}, {'base_info': 1})
        base_info_one['_id'] = str(base_info_one['_id'])

        return {'results': base_info_one}, 200

    def delete(self):
        """
        delete base info
        :return:
        """

        # verification
        _id = request.args.get('id', None)
        if not _id:
            return {'msg': 'params error !'}, 400

        # delete the algo info, it will return a deleted_count property without throwing exception,
        # the property of deleted_count will retun greater than 0 on success or equal 0 on faild
        try:
            result = mongo_algo.db.algo_info.delete_one({'_id': bson.ObjectId(_id)})
            if result.deleted_count == 0:
                return {'msg': 'id is not exist !'}, 400
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        return {'msg': 'successful to detele the record !'}, 200


class BaseInfoDeleteViews(Resource):

    def post(self):
        """
        delete algo info record
        :return:
        """

        # verify args params
        id_dict = request.form.to_dict()
        id_list = list(id_dict.values())
        if not id_list:
            return {'msg': 'params error !'}, 400

        # delete userinfo, it will return a deleted_count property without throwing exception,
        # the property of deleted_count will retun greater than 0 on success or equal 0 on faild, but if id not wrong,
        # if will throw an exception, so need to do two ways verify!
        try:
            for _id in id_list:
                mongo_algo.db.algo_info.delete_one({'_id': bson.ObjectId(_id)})
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        return {'msg': 'successful to detele !'}, 200


class BaseInfoSearchViews(Resource):

    def get(self):

        # verification
        search_text = request.args.get('text', None)
        if not search_text:
            return {'msg': 'params error !'}, 400

        # search
        search_list = mongo_algo.db.algo_info.find({'base_info.version_name': {'$regex': search_text}})
        results = []
        for record in search_list:
            record['_id'] = str(record['_id'])
            results.append(record)
        return {'results': results}, 200


class DataSectionViews(Resource):

    def get(self):
        """
        get one data section through id
        :return:
        """

        # verification
        _id = request.args.get('id', None)
        if not _id:
            return {'msg': 'params error !'}, 400

        # get data section info through id
        try:
            result = mongo_algo.db.algo_info.find_one({'_id': bson.ObjectId(_id)}, {'data_section': 1})
            if not result:
                return {'msg': 'id is not exist !'}, 200
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        return {'results': result}, 200

    def post(self):
        """
        add an data section record
        :return:
        """

        # verification
        post_form = DataSectionPostForm(request.form)
        if not post_form.validate():
            return {'msg': post_form.errors}, 400

        # get register params
        form_data = request.form.to_dict()
        _id = form_data.pop('id')

        # save to mongodb
        form_data = {k: v for k, v in form_data.items() if k in post_form.save_column}
        try:
            mongo_algo.db.algo_info.update_one(
                {'_id': bson.ObjectId(_id)},
                {'$set': {
                    'data_section': form_data,
                    'update_time': time.strftime("%Y-%m-%d %H:%M:%S")
                }}
            )
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        # select and return
        data_section_one = mongo_algo.db.algo_info.find_one({'_id': bson.ObjectId(_id)}, {'data_section': 1})
        data_section_one['_id'] = str(data_section_one['_id'])

        return {'results': data_section_one}, 201

    def put(self):
        """
        update data section record
        :return:
        """

        # verification
        _id = request.args.get('id', None)
        if not _id:
            return {'msg': 'params error !'}, 400

        # save to mongodb
        try:
            mongo_algo.db.algo_info.update_one(
                {'_id': bson.ObjectId(_id)},
                {'$set': {
                    'data_section': request.get_json(),
                    'update_time': time.strftime("%Y-%m-%d %H:%M:%S")
                }},
                # to do update if exist, else insert
                upsert=True
            )
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        # select and return
        data_section_one = mongo_algo.db.algo_info.find_one({'_id': bson.ObjectId(_id)}, {'data_section': 1})
        data_section_one['_id'] = str(data_section_one['_id'])

        return {'results': data_section_one}, 200


class ModelSectionViews(Resource):

    def get(self):
        """
        get one model section through id
        :return:
        """

        # verification
        _id = request.args.get('id', None)
        if not _id:
            return {'msg': 'params error !'}, 400

        # get data section info through id
        try:
            result = mongo_algo.db.algo_info.find_one({'_id': bson.ObjectId(_id)}, {'model_section': 1})
            if not result:
                return {'msg': 'id is not exist !'}, 200
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        return {'results': result}, 200

    def post(self):
        """
        add an model section record
        :return:
        """

        # verification
        post_form = ModelSectionPostForm(request.form)
        if not post_form.validate():
            return {'msg': post_form.errors}, 400

        # get register params
        form_data = request.form.to_dict()
        _id = form_data.pop('id')

        # save to mongodb
        form_data = {k: v for k, v in form_data.items() if k in post_form.save_column}
        try:
            mongo_algo.db.algo_info.update_one(
                {'_id': bson.ObjectId(_id)},
                {'$set': {
                    'model_section': form_data,
                    'update_time': time.strftime("%Y-%m-%d %H:%M:%S")
                }}
            )
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        # select and return
        model_section_one = mongo_algo.db.algo_info.find_one({'_id': bson.ObjectId(_id)}, {'model_section': 1})
        model_section_one['_id'] = str(model_section_one['_id'])

        return {'results': model_section_one}, 201

    def put(self):
        """
        update model section record
        :return:
        """

        # verification
        _id = request.args.get('id', None)
        if not _id:
            return {'msg': 'params error !'}, 400

        # save to mongodb
        try:
            mongo_algo.db.algo_info.update_one(
                {'_id': bson.ObjectId(_id)},
                {'$set': {
                    'model_section': request.get_json(),
                    'update_time': time.strftime("%Y-%m-%d %H:%M:%S")
                }},
                # to do update if exist, else insert
                upsert=True
            )
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        # select and return
        model_section_one = mongo_algo.db.algo_info.find_one({'_id': bson.ObjectId(_id)}, {'model_section': 1})
        model_section_one['_id'] = str(model_section_one['_id'])

        return {'results': model_section_one}, 200


class HyperParamsViews(Resource):

    def get(self):
        """
        get one hyper params through id
        :return:
        """

        # verification
        _id = request.args.get('id', None)
        if not _id:
            return {'msg': 'params error !'}, 400

        # get hyper params info through id
        try:
            result = mongo_algo.db.algo_info.find_one({'_id': bson.ObjectId(_id)}, {'hyper_params': 1})
            if not result:
                return {'msg': 'id is not exist !'}, 200
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        return {'results': result}, 200

    def post(self):
        """
        add an hyper params record
        :return:
        """

        # verification
        post_form = HyperParamsPostForm(request.form)
        if not post_form.validate():
            return {'msg': post_form.errors}, 400

        # get register params
        form_data = request.form.to_dict()
        _id = form_data.pop('id')

        # save to mongodb
        form_data = {k: v for k, v in form_data.items() if k in post_form.save_column}
        try:
            mongo_algo.db.algo_info.update_one(
                {'_id': bson.ObjectId(_id)},
                {'$set': {
                    'hyper_params': form_data,
                    'update_time': time.strftime("%Y-%m-%d %H:%M:%S")
                }}
            )
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        # select and return
        hyper_params_one = mongo_algo.db.algo_info.find_one({'_id': bson.ObjectId(_id)}, {'hyper_params': 1})
        hyper_params_one['_id'] = str(hyper_params_one['_id'])

        return {'results': hyper_params_one}, 201

    def put(self):
        """
        update hyper params record
        :return:
        """

        # verification
        _id = request.args.get('id', None)
        if not _id:
            return {'msg': 'params error !'}, 400

        # save to mongodb
        try:
            mongo_algo.db.algo_info.update_one(
                {'_id': bson.ObjectId(_id)},
                {'$set': {
                    'hyper_params': request.get_json(),
                    'update_time': time.strftime("%Y-%m-%d %H:%M:%S")
                }},
                # to do update if exist, else insert
                upsert=True
            )
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        # select and return
        hyper_params_one = mongo_algo.db.algo_info.find_one({'_id': bson.ObjectId(_id)}, {'hyper_params': 1})
        hyper_params_one['_id'] = str(hyper_params_one['_id'])

        return {'results': hyper_params_one}, 200


class AlgoPerformanceViews(Resource):

    def get(self):
        """
        get one algo performance through id
        :return:
        """

        # verification
        _id = request.args.get('id', None)
        if not _id:
            return {'msg': 'params error !'}, 400

        # get algo performance info through id
        try:
            result = mongo_algo.db.algo_info.find_one({'_id': bson.ObjectId(_id)}, {'algo_performance': 1})
            if not result:
                return {'msg': 'id is not exist !'}, 200
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        return {'results': result}, 200

    def post(self):
        """
        add an algo performance record
        :return:
        """

        # verification
        post_form = AlgoPerformancePostForm(request.form)
        if not post_form.validate():
            return {'msg': post_form.errors}, 400

        # get register params
        form_data = request.form.to_dict()
        _id = form_data.pop('id')

        # save to mongodb
        form_data = {k: v for k, v in form_data.items() if k in post_form.save_column}
        try:
            mongo_algo.db.algo_info.update_one(
                {'_id': bson.ObjectId(_id)},
                {'$set': {
                    'algo_performance': form_data,
                    'update_time': time.strftime("%Y-%m-%d %H:%M:%S")
                }}
            )
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        # select and return
        algo_performance_one = mongo_algo.db.algo_info.find_one(
            {'_id': bson.ObjectId(_id)}, {'algo_performance': 1}
        )
        algo_performance_one['_id'] = str(algo_performance_one['_id'])

        return {'results': algo_performance_one}, 201

    def put(self):
        """
        update algo performance record
        :return:
        """

        # verification
        _id = request.args.get('id', None)
        if not _id:
            return {'msg': 'params error !'}, 400

        # save to mongodb
        try:
            mongo_algo.db.algo_info.update_one(
                {'_id': bson.ObjectId(_id)},
                {'$set': {
                    'algo_performance': request.get_json(),
                    'update_time': time.strftime("%Y-%m-%d %H:%M:%S")
                }},
                # to do update if exist, else insert
                upsert=True
            )
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        # select and return
        algo_performance_one = mongo_algo.db.algo_info.find_one(
            {'_id': bson.ObjectId(_id)}, {'algo_performance': 1}
        )
        algo_performance_one['_id'] = str(algo_performance_one['_id'])

        return {'results': algo_performance_one}, 200


class AlgoWeaknessViews(Resource):

    def get(self):
        """
        get one algo weakness through id
        :return:
        """

        # verification
        _id = request.args.get('id', None)
        if not _id:
            return {'msg': 'params error !'}, 400

        # get algo weakness info through id
        try:
            result = mongo_algo.db.algo_info.find_one({'_id': bson.ObjectId(_id)}, {'algo_weakness': 1})
            if not result:
                return {'msg': 'id is not exist !'}, 200
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        return {'results': result}, 200

    def post(self):
        """
        add an algo weakness record
        :return:
        """

        # verification
        post_form = AlgoWeaknessPostForm(request.form)
        if not post_form.validate():
            return {'msg': post_form.errors}, 400

        # get register params
        form_data = request.form.to_dict()
        _id = form_data.pop('id')

        # save to mongodb
        form_data = {k: v for k, v in form_data.items() if k in post_form.save_column}
        try:
            mongo_algo.db.algo_info.update_one(
                {'_id': bson.ObjectId(_id)},
                {'$set': {
                    'algo_weakness': form_data,
                    'update_time': time.strftime("%Y-%m-%d %H:%M:%S")
                }}
            )
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        # select and return
        algo_weakness_one = mongo_algo.db.algo_info.find_one(
            {'_id': bson.ObjectId(_id)}, {'algo_weakness': 1}
        )
        algo_weakness_one['_id'] = str(algo_weakness_one['_id'])

        return {'results': algo_weakness_one}, 201

    def put(self):
        """
        update algo weakness record
        :return:
        """

        # verification
        _id = request.args.get('id', None)
        if not _id:
            return {'msg': 'params error !'}, 400

        # save to mongodb
        try:
            mongo_algo.db.algo_info.update_one(
                {'_id': bson.ObjectId(_id)},
                {'$set': {
                    'algo_weakness': request.get_json(),
                    'update_time': time.strftime("%Y-%m-%d %H:%M:%S")
                }},
                # to do update if exist, else insert
                upsert=True
            )
        except Exception as e:
            logging.error(e, exc_info=True)
            return {'msg': 'id is not exist !'}, 400

        # select and return
        algo_weakness_one = mongo_algo.db.algo_info.find_one(
            {'_id': bson.ObjectId(_id)}, {'algo_weakness': 1}
        )
        algo_weakness_one['_id'] = str(algo_weakness_one['_id'])

        return {'results': algo_weakness_one}, 200
