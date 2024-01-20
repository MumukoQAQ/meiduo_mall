from django.shortcuts import render

# Create your views here.


from alipay import AliPay, DCAliPay, ISVAliPay
from alipay.utils import AliPayConfig

from rest_framework.views import APIView

from apps.orders.models import OrderInfo
from apps.pay.models import Payment
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from apps.users.views import LoginAPIView
from django.http import HttpResponse
from meiduo_mall import settings


class PayUrlView(LoginAPIView):


    def get(self,request,order_id):
        order = get_object_or_404(OrderInfo,order_id=order_id,status=1)

        app_private_key_string = open(settings.APP_PRIVATE_KEY_PATH).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH).read()

        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调 url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG,  # 默认 False
            verbose=True,  # 输出调试数据
            config=AliPayConfig(timeout=15)  # 可选，请求超时时间
        )

        subject = "测试订单"

        # 电脑网站支付，需要跳转到：https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order.order_id,
            total_amount= str(order.total_amount),
            subject=subject,
            return_url= settings.ALIPAY_RETURN_URL,
            notify_url="https://example.com/notify"  # 可选，不填则使用默认 notify url
        )
        pay_url = "https://openapi-sandbox.dl.alipaydev.com/gateway.do?" + order_string

        return JsonResponse({
            "code":0,
            "msg":"ok",
            "alipay_url":pay_url
        })


    def put(self,request):

        data = request.GET.dict()
        print(data)
        try:
            signature = data.pop("sign")
        except:
            return JsonResponse({"code": 0,"errmsg": "缺失签名参数",})

        app_private_key_string = open(settings.APP_PRIVATE_KEY_PATH).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH).read()
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调 url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG,  # 默认 False
            verbose=True,  # 输出调试数据
            config=AliPayConfig(timeout=15)  # 可选，请求超时时间
        )

        # verification
        success = alipay.verify(data, signature)

        if success:
            order = OrderInfo.objects.get(order_id=data['out_trade_no'])
            order.status = 2
            order.save()

            payment = Payment.objects.create(
                order = order,
                trade_id = data["trade_no"]
            )

        else:
            return JsonResponse({"code": 0, "errmsg": "付款失败", })

        return JsonResponse({"code": 0, "errmsg": "支付成功", })

