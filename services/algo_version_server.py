# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: algo_version_server.py
# @time: 19-6-28 下午3:23


# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
# @author: condi
# @file: manage.py.py
# @time: 19-6-11 上午11:10

import sys
from flask_restful import Api
from flask_cors import CORS

from AlgoVersion import create_app, ConfigLog
import AlgoVersion.views as algo_views

# generate app
# app = create_app('development')
app = create_app('product')
CORS(app, supports_credentials=True)

# api
api = Api(app)
api.add_resource(algo_views.BaseInfoViews, '/api/v1/base_info')  # read/create/modify/delete with base info
api.add_resource(algo_views.BaseInfoDeleteViews, '/api/v1/base_info/delete')  # delete one or more base info
api.add_resource(algo_views.BaseInfoSearchViews, '/api/v1/base_info/search')  # search from base info
api.add_resource(algo_views.DataSectionViews, '/api/v1/data_section')  # read/create/modify with data section
api.add_resource(algo_views.ModelSectionViews, '/api/v1/model_section')  # read/create/modify with model section
api.add_resource(algo_views.HyperParamsViews, '/api/v1/hyper_params')  # read/create/modify with hyper params
api.add_resource(algo_views.AlgoPerformanceViews, '/api/v1/algo_performance')  # read/create/modify with algo pfm
api.add_resource(algo_views.AlgoWeaknessViews, '/api/v1/algo_weakness')  # read/create/modify with algo weakness


if __name__ == '__main__':

    # 开始日志
    ConfigLog()

    # app.run(host='0.0.0.0', port=5998)

    # 指定端口号
    port = sys.argv[1]
    try:
        port = int(port)
    except:
        raise Exception("PORT %s IS NOT ACCEPTED!" % port)

    app.run(host="0.0.0.0", port=port)
