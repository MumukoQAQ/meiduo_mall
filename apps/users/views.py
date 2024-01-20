import random

from django.views import View
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet,ModelViewSet
from rest_framework.views import APIView

from apps.users.models import User
from django.http import JsonResponse, HttpResponse

from utils.verify import generate_code, send_message,sendAVerificationEmail

# from celery_tasks.sms.tasks import send_sms_code,
import logging

logger = logging.getLogger('django')


class registrationChecks(ViewSet):
    """判断用户名是否重复注册"""

    def checkTheUsername(self, request, username):
        """
        :param request: 请求对象
        :param username: 用户名
        :return: JSON
        """
        count = User.objects.filter(username=username)
        return Response({'code': 0, 'errmsg': 'OK', 'count': count})

    def checkPhoneNumber(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        return Response({'code': 0, 'errmsg': 'OK', 'count': count})

    def get_user(self, request):
        print(request.user)
        print(request.session.items())
        print(request.COOKIES.items())
        return HttpResponse(request.session.items())


import re
from django.core.exceptions import ValidationError

from django.contrib.auth import login  # 自带的认证


class userRegistration(APIView):

    def post(self, request, *args, **kwargs):
        try:

            username = request.data.get('username')
            password = request.data.get('password')
            mobile = request.data.get('mobile')
            sms_code = request.data.get('sms_code')

            if len(request.data) != 6 or 'mobile' not in request.data:
                return Response({"code": 0, "message": "缺少参数。"}, status=400)

            self.validate_user_parameters(username, password, mobile, sms_code)
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
            login(request, user)
            return Response({"code": 0, "message": "注册成功。"}, status=200)

        except ValidationError as e:
            return Response({"code": 400, "errmsg": str(e.message)}, status=400)

    def validate_user_parameters(self, username, password, mobile, sms_code):
        if not username:
            raise ValidationError('用户名不能为空。')
        if User.objects.filter(username=username).exists():
            raise ValidationError('用户名已存在。')
        if not password or len(password) < 8:
            raise ValidationError('密码长度必须至少为8个字符。')

        if not mobile or not re.fullmatch(r'\d{11}', mobile):
            raise ValidationError('无效的手机号。')

        redis_cli = get_redis_connection('code')
        try:
            redis_mobile = redis_cli.get(mobile).decode()
        except:
            raise ValidationError('手机验证码失效。')
        if redis_mobile != sms_code:
            raise ValidationError('手机验证码错误。')


# redis

from django_redis import get_redis_connection


class ImageCodeView(APIView):  # 验证码

    def get(self, request, uuid):
        redis_cli = get_redis_connection('code')
        code, img = generate_code(4)
        redis_cli.setex(str(uuid), 300, code)  # 写入redis
        return HttpResponse(img, content_type='image/jpeg')


class MobileCodeView(APIView):

    def get(self, request, mobile):

        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')
        # 校验参数
        if not all([image_code_client, uuid]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})

        redis_conn = get_redis_connection('code')

        if redis_conn.get(mobile) is not None:
            return JsonResponse({'code': 400, 'errmsg': '操作频繁'})

        image_code_server = redis_conn.get(uuid)

        if image_code_server is None:
            # 图形验证码过期或者不存在
            return JsonResponse({'code': 400, 'errmsg': '图形验证码失效'},status=400)
        try:
            redis_conn.delete(uuid)
        except Exception as e:
            logger.error(e)

        # 对比图形验证码
        image_code_server = image_code_server.decode()  # bytes转字符串
        if image_code_client.lower() != image_code_server.lower():  # 转小写后比较
            return JsonResponse({'code': 400, 'errmsg ': '输入图形验证码有误'},status=400)

        sms_code = '%04d' % random.randint(0, 9999)
        logger.info(sms_code)

        redis_conn.setex(mobile, 300, sms_code)  # 写入redis
        send = send_message(mobile=mobile, sms_code=sms_code)  # 发送短信
        # send = send_sms_code.delay(mobile=mobile,sms_code=sms_code)
        if send:
            return JsonResponse({'code': 0, 'errmsg': '短信发送成功'})
        else:
            redis_conn.delete(mobile)
            return JsonResponse({'code': 400, 'errmsg': '短信发送失败，请检查手机号码'})


