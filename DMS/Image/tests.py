from django.test import TestCase, Client
from Image.models import Image
import time, json


class ImageTestCase(TestCase):
    """
    大图单元测试
    """

    def setUp(self):
        self.client = Client()

        # 手动添加测试数据
        self.image_id = 1
        Image.objects.create(
            id=self.image_id,
            pathology='T1807066',
            file_name='T1807066',
            resolution='20X',
            storage_path='/run/user/1000/gvfs/smb-share:server=192.168.2.221,share=data_samba/DATA/0TIFF/20X/QZ'
        )

        print('Image接口测试 =========>')

    def test_image_get(self):
        response = self.client.get("/api/v1/images/")
        self.assertEqual(response.status_code, 200)
        print('1.get方法查询列表数据, 返回的状态码为：%s' % response.status_code)

        response = self.client.get('/api/v1/images/{}/'.format(self.image_id))
        self.assertEqual(response.status_code, 200)
        print('2.get方法查询一条数据, 返回的状态码为：%s' % response.status_code)

        response = self.client.get('/api/v1/images/statistics/')
        self.assertEqual(response.status_code, 200)
        print('3.get方法查询首页统计信息, 返回的状态码为：%s' % response.status_code)

        response = self.client.get('/api/v1/images/duplicates/')
        self.assertEqual(response.status_code, 200)
        print('4.get方法查找大图中出现重复的(病理号,倍数)及重复的次数, 返回的状态码为：%s \n' % response.status_code)

    def test_image_post(self):
        # 携带参数
        params = {
            'update_type': 'db'
        }
        start_time = time.time()
        response = self.client.post('/api/v1/images/updates/', params)
        self.assertEqual(response.status_code, 201)
        end_time = time.time()
        print('1.post方法更新数据库, 返回的状态码为：%s, 一共消耗：%s秒' % (response.status_code, int(end_time-start_time)))
