from django.http import HttpResponse, JsonResponse
# Create your views here.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .auth import AdminOnlyAuthentication, JWTAuthentication


class BaseView(APIView):
    authentication_classes = [JWTAuthentication]


class LoginView(APIView):
    authentication_classes = [AdminOnlyAuthentication]

    def post(self, request):
        user = request.user
        return Response({
            "code": 0,
            "username": user.username,
            "id": user.id,
            "token": request.auth
        })

    def handle_exception(self, exc):
        detail = exc.detail
        code = detail.get('code', None)
        msg = detail.get('msg', None)
        return JsonResponse({'code': code, 'msg': msg}, status=400)


from apps.users.models import User
from datetime import date, timedelta

today = date.today()


# 用户总数
class TotalUserView(BaseView):
    def get(self, request):
        user_coutn = User.objects.all().count()
        return Response({'code': 1, 'count': user_coutn, 'date': today})


# 月新增
class MonthAddView(BaseView):

    def get(self, request):
        today = date.today()
        # 获取一个月前日期
        start_date = today - timedelta(days=30)
        # 创建空列表保存每天的用户量
        date_list = []

        for i in range(30):
            # 循环遍历获取当天日期
            index_date = start_date + timedelta(days=i)
            # 指定下一天日期
            cur_date = start_date + timedelta(days=i + 1)

            # 查询条件是大于当前日期index_date，小于明天日期的用户cur_date，得到当天用户量
            count = User.objects.filter(date_joined__gte=index_date, date_joined__lt=cur_date).count()

            date_list.append({
                'count': count,
                'date': index_date
            })
        return Response(date_list)


# 日活统计
class DailyActiveView(BaseView):
    def get(self, request):
        active_users_today = User.objects.filter(last_login__gte=today).count()
        return Response({'code': 1, 'count': active_users_today, 'date': today})


# 日下单统计
class DailyOrderActiveView(BaseView):
    def get(self, request):
        order_count = User.objects.filter(orderinfo__create_time__gte=today).count()  # 关联查询 模型名__字段名
        return Response({'code': 1, 'count': order_count, 'date': today})


# 日增用户
class DailyAddView(BaseView):
    def get(self, request):
        user_coutn = User.objects.filter(date_joined__gte=today).count()
        return Response({'code': 1, 'count': user_coutn, 'date': today})


from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10  # 设置每页显示的项数
    page_query_param = 'page'  # 页数查询参数
    page_size_query_param = 'pagesize'  # 每页最多数参数
    max_page_size = 15  # 每页最大数

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'lists': data,
            'page': self.page.number,  # 第几页
            'pages': self.page.paginator.num_pages,  # 总页数
            'pagesize': self.page.paginator.per_page,  # 页容量
        })


from rest_framework.generics import ListAPIView, CreateAPIView
from .seriali import UserlistSerializer


# 查询用户列表
class UserListView(ListAPIView, CreateAPIView, BaseView):
    # queryset = User.objects.all()  # 重写了get_queryset可以不指定queryset
    serializer_class = UserlistSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        keyword = self.request.query_params.get("keyword", None)
        if keyword:
            return User.objects.filter(username__contains=keyword)
        return User.objects.all()


from rest_framework.viewsets import ModelViewSet
from apps.goods.models import SKUImage, SKU
from .seriali import SkuImgSerializer, SkuListSerializer

import uuid
import os
from rest_framework.permissions import DjangoModelPermissions
class SkuImgView(ModelViewSet, BaseView):

    permission_classes = [DjangoModelPermissions]

    queryset = SKUImage.objects.all()
    serializer_class = SkuImgSerializer
    pagination_class = CustomPageNumberPagination

    def create(self, request, *args, **kwargs):
        image = request.FILES.get('image')  # 获取传的图片
        uid = str(uuid.uuid4()).replace('-', '')  # 生成uuid
        file_name = uid + '.' + str(image.name).split('.')[-1]  # 文件名 + 文件格式
        file_path = os.path.join(r"C:\Users\Administrator\Desktop\meiduo_mall_admin\static\images", file_name)  # 拼接文件
        with open(file_path, 'wb+') as f:
            for chunk in image.chunks():  # 写入
                f.write(chunk)

        skuimg = SKUImage.objects.create(
            sku_id=request.data.get("sku"),
            image='static\images/' + file_name
        )
        return Response({
            "id": skuimg.id,
            "sku": skuimg.sku_id,
            "image": skuimg.image.name,

        }, status=201)

    def update(self, request, *args, **kwargs):

        image = request.FILES.get('image')  # 获取传的图片
        basepath = r'C:\Users\Administrator\Desktop\meiduo_mall_admin\static\images'
        uid = str(uuid.uuid4()).replace('-', '')  # 生成uuid
        file_name = uid + '.' + str(image).split('.')[-1]  # 文件名 + 文件格式
        file_path = os.path.join(basepath, file_name)  # 拼接文件

        with open(file_path, 'wb+') as f:
            for chunk in image.chunks():  # 写入
                f.write(chunk)

        instance = self.get_object()
        try:
            os.remove(os.path.join(r'C:/Users/Administrator/Desktop/meiduo_mall_admin/', instance.image.name))
        except:
            pass
        instance.image = 'static\images/' + file_name
        instance.save()
        return Response({
            "id": instance.id,
            "sku": instance.sku_id,
            "image": instance.image.name,
        }, status=201)

class SkuListView(BaseView):
    def get(self, request):
        skus = SkuListSerializer(instance=SKU.objects.all(), many=True)
        return Response(skus.data)

from .seriali import SkuAdminSerializer

