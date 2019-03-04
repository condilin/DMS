# -*- coding: utf8 -*-

import os, sys
import requests
import logging
from io import BytesIO
from sanic import Sanic, response
from sanic_cors import CORS
from sanic.response import text, json
from Aslide.aslide import Aslide
from Aslide.deepzoom import ADeepZoomGenerator

app = Sanic(__name__)
# 跨域
CORS(app)

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
            tif_path_cache[image_info['file_name']] = tif_path
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
    img = image_id + '_' + img_name

    try:
        if img in slide_cache:
            slide = slide_cache[img]
        else:
            slide = Aslide(img_path)
            slide_cache[img] = slide

        return slide
    except Exception as e:
        logging.error('读取图片失败：%s' % e)


@app.route('/tiles/<image_id>')
async def tiles_dzi(request, image_id):
    """
    get tiff information
    :param request:
    :param image_id: id of tiff image
    :return:
    """

    # img_path = request.args.get('img_path', None)
    # if not img_path:
    #     return text('请求参数错误！', status=400)
    #
    # slide = get_slide(img_path)

    slide = get_slide(image_id, get_path(image_id, request))
    try:
        zoomer = ADeepZoomGenerator(slide).get_dzi('jpeg')
        return response.html(zoomer)
    except Exception as e:
        logging.error(e)
        return response.html(str(e))


@app.route('/tiles/label_image/<image_id>_label.<format:[A-z]+>')
async def label_image(request, image_id, format):
    """
    get tile image
    :param request:
    :param image_id: id of tiff image
    :param format: view format
    :return:
    """

    slide = get_slide(image_id, get_path(image_id, request))

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

    return response.HTTPResponse(status=200, headers=headers,
                                 body_bytes=image_bytes, content_type='image/png')


@app.route('/tiles/<image_id>_files/<z:int>/<x:int>_<y:int>.<format:[A-z]+>')
async def tiles_png(request, image_id, z, x, y, format):
    """
    get tile image
    :param request:
    :param image_id: id of tiff image
    :param x: coordinate-x
    :param y: coordinate-y
    :param format: view format
    :return:
    """

    slide = get_slide(image_id, get_path(image_id, request))

    x = int(x)
    y = int(y)
    z = int(z)

    bio = BytesIO()
    tiles_image = ADeepZoomGenerator(slide).get_tile(z, (x, y))
    tiles_image.save(bio, 'png')
    image_bytes = bio.getvalue()

    headers = {}
    headers.setdefault(
        'Content-Disposition',
        'attachment; image_id="{}"'.format(os.path.basename(image_id))
    )

    return response.HTTPResponse(status=200, headers=headers,
                                 body_bytes=image_bytes, content_type='image/png')


@app.route("/tiles/<image_id>/<x:int>_<y:int>_<w:int>_<h:int>")
async def cell_image_request(request, image_id, x, y, w, h):
    """
    get cell image
    :param request:
    :param image_id: id of tiff image
    :param x: coordinate-x
    :param y: coordinate-y
    :param w: image width
    :param h: image height
    :return:
    """

    slide = get_slide(image_id, get_path(image_id, request))

    tile_image = slide.read_region((x, y), 0, (w, h))

    bio = BytesIO()

    tile_image.save(bio, 'png')
    image_bytes = bio.getvalue()

    headers = {}
    headers.setdefault(
        'Content-Disposition',
        'attachment; image_id="{}"'.format(os.path.basename(image_id))
    )

    return response.HTTPResponse(status=200, headers=headers,
                                 body_bytes=image_bytes, content_type='image/png')


if __name__ == '__main__':

    # 开始日志
    ConfigLog()

    # 指定端口号
    port = sys.argv[1]
    try:
        port = int(port)
    except:
        raise Exception("PORT %s IS NOT ACCEPTED!" % port)

    # access_log=False 不记录成功的日志, error_log=True, 记录失败的日志
    app.run(host="0.0.0.0", port=port, access_log=False, error_log=True)
