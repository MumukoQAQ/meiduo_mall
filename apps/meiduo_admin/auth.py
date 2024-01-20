import jwt
from django.conf import settings
from rest_framework import authentication, exceptions
from apps.users.models import User
import datetime


from django.contrib.auth import authenticate
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class AdminOnlyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            raise AuthenticationFailed({'code': -1, 'msg': '账号或密码错误'}, code=400)
        if not user.is_staff:
            raise AuthenticationFailed({'code': -1, 'msg': '不是管理员账号'}, code=400)
        jwt_token = GenerateToken(user)

        return (user, jwt_token)

def GenerateToken(user):
    expiration_time = datetime.datetime.now() + datetime.timedelta(seconds=settings.JWT_EXP)
    expiration_timestamp = int(expiration_time.timestamp())  # 转换为 Unix 时间戳
    payload = {
        'id': user.id,
        'username': user.username,
        'exp': expiration_timestamp
    }
    jwt_token = jwt.encode(payload, settings.SECRET_KEY)
    return jwt_token


class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_data = authentication.get_authorization_header(request)  # jwt token 数据
        if not auth_data:
            # return None
            raise exceptions.AuthenticationFailed('未携带token')
        prefix, token = auth_data.decode('utf-8').split(' ')  # 将jwt转为字符串
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms="HS256")  # 解密jwt数据
            user = User.objects.get(username=payload['username'])  # 获取用户数据
            return (user, token) # 返回

        except jwt.DecodeError as identifier:
            raise exceptions.AuthenticationFailed('token无效')
        except jwt.ExpiredSignatureError as identifier:
            raise exceptions.AuthenticationFailed('token过期，请重新登录')