def f(request):
    request.user.is_authenticated
    request.COOKIES.items()


from django.contrib.auth import logout
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated

from apps.carts.utils import merge_carts

class UserLoginView(ViewSet):
    def user_login(self, request, *args, **kwargs):

        if len(request.data) < 2:
            return Response({'code': 400, 'errmsg': '缺少必传参数'})

        username = request.data.get("username")
        password = request.data.get("password")
        remembered = request.data.get("remembered")

        if re.match('1[3-9]\d{9}', username):
            User.USERNAME_FIELD = 'mobile'  #
        else:
            User.USERNAME_FIELD = 'username'

        user = authenticate(username=username, password=password)
        if not user:
            return Response({'code': 400, 'errmsg': '用户名或者密码错误'})

        login(request, user)

        response = JsonResponse({'code': 0, 'errmsg': '登陆成功'})
        response.set_cookie('username', username, "max_age", 3600)
        if not remembered:
            request.session.set_expiry(0)
            # 为了首页显示用户信息
            response.set_cookie('username', username)

        response = merge_carts(request,response) # cookie中的购物车数据合并到redis中

        return response

    def user_logout(self, request, *args, **kwargs):
        logout(request)
        request.session.flush()
        response = JsonResponse({'code': 0,
                                 'errmsg': 'ok'})
        # 退出登录时清除cookie中的username
        response.delete_cookie('username')
        return response

from rest_framework.exceptions import NotAuthenticated
class LoginAPIView(APIView):  # 登录后才能访问的视图
    permission_classes = [IsAuthenticated]
    def handle_exception(self, exc):
        print(exc)
        if isinstance(exc, NotAuthenticated):
            return JsonResponse({"error": "未登录或登录失效", "code": 400}, status=400)
        return super().handle_exception(exc)

from utils.verify import generateTokens,decryptTheToken
class SetEmailView(LoginAPIView):
    def put(self,request):
        email = request.data.get('email')
        request.user.email = email
        request.user.save()

        token = generateTokens(request.user.id)
        sendAVerificationEmail(email,token)
        try:
            return JsonResponse({"error": "ok", "code": 0}, status=200)
        except:
            return JsonResponse({"error": "添加邮箱失败，检查邮箱格式是否正确！", "code": 400}, status=400)

class VerifyEmailVIew(APIView):
    def put(self,request):
        token = request.GET.get('token')
        try:
            user_id = decryptTheToken(token)
            cur_user = User.objects.filter(id=user_id).first()
            cur_user.email_active = True
            cur_user.save()
            return JsonResponse({'code': 1,"msg":"邮箱验证成功"})
        except Exception as e:
            pass
        return JsonResponse({'code':0,"errmsg":"没有数据"},status=400)

class UserInfoView(LoginAPIView):
    def get(self, request):
        response = {
            "code": 0,
            "info_data": {
                "username": request.user.username,
                "mobile": request.user.mobile,
                "email": request.user.email,
                "email_active": request.user.email_active
            }
        }
        return JsonResponse(response)

    def put(self,request):

        password = request.data.get('new_password')
        password2 = request.data.get('new_password2')
        old_password = request.data.get('old_password')
        if password != password2:
            return JsonResponse({"code": 1, "msg": "两次输入的密码不同"})

        user = authenticate(username=request.user.username, password=old_password)
        if not user:
            return Response({'code': 400, 'errmsg': '原始密码错误'})

        if not re.match(r'^[0-9A-Za-z]{8,20}$', password2):
            return JsonResponse({'code': 400,'errmsg': '密码最少8位,最长20位'})

        request.user.set_password(password2)
        request.user.save()
        logout(request)

        response = JsonResponse({'code': 0,'errmsg': 'ok'})
        response.delete_cookie('username')
        return response

######### 地址相关业务逻辑
from apps.areas.models import Areas
from apps.users.models import Address
from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

class AddressSerializer(ModelSerializer):
    province_id = serializers.PrimaryKeyRelatedField(
        source='province', queryset=Areas.objects.all(), write_only=True) # 关联
    city_id = serializers.PrimaryKeyRelatedField(
        source='city', queryset=Areas.objects.all(), write_only=True)
    district_id = serializers.PrimaryKeyRelatedField(
        source='district', queryset=Areas.objects.all(), write_only=True)

    class Meta:
        model = Address
        exclude = ['is_deleted']  # 排除
        extra_kwargs = {
            'province': {'source': 'province_id'},
            'city': {'source': 'city_id'},
            'district': {'source': 'district_id'}
        }

