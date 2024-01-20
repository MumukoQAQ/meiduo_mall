from django.shortcuts import render

# Create your views here.

from django.http import JsonResponse, HttpResponse

from rest_framework.views import APIView
from rest_framework.serializers import Serializer, ModelSerializer

from collections import OrderedDict

from apps.contents.models import ContentCategory
from apps.goods.models import GoodsChannel, GoodsCategory


class IndexView(APIView):
    def get(self, request):
        categories = {}
        channels = GoodsChannel.objects.order_by('group_id', 'sequence')
        for cate in channels:
            group_id = cate.group_id
            if group_id not in categories:
                categories[group_id] = {
                    'channels': [],
                    'sub_cats': []
                }

            cat1 = cate.category
            categories[group_id]['channels'].append({
                'id': cat1.id,
                'name': cat1.name,
                'url': cate.url
            })

            for cat3 in cat1.subs.all():
                temp = {
                    'id': cat3.id,
                    'name': cat3.name,
                    'sub_cats': [],
                }
                for cat4 in cat3.subs.all():
                    temp['sub_cats'].append(
                        {"id": cat4.id, "name": cat4.name}
                    )
                categories[group_id]['sub_cats'].append(temp)

        contents = {}
        content_categories = ContentCategory.objects.all()

        for cat in content_categories:
            contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        context = {
            'categories': categories,
            'contents': contents,
        }
        return render(request, 'index.html', context)


def get_breadcrumb(category):
    """
    获取面包屑导航
    :param category: 商品类别
    :return: 面包屑导航字典
    """
    breadcrumb = dict(
        cat1='',
        cat2='',
        cat3=''
    )
    if category.parent is None:
        # 当前类别为一级类别
        breadcrumb['cat1'] = category.name
    elif category.subs.count() == 0:
        # 当前类别为三级
        print('三级')
        breadcrumb['cat3'] = category.name
        breadcrumb['cat2'] = category.parent.name
        breadcrumb['cat1'] = category.parent.parent.name
    else:
        # 当前类别为二级
        breadcrumb['cat2'] = category.name
        breadcrumb['cat1'] = category.parent.name

    return breadcrumb


from django.shortcuts import get_object_or_404
from apps.goods.models import SKU

from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from rest_framework.response import Response


class GoodsListSerializer(ModelSerializer):
    default_image_url = serializers.ImageField(source='default_image')

    class Meta:
        model = SKU
        fields = ['id', 'default_image_url', 'name', 'price']


from django.core.paginator import Paginator  # 分页器


class GoodsListView(APIView):
    def get(self, request, id):
        cate = get_object_or_404(GoodsCategory, id=id)
        mb = get_breadcrumb(cate)

        order = request.GET.get('ordering')
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')

        skus = cate.sku_set.filter(is_launched=True).order_by(order)
        # skus = SKU.objects.filter(category=cate,
        #                               is_launched=True).order_by(order)

        paginator = Paginator(skus, page_size)  # django分页器 skus数据  page_size 一页多少条
        # print(paginator.object_list) # 全部数据
        # print(len(paginator.object_list))
        # print(paginator.num_pages) 总共多少页
        sku_page = paginator.page(page)  # 获取page页的数据
        # print(paginator.count) # 数据量

        # print(sku_page.object_list)
        serializer = GoodsListSerializer(instance=sku_page, many=True)
        return Response({
            'code': 0,
            'errmsg': 'ok',
            'breadcrumb': mb,
            'list': serializer.data,
            'count': paginator.count
        })


class HotGoodsView(APIView):

    def get(self, request, id):
        hot_skus = SKU.objects.filter(category_id=id).order_by('-sales')
        serializer = GoodsListSerializer(instance=hot_skus, many=True)
        return Response({
            'code': 0,
            'errmsg': 'ok',
            'hot_skus': serializer.data,
        })


from haystack.views import SearchView
from django.http import JsonResponse


class MySearchView(SearchView):
    '''重写SearchView类'''

    def create_response(self):
        # 获取搜索结果
        context = self.get_context()
        data_list = []
        print(context)
        print(context['page'].object_list)
        for sku in context['page'].object_list:
            data_list.append({
                'id': sku.object.id,
                'name': sku.object.name,
                'price': sku.object.price,
                'default_image_url': sku.object.default_image.url,
                'searchkey': context.get('query'),
                'page_size': context['page'].paginator.num_pages,
                'count': context['page'].paginator.count
            })
        # 拼接参数, 返回
        return JsonResponse(data_list, safe=False)


from .utils import get_goods_specs
from django.views import View
from apps.goods.models import GoodsVisitCount
from datetime import datetime
from django.middleware.csrf import get_token

class GoodsDetailiView(View):
    def get(self, request, group_id):
        sku = get_object_or_404(SKU, id=group_id)
        goods_specs = get_goods_specs(sku)

        categories = {}
        channels = GoodsChannel.objects.order_by('group_id', 'sequence')

        for cate in channels:
            group_id = cate.group_id
            if group_id not in categories:
                categories[group_id] = {
                    'channels': [],
                    'sub_cats': []
                }

            cat1 = cate.category
            categories[group_id]['channels'].append({
                'id': cat1.id,
                'name': cat1.name,
                'url': cate.url
            })

            for cat3 in cat1.subs.all():
                temp = {
                    'id': cat3.id,
                    'name': cat3.name,
                    'sub_cats': [],
                }
                for cat4 in cat3.subs.all():
                    temp['sub_cats'].append(
                        {"id": cat4.id, "name": cat4.name}
                    )
                categories[group_id]['sub_cats'].append(temp)
        context = {
            'categories': categories,
            'breadcrumb': get_breadcrumb(sku.category),
            'sku': sku,
            'specs': goods_specs,
        }

        return render(request, 'detail.html', context)

    def post(self, request,group_id):
        category = get_object_or_404(GoodsCategory,id=group_id)
        today = datetime.today()

        try:
            category_count = GoodsVisitCount.objects.get(category=category,date=today)
        except GoodsVisitCount.DoesNotExist:
            GoodsVisitCount.objects.create(
                category=category,
                date=today,
                count=1
            )
        else:
            category_count.count += 1
            category_count.save()
        return JsonResponse({"code": 0, "msg": "ok"})
