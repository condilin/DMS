from django.test import TestCase, Client
import json
from Image.models import Image


class ImageTestCase(TestCase):
    """
    大图单元测试
    """

    def setUp(self):
        self.client = Client()

        # 添加测试数据
        self.image = {
            "file_name": "TC10001_2018_05_09",
            "resolution": "20x",
            "waveplate_source": "huayin"
        }

        # 发送post请求, 增加一条数据, 并获取id值
        response = self.client.post('/api/v1/images/', json.dumps(self.image), content_type='application/json')
        if response.status_code == 201:
            self.image_id = response.json()['id']
        else:
            print(response.json())

    def test_image_get(self):
        response = self.client.get("/api/v1/images/", )
        self.assertEqual(response.status_code, 200, (response.json()))

        response = self.client.get('/api/v1/images/{}/'.format(self.image_id), )
        self.assertEqual(response.status_code, 200, (response.json()))

    def test_image_post(self):
        response = self.client.post('/api/v1/images/', json.dumps(self.image), content_type='application/json')
        self.assertEqual(response.status_code, 201, (response.json()))

    def test_image_patch(self):
        response = self.client.patch('/api/v1/images/{}/'.format(self.image_id),
                                     json.dumps({'file_name': 'TC6666_2018_05_09'}), content_type='application/json')
        self.assertEqual(response.status_code, 200, (response.json()))
        # 断言：当修改文件名时, 病理号是否会发生改变
        self.assertEqual(response.json()['pathology'], 'TC6666', (response.json()))

    def test_image_delete(self):
        response = self.client.delete('/api/v1/images/{}/'.format(self.image_id), )
        self.assertEqual(response.status_code, 204, response.content)
