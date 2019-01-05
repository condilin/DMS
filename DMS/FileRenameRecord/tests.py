from django.test import TestCase, Client
import json
from FileRenameRecord.models import FileRenameRecord


class DiagnosisTestCase(TestCase):
    """
    文件更名记录单元测试
    """

    def setUp(self):
        self.client = Client()

        # 添加测试数据
        self.diagnose = {
            "pathology": "GZY126047",
            "current_file_name": "GZY126047",
        }

        # 发送post请求, 增加一条数据, 并获取id值
        response = self.client.post('/api/v1/renames/', json.dumps(self.diagnose), content_type='application/json')
        if response.status_code == 201:
            self.diagnose_id = response.json()['id']
        else:
            print(response.json())

        print('FileRenameRecord接口测试 =========>')

    def test_diagnose_get(self):
        response = self.client.get("/api/v1/renames/")
        self.assertEqual(response.status_code, 200)
        print('1.get方法查询列表数据, 返回的状态码为：%s' % response.status_code)

        response = self.client.get('/api/v1/renames/{}/'.format(self.diagnose_id))
        self.assertEqual(response.status_code, 200)
        print('2.get方法查询一条数据, 返回的状态码为：%s' % response.status_code)

        response = self.client.get('/api/v1/renames/duplicates/')
        self.assertEqual(response.status_code, 200)
        print('3.get方法查找更名记录中出现重复的文件名及重复的次数, 返回的状态码为：%s \n' % response.status_code)

    def test_diagnose_post(self):
        # 插入数据
        insert_data1 = {
            "pathology": "ZA0016105",
        }

        response = self.client.post('/api/v1/renames/', json.dumps(insert_data1), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        print('1.post方法增加一条数据, 返回的状态码为：%s' % response.status_code)

    def test_diagnose_patch(self):
        update_data1 = {
            "current_file_name": "ZA0016106",
        }

        response = self.client.patch('/api/v1/renames/{}/'.format(self.diagnose_id),
                                     json.dumps(update_data1), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        print('1.patch方法修改一条数据, 返回的状态码为：%s' % response.status_code)

    def test_case_delete(self):
        response = self.client.delete('/api/v1/renames/{}/'.format(self.diagnose_id))
        self.assertEqual(response.status_code, 204)
        print('1.delete方法删除一条数据, 返回的状态码为：%s\n' % response.status_code)