class ShowAddressSerializer(ModelSerializer):
    province = serializers.StringRelatedField()  # 关联
    city = serializers.CharField(source='city.name', read_only=True)
    district = serializers.CharField(source='district.name', read_only=True)
    class Meta:
        model = Address
        exclude = ['user','is_deleted']  # 排除

from django.shortcuts import get_object_or_404
class AddressView(ViewSet):
    def get_address(self,request):
        user_address = Address.objects.filter(user=request.user)

        address_serializer = ShowAddressSerializer(instance=user_address,many=True)
        response = {
            'code':0,
            'msg':'成功',
            'addresses':address_serializer.data,
        }
        return Response(response)

    def post_address(self,request):
        print(request.headers)
        request.data['user'] = request.user.id
        #{'receiver': '123123', 'province_id': 120000, 'city_id': 120100, 'district_id': 120101, 'place': '132131', 'mobile': '13145550200', 'tel': '13145550200', 'email': '13145550200@qq.com', 'title': '123123'}
        address_serializer = AddressSerializer(data=request.data)
        address_serializer.is_valid(raise_exception=True)
        address_serializer.save()
        # try:
        #     Address.objects.create(
        #         user=request.user,
        #         title=request.data.get('title'),
        #         receiver=request.data.get('receiver'),
        #         province = Areas.objects.get(id=request.data.get('province_id')),
        #         city = Areas.objects.get(id=request.data.get('city_id')),
        #         district = Areas.objects.get(id=request.data.get('district_id')),
        #         place=request.data.get('place'),
        #         mobile=request.data.get('mobile'),
        #         tel=request.data.get('tel'),
        #         email=request.data.get('email')
        #     )
        return JsonResponse({'code': 0, 'errmsg': '添加成功','address':address_serializer.data})

    def delete_address(self,request,id):
        Address.objects.get(id=id).delete()
        return JsonResponse({"code":0,"msg":"删除成功"})

    def edit_address(self,request,id):
        cur_address = get_object_or_404(Address,id=id)
        request.data['user'] = request.user.id
        dress_serializer = AddressSerializer(instance=cur_address,data=request.data)
        dress_serializer.is_valid(raise_exception=True)
        dress_serializer.save()
        return  JsonResponse({"code":0,"msg":"编辑成功"})

    def put_title(self,request,id):
        address = get_object_or_404(Address,id=id)
        address.title = request.data.get("title")
        address.save()
        return JsonResponse({"code": 0, "msg":"修改成功"})

    def set_default(self,request,id):
        address = Address.objects.get(id=id)
        request.user.default_address = address
        request.user.save()
        return JsonResponse({"code": 0, "msg": "设置成功"})



from apps.goods.models import SKU
import time

from apps.goods.views import GoodsListSerializer

class BrowsingHistory(LoginAPIView):

    def get(self,request):
        redis_cli = get_redis_connection('history')
        skus = redis_cli.zrevrange(f'{request.user.id}', 0, -1) # redis 获取当前用户的浏览记录
        instance_list = []
        for sku_id in skus:
            instance_list.append(
                SKU.objects.get(id=sku_id)
            )
        serializer = GoodsListSerializer(instance=instance_list,many=True)
        return JsonResponse(
            {"code": 0,
             "msg": "ok",
             "skus":serializer.data
             }
        )

    def post(self,request):
        sku_id = request.data.get("sku_id")
        sku = get_object_or_404(SKU,id=sku_id)
        redis_cli = get_redis_connection('history')

        current_timestamp = int(time.time())
        redis_cli.zadd(f'{request.user.id}', {sku_id: current_timestamp})  # 有序集合
        # 保持有序集合的大小为 5
        # 移除索引范围在 0 到 -6 的元素，只保留最新的 5 个元素
        redis_cli.zremrangebyrank(f'{request.user.id}', 0, -6)
        redis_cli.expire(f'{request.user.id}', 3600)
        return JsonResponse({"code": 0, "msg": "ok"})





