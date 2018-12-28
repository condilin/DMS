from django.contrib.auth.models import User, Permission
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
            "waveplate_source": "南方医院"
        }

        # 发送post请求, 增加一条数据, 并获取id值
        response = self.client.post('/api/v1/images/', json.dumps(self.image), content_type='application/json')
        if response.status_code == 201:
            self.image_id = response.json()['id']
        else:
            print(response.json())

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
        print('3.get方法查询首页统计信息, 返回的状态码为：%s\n' % response.status_code)

    def test_image_post(self):
        # 插入数据
        insert_data1 = {
            "file_name": "TC16666_2018_05_09",
        }

        response = self.client.post('/api/v1/images/', json.dumps(insert_data1), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        print('1.post方法增加一条数据, 返回的状态码为：%s' % response.status_code)

        # 断言, 增加一条数据, 如果没有添加病理号, 则自动从文件名中获取
        self.assertEqual(response.json()['pathology'], 'TC16666')
        print('2.post方法添加文件名为TC16666_2018_05_09, 没有添加病理号, 最终请求得到的结果为：\n 病理号为: %s, 文件名为：%s \n' % (
            response.json()['pathology'], response.json()['file_name']))

    def test_image_patch(self):
        # 修改数据
        update_data1 = {
            'file_name': 'TC6666_2018_05_09'
        }
        update_data2 = {
            'pathology': 'ABCDE'
        }

        response = self.client.patch('/api/v1/images/{}/'.format(self.image_id),
                                     json.dumps(update_data1), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        print('1.patch方法修改一条数据, 返回的状态码为：%s ' % response.status_code)

        # 断言：当修改文件名时, 病理号是否会发生改变
        self.assertEqual(response.json()['pathology'], 'TC6666')
        print('2.patch方法修改文件名为TC6666_2018_05_09, 最终修改后得到的结果为：\n 文件名为: %s, 病理号为：%s' % (
            response.json()['file_name'], response.json()['pathology']))

        # 断言：当修改病理号时, 病理号是否会发生改变
        response = self.client.patch('/api/v1/images/{}/'.format(self.image_id),
                                     json.dumps(update_data2), content_type='application/json')
        self.assertEqual(response.json()['pathology'], 'ABCDE')
        print('3.patch方法修改病理号为ABCDE, 最终修改后得到的病理号为：\n %s, 文件名为: %s \n' % (
            response.json()['pathology'], response.json()['file_name']))

    def test_image_delete(self):
        response = self.client.delete('/api/v1/images/{}/'.format(self.image_id))
        self.assertEqual(response.status_code, 204)
        print('1.delete方法删除一条数据, 返回的状态码为：%s\n' % response.status_code)
