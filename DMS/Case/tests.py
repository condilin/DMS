from django.test import TestCase, Client
import json


class CaseTestCase(TestCase):
    """
    病例单元测试
    """

    def setUp(self):
        self.client = Client()

        # 添加测试数据
        self.case = {
            "pathology": "34273278",
            "diagnosis_label_doctor": "HSIL",
            "waveplate_source": "华银"
        }

        # 发送post请求, 增加一条数据, 并获取id值
        response = self.client.post('/api/v1/cases/', json.dumps(self.case), content_type='application/json')
        if response.status_code == 201:
            self.case_id = response.json()['id']
        else:
            print(response.json())

        print('Case接口测试 =========>')

    def test_case_get(self):
        response = self.client.get("/api/v1/cases/")
        self.assertEqual(response.status_code, 200)
        print('1.get方法查询列表数据, 返回的状态码为：%s' % response.status_code)

        response = self.client.get('/api/v1/cases/{}/'.format(self.case_id))
        self.assertEqual(response.status_code, 200)
        print('2.get方法查询一条数据, 返回的状态码为：%s' % response.status_code)

        response = self.client.get('/api/v1/cases/duplicates/')
        self.assertEqual(response.status_code, 200)
        print('3.get方法查找病例中出现重复的病理号及重复的次数, 返回的状态码为：%s \n' % response.status_code)

    def test_case_post(self):
        # 插入数据
        insert_data1 = {
            "pathology": "ZA0016105",
        }

        response = self.client.post('/api/v1/cases/', json.dumps(insert_data1), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        print('1.post方法增加一条数据, 返回的状态码为：%s' % response.status_code)

    def test_case_delete(self):
        response = self.client.delete('/api/v1/cases/{}/'.format(self.case_id))
        self.assertEqual(response.status_code, 204)
        print('1.delete方法删除一条数据, 返回的状态码为：%s\n' % response.status_code)
