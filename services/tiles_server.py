# -*- coding: utf8 -*-

import os, sys
import requests
import logging
from io import BytesIO
# from sanic import Sanic, response
# from sanic_cors import CORS
from japronto import Application
from Aslide.aslide import Aslide
from Aslide.deepzoom import ADeepZoomGenerator

# app = Sanic(__name__)
# # 跨域
# CORS(app)

tif_path_cache = {}
slide_cache = {}

HOST = '192.168.2.179'
TIF_PATH_PREX = '/run/user/1000/gvfs/smb-share:server=192.168.2.221,share='


# 配置日志/初始化变量
class ConfigLog(object):
    def __init__(self):
        # 日志输出的位置
        self.log_name = '/home/kyfq/MyPython/PycharmProjects/dms/DMS/DMS/logs/tiles_server.log'
        # 输出格式
        self.log_format = '%(levelname)s [%(asctime)s] %(message)s'

        # logging配置
        logging.basicConfig(
            level=logging.WARNING,
            format=self.log_format,
            filename=self.log_name,
        )


def get_path(image_id, request):
    try:
        if image_id in tif_path_cache:
            tif_path = tif_path_cache[image_id]
        else:
            tiff_url = 'http://%s/api/v1/images/?id=%s' % (HOST, image_id)
            response = requests.get(tiff_url)
            if response.status_code != 200:
                raise Exception('can not get resource', response.status_code, response.content)

            image_info = response.json()['results'][0]
            tif_path = TIF_PATH_PREX + os.path.join(image_info['storage_path'], image_info['file_name']) + image_info['suffix']
            tif_path_cache[image_id] = tif_path
        return tif_path
    except Exception as e:
        logging.error('获取路径出错：%s' % e)


def get_slide(image_id, img_path):
    """
    get tiles and cache
    :param img_path:
    :return:
    """
    img_name = os.path.basename(img_path)
    img = str(image_id) + '_' + img_name

    try:
        if img in slide_cache:
            slide = slide_cache[img]
        else:
            slide = Aslide(img_path)
            slide_cache[img] = slide
        return slide
    except Exception as e:
        logging.error('读取图片失败：%s' % e)


async def tiles_dzi(request):
    """
    get tiff information
    :param request:
    :param image_id: id of tiff image
    :return:
    """

    # 使用request.match_dict获取参数
    image_id = request.match_dict['image_id']
    image_id = int(image_id)
    try:
        slide = get_slide(image_id, get_path(image_id, request))
        zoomer = ADeepZoomGenerator(slide).get_dzi('jpeg')
        return request.Response(zoomer)
    except Exception as e:
        logging.error("Fail to get tiles_dzi：%s" % e)
        return request.Response(code=500, json={'err': str(e)})


async def label_image(request):
    """
    get tile image
    :param request:
    :param image_id: id of tiff image
    :param format: view format
    :return:
    """

    # 对前端参数：2_label.png进行提取
    image_name = request.match_dict['image_name']
    image_id, img_format = image_name.split('.')
    image_id = image_id.split('_')[0]
    try:
        slide = get_slide(int(image_id), get_path(int(image_id), request))

        bio = BytesIO()
        label_image = slide.label_image
        # 如果标签存在则保存,否则返回一个空字节
        if label_image:
            label_image.save(bio, 'png')
            image_bytes = bio.getvalue()
        else:
            image_bytes = b''

        headers = {}
        headers.setdefault(
            'Content-Disposition',
            'attachment; image_id="{}"'.format(os.path.basename(image_id))
        )

        return request.Response(code=200, headers=headers,
                                mime_type='image/png', body=image_bytes)
    except Exception as e:
        logging.error("Fail to get tiles_dzi：%s" % e)
        return request.Response(code=500, json={'err': str(e)})


# @app.route('/tiles/<image_id>_files/<z:int>/<x:int>_<y:int>.<format:[A-z]+>')
async def tiles_png(request):
    """
    get tile image
    :param request:
    :param image_id: id of tiff image
    :param x: coordinate-x
    :param y: coordinate-y
    :param format: view format
    :return:
    """

    image_id = request.match_dict['image_id']
    if not image_id:
        return request.Response(code=400, json={'err': "[image_id] is needed!"})

    try:
        image_id = int(image_id.replace("_files", ""))
        z = request.match_dict['z']

        x_y_format = request.match_dict['x_y_format']
        x_y, img_format = x_y_format.split('.')
        x, y = x_y.split("_")

        x, y, z = int(x), int(y), int(z)

        slide = get_slide(image_id, get_path(image_id, request))
        bio = BytesIO()
        tiles_image = ADeepZoomGenerator(slide).get_tile(z, (x, y))
        tiles_image.save(bio, 'png')
        image_bytes = bio.getvalue()

        headers = {}
        headers.setdefault(
            'Content-Disposition',
            'attachment; image_id="{}"'.format(image_id)
        )

        # sanic response
        # return response.HTTPResponse(status=200, headers=headers,
        #                              body_bytes=image_bytes, content_type='image/png')

        # japronto response
        return request.Response(code=200, headers=headers,
                                mime_type='image/png', body=image_bytes)
    except Exception as e:
        logging.error("Fail to get tiles_png：%s" % e)
        return request.Response(code=500, json={'err': str(e)})


app = Application()

app.router.add_route('/tiles/{image_id}/', tiles_dzi)

app.router.add_route('/tiles/label_image/{image_name}/', label_image)

# app.route('/tiles/<image_id>_files/<z:int>/<x:int>_<y:int>.<format:[A-z]+>')
app.router.add_route('/tiles/{image_id}/{z}/{x_y_format}/', tiles_png)


if __name__ == '__main__':

    # 开始日志
    ConfigLog()

    # 指定端口号
    port = sys.argv[1]
    try:
        port = int(port)
    except:
        raise Exception("PORT %s IS NOT ACCEPTED!" % port)

    # sanic配置：access_log=False 不记录成功的日志, error_log=True, 记录失败的日志
    # app.run(host="0.0.0.0", port=port, access_log=False, error_log=True)

    # japronto配置
    app.run(host="0.0.0.0", port=port, debug=True)