class SkuAdminView(ModelViewSet,BaseView):
    queryset = SKU.objects.all()
    serializer_class = SkuAdminSerializer
    pagination_class =  CustomPageNumberPagination

    def get_queryset(self):
        keyword = self.request.query_params.get("keyword", None)
        if keyword:
            return SKU.objects.filter(name__icontains=keyword)
        return SKU.objects.all()



from apps.goods.models import GoodsCategory,SPU
from .seriali import CateSerializer,SpuSerializer,AllSpuSerializer
class CateView(BaseView):
    def get(self,request):
        objs = GoodsCategory.objects.filter(subs = None)  # subs =  None三级分类
        s = CateSerializer(instance=objs,many=True)
        return Response(s.data)


from rest_framework.viewsets import ViewSet
from .seriali import SPUSpecification
class SpuView(ViewSet,BaseView):

    def get_all(self,request):
        objs = SPU.objects.all()
        s = AllSpuSerializer(instance=objs,many=True)
        return Response(s.data)

    def get_info(self,request,id):
        obj = SPUSpecification.objects.filter(spu_id=id)
        s = SpuSerializer(instance=obj, many=True)
        return Response(s.data)


from .seriali import SpuAdminSerializer
from rest_framework.generics import DestroyAPIView
class SpuAdminView(ListAPIView,DestroyAPIView,BaseView):

    queryset = SPU.objects.all()
    serializer_class = SpuAdminSerializer

    pagination_class = CustomPageNumberPagination

    def delete(self, request, *args, **kwargs):
        try:
            result = self.destroy(request, *args, **kwargs)
            return result
        except:
            return Response({"code":-1,"error":"删除失败"},status=404)

from .seriali import BrandSerializer,TypeSerializer
from apps.goods.models import Brand,GoodsCategory
class BrandList(ListAPIView,BaseView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer


class Catelist(ListAPIView,BaseView):
    queryset = GoodsCategory.objects.all()
    serializer_class = TypeSerializer


from .seriali import SpecsSerializer
class SpecsList(ListAPIView,CreateAPIView,DestroyAPIView):
    lookup_field = 'id'
    queryset = SPUSpecification.objects.all()
    serializer_class = SpecsSerializer
    pagination_class = CustomPageNumberPagination


from .seriali import SpecsoptionsSerializer
from apps.goods.models import SpecificationOption
class SpecsoptionsList(ListAPIView,CreateAPIView,DestroyAPIView,BaseView):
    lookup_field = 'id'
    queryset = SpecificationOption.objects.all()
    serializer_class = SpecsoptionsSerializer
    pagination_class = CustomPageNumberPagination

    def delete(self, request, *args, **kwargs):
        try:
            result = self.destroy(request, *args, **kwargs)
            return result
        except:
            return Response({"code":-1,"error":"删除失败"},status=404)


class SpecsSimple(ListAPIView,BaseView):
    queryset =  SPUSpecification.objects.all()
    serializer_class = SpecsSerializer

from .seriali import GoodsChannelSerializer,ChannelGroupSerializer

from apps.goods.models import GoodsChannel,GoodsChannelGroup
class GoodsChannelList(ModelViewSet,BaseView):
    lookup_field = 'id'
    queryset = GoodsChannel.objects.all()
    serializer_class = GoodsChannelSerializer
    pagination_class = CustomPageNumberPagination

class ChannelGroupView(ListAPIView,BaseView):
    queryset = GoodsChannelGroup.objects.all()
    serializer_class = ChannelGroupSerializer

from .seriali import BrandAdminSerializer,OrderSerializer
class BrandlList(ModelViewSet,BaseView):
    lookup_field = 'id'
    queryset = Brand.objects.all()
    serializer_class = BrandAdminSerializer
    pagination_class = CustomPageNumberPagination


from apps.orders.models import OrderInfo
from rest_framework.viewsets import ReadOnlyModelViewSet

class OrderAdmin(ReadOnlyModelViewSet,BaseView):

    serializer_class = OrderSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        keyword = self.request.query_params.get("keyword", None)
        if keyword:
            return OrderInfo.objects.filter(order_id__contains=keyword)
        return OrderInfo.objects.all()

class EditOrderStatusView(BaseView):
    def put(self,request,id):

        status = request.data.get("status",None)
        if status not in [1,2,3,4,5]:
            return Response({"code":-1},status=400)

        order = OrderInfo.objects.get(order_id=id)
        order.status = status
        order.save()
        return Response({"code": 0})



######## 权限
# 用户
from apps.users.models import User
# 组
from django.contrib.auth.models import Group
# 权限
from django.contrib.auth.models import Permission
# 类型 模型名
from django.contrib.auth.models import ContentType

from .seriali import PermissionSerializer,ContentTypeSerializer
class PermissionView(ModelViewSet,BaseView):

    queryset = Permission.objects.all()

    serializer_class = PermissionSerializer

    pagination_class = CustomPageNumberPagination



class ContentList(ListAPIView,BaseView):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer

from .seriali import GroupSerializer

class PermissionListView(ListAPIView,BaseView):

    queryset = Permission.objects.all()

    serializer_class = PermissionSerializer



class GroupsView(ModelViewSet,BaseView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    pagination_class = CustomPageNumberPagination

from .seriali import AdminSerializer
class AdminUserList(ModelViewSet,BaseView):

    queryset = User.objects.filter(is_staff=True)
    serializer_class = AdminSerializer
    pagination_class = CustomPageNumberPagination

class GroupsList(ListAPIView,BaseView):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


def f(request):
    request.FILES
