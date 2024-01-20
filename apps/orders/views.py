from decimal import Decimal

from django.shortcuts import render, HttpResponse

from django.http import JsonResponse
# Create your views here.


from rest_framework.views import APIView

from apps.areas.models import Areas
from apps.users.views import LoginAPIView
from apps.users.models import Address
from apps.goods.models import SKU

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework.response import Response

from django_redis import get_redis_connection


class AddressSerializer(ModelSerializer):
    province = serializers.StringRelatedField()
    city = serializers.StringRelatedField()
    district = serializers.StringRelatedField()

    class Meta:
        model = Address
        exclude = ['is_deleted', 'tel', 'user', 'email', 'title']  # 排除


class OrderView(LoginAPIView):

    def get(self, request):
        user = request.user

        addrs = user.addresses.all()  # 地址实例

        adds_serializer = AddressSerializer(instance=addrs, many=True)

        redis_cli = get_redis_connection('carts')

        pipeline = redis_cli.pipeline()
        pipeline.hgetall(user.id)
        pipeline.smembers('s%s' % user.id)

        result = pipeline.execute()
        skus = []

        for sku in result[1]:
            goods = SKU.objects.get(id=sku)
            skus.append(
                {
                    "id": goods.id,
                    "name": goods.name,
                    "default_image_url": goods.default_image.url,
                    "count": int(result[0][sku]),
                    "price": goods.price
                }
            )

        context = {
            'addresses': adds_serializer.data,
            'skus': skus,
            'freight': 10,
        }
        return Response({'code': 0, 'errmsg': 'ok', 'context': context})


from django.utils import timezone
from decimal import Decimal
from apps.orders.models import OrderInfo,OrderGoods

from django.db import transaction # 事务

import time

class GenerationOrder(LoginAPIView):

    def post(self, request):

        user = request.user
        data = request.data

        address = Address.objects.get(id=data.get('address_id'))
        pay_method = data.get('pay_method')

        order_id = timezone.localtime().strftime("%Y%m%d%H%M%S") + '%09d' % user.id
        pay_status = 1 if pay_method == 2 else 2

        total_count = 0
        total_amount = Decimal('0')
        freight = Decimal('10.00')

        with transaction.atomic():  # with 语句开启事务

            save_id = transaction.savepoint() # 开始点 要回滚就到这里

            orderinfo = OrderInfo.objects.create(
                order_id = order_id,
                user = user,
                address = address,
                total_count = total_count,
                pay_method = pay_method,
                status = pay_status,
                total_amount = total_amount,
                freight = freight
            )

            redis_cli = get_redis_connection('carts')
            pipeline = redis_cli.pipeline()
            pipeline.hgetall(user.id)
            pipeline.smembers('s%s' % user.id)

            carts_result = pipeline.execute()

            carts = {}
            print(carts_result)

            for sku_id in carts_result[1]:
                carts[int(sku_id)] = int(carts_result[0][sku_id])

            for sku_id, count in carts.items():

                while True:
                    sku = SKU.objects.get(id=sku_id)

                    # 读取原始库存
                    origin_stock = sku.stock
                    origin_sales = sku.sales

                    if sku.stock < count:
                        transaction.savepoint_rollback(save_id)  # 回滚
                        return JsonResponse({"code": 400, "errmsg": "库存不足"})
                    else:
                        # 乐观锁更新库存和销量
                        new_stock = origin_stock - count
                        new_sales = origin_sales + count
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                        if result == 0:
                            continue

                        total_count += count
                        total_amount += (sku.price * count)

                        OrderGoods.objects.create(
                            order=orderinfo,
                            sku = sku,
                            count = count,
                            price = sku.price
                        )
                        break

            orderinfo.total_count = total_count
            orderinfo.total_amount = total_amount + freight


            orderinfo.save()

            # pipeline.srem('s%s' % user.id, *carts_result[1])
            # pipeline.hdel(user.id, *carts_result[1])
            # pipeline.execute()

            transaction.savepoint_commit(save_id) # 提交点

        return JsonResponse({
            "code": 0,
            "errmsg":"ok",
            "order_id":order_id
        })
