from django.shortcuts import render, HttpResponse

from django.http import JsonResponse

from django_redis import get_redis_connection
# Create your views here.


from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from apps.goods.models import SKU

import pickle
import base64


class cartsView(APIView):

    def get(self, request):
        user = request.user
        if user.is_authenticated:
            catrs = {}
            redis_cli = get_redis_connection('carts')

            skus = redis_cli.hgetall(user.id)
            selected_id = redis_cli.smembers('s%s' % user.id)

            for sku_id, c in skus.items():
                catrs[int(sku_id)] = {
                    'count': int(c),
                    'selected': sku_id in selected_id
                }
        else:
            before_catrs = request.COOKIES.get('carts')
            if not before_catrs:
                return JsonResponse({'code': 1, 'errmsg': '没有购物车数据'})
            catrs = pickle.loads(base64.b64decode(before_catrs))  # 解密之前的购物车数据

        goods = SKU.objects.filter(id__in=catrs.keys())
        sku_list = []
        for sku in goods:
            sku_list.append(
                {
                    "id": sku.id,
                    "price": sku.price,
                    "name": sku.name,
                    "default_image_url": sku.default_image.url,
                    "count": catrs[sku.id]['count'],
                    "selected": catrs[sku.id]['selected'],
                    "amount": catrs[sku.id]['count'] * sku.price
                }
            )
        return JsonResponse({'code': 0, 'msg': 'ok', 'cart_skus': sku_list})

    def post(self, request):
        sku_id = request.data.get('sku_id')
        count = request.data.get('count')
        sku = get_object_or_404(SKU, id=sku_id)
        user = request.user
        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            pl = redis_cli.pipeline()  # redis管道

            pl.hincrby(user.id, sku_id, count)
            pl.sadd('s%s' % user.id, sku_id)
            pl.execute()  # 提交命令

            return JsonResponse({'code': 0, 'msg': 'ok'})

        else:
            before_catrs = request.COOKIES.get('carts')
            if before_catrs:  # 判断cookie是否存在购物车
                catrs = pickle.loads(base64.b64decode(before_catrs))  # 解密之前的购物车数据
            else:
                catrs = {}
            if catrs.get(sku_id):  # 判断当前商品id是否存在之前的购物车
                count += catrs[sku_id]['count']  # 累加之前的数量

            catrs[sku_id] = {'count': count, 'selected': True}
            base64_encode = base64.b64encode(pickle.dumps(catrs))
            response = JsonResponse({'code': 0, 'msg': 'ok'})
            response.set_cookie(
                'carts', base64_encode.decode(), max_age=3600
            )
            return response

    def put(self, request):

        user = request.user
        sku_id = request.data.get('sku_id')
        sku = get_object_or_404(SKU, id=sku_id)

        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            pl = redis_cli.pipeline()  # redis管道
            redis_cli.hset(user.id, sku_id, request.data.get('count'))
            if request.data.get('selected'):
                pl.sadd('s%s' % user.id, sku_id)
            else:
                pl.srem('s%s' % user.id, sku_id)
            pl.execute()  # 提交命令
            return JsonResponse({'code': 0, 'msg': 'ok', 'cart_sku': {'count': request.data.get('count'),
                                                                      'selected': request.data.get('selected')}})

        else:
            before_catrs = request.COOKIES.get('carts')
            request.data.pop("sku_id")
            catrs = pickle.loads(base64.b64decode(before_catrs))
            catrs[sku_id] = request.data

            base64_encode = base64.b64encode(pickle.dumps(catrs))
            response = JsonResponse({'code': 0, 'msg': 'ok', 'cart_sku': request.data})
            response.set_cookie(
                'carts', base64_encode.decode(), max_age=3600
            )
            return response

    def delete(self, request):

        sku_id = request.data.get('sku_id')
        user = request.user
        if user.is_authenticated:
            redis_cli = get_redis_connection('carts')
            pl = redis_cli.pipeline()
            redis_cli.hdel(user.id, sku_id)  # 删除商品
            redis_cli.srem('s%s' % user.id, sku_id)  # 删除选中
            pl.execute()  # 提交命令
            return JsonResponse({'code': 0, 'msg': 'ok'})

        else:
            before_catrs = request.COOKIES.get('carts')
            catrs = pickle.loads(base64.b64decode(before_catrs))

            catrs.pop(sku_id)
            base64_encode = base64.b64encode(pickle.dumps(catrs))
            response = JsonResponse({'code': 0, 'msg': 'ok'})
            if catrs:
                response.set_cookie(
                    'carts', base64_encode.decode(), max_age=3600
                )
            else:
                response.delete_cookie('carts')
            return response


