from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from Check.models import Check
from Check.serializers import CheckSerializer


class SCCheckView(ListCreateAPIView):
    """
    get: 查询审核数据记录列表
    post: 创建一条审核数据记录
    """

    # 指定查询集, 获取没有逻辑删除的数据
    queryset = Check.objects.filter(is_delete=False)

    # 指定序列化器
    serializer_class = CheckSerializer

    # OrderingFilter：指定排序的过滤器,可以按任意字段排序,通过在路由中通过ordering参数控制,如：?ordering=id
    # DjangoFilterBackend对应filter_fields属性，做相等查询
    # SearchFilter对应search_fields，对应模糊查询
    filter_backends = [OrderingFilter, DjangoFilterBackend, SearchFilter]
    # 默认指定按哪个字段进行排序
    ordering_fields = ('check_version_number', )
    # 指定可以被搜索字段, 如在路由中通过?id=2查询id为2的记录
    filter_fields = ('id', 'check_version_number')


class SUDCheckView(APIView):
    """
    get: 查询一条审核数据记录
    patch: 更新一条审核数据记录
    """

    def get(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            diagnose = Check.objects.get(id=pk, is_delete=False)
        except Check.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})

        # 序列化返回
        serializer = CheckSerializer(diagnose)
        return Response(serializer.data)

    def patch(self, request, pk):
        # 根据id, 查询数据库对象
        try:
            diagnose = Check.objects.get(id=pk, is_delete=False)
        except Check.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND, data={'msg': '数据不存在！'})

        # 获取参数, 校验参数, 保存结果
        serializer = CheckSerializer(diagnose, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
