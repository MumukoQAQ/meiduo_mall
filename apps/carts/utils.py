import pickle
import base64

import redis
from django_redis import get_redis_connection
def merge_carts(request,response):

    cookie_carts = request.COOKIES.get('carts')

    if cookie_carts:
        catrs = pickle.loads(base64.b64decode(cookie_carts))
        cookie_dict = {}
        selected_list = []
        unselected_list = []

        for sku_id,c in catrs.items():
            cookie_dict[sku_id] = catrs[sku_id]['count']
            if catrs[sku_id]['selected']:
                selected_list.append(sku_id)
            else:
                unselected_list.append(sku_id)

        redis_cli = get_redis_connection('carts')
        pipeline = redis_cli.pipeline()
        pipeline.hmset(request.user.id,cookie_dict)


        if selected_list:
            pipeline.sadd('s%s'%request.user.id,*selected_list) # *星号解包
        if unselected_list:
            pipeline.srem('s%s' % request.user.id, *unselected_list)  # *星号解包

        pipeline.execute()  # 提交命令
        response.delete_cookie('carts')

    return response

