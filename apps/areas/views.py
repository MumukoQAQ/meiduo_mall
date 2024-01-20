from django.shortcuts import render

from django.http import JsonResponse,HttpResponse

from rest_framework.views import APIView
from rest_framework import serializers
from rest_framework.response import Response

from rest_framework.generics import GenericAPIView

# Create your views here.

from .models import Areas
class ProvinceSerializers(serializers.ModelSerializer):
    class Meta:
        model = Areas
        exclude = ['parent'] #排除

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = Areas
        fields = ['id', 'name']  # 包含你需要的字段

class CitySerializer(serializers.ModelSerializer):
    subs  = DistrictSerializer(many=True, read_only=True)
    class Meta:
        model = Areas
        fields = ['subs']

class CustomResponseSerializer(serializers.Serializer):
    code = serializers.CharField(default='0')
    errmsg = serializers.CharField(default='OK')
    sub_data = CitySerializer(source='*')  # 使用 source='*' 传递整个对象



from django.core.cache import cache # 缓存

class ProvinceView(GenericAPIView):
    queryset = Areas.objects.all()
    serializer_class = ProvinceSerializers

    def get(self,request,id=None):
        if not id:
            response = {
                "code": 0,
                "msg": "获取成功",
                "province_list":None
            }
            cache_provinces = cache.get("provinces")
            if cache_provinces:

                response["province_list"] = cache_provinces
            else:
                provinces = Areas.objects.filter(parent__isnull=True)
                serializer = ProvinceSerializers(instance=provinces, many=True)
                # serializer = self.get_serializer(instance=self.get_object(),many=True)
                response["province_list"] = serializer.data
                cache.set("provinces",serializer.data,360)
            return Response(response)

        else:
            cache_city = cache.get('sub_area_' + id)
            if cache_city:

                return Response(cache_city)
            else:

                city = Areas.objects.filter(id=id).first()
                city_serializer = CustomResponseSerializer(city)
                cache.set('sub_area_' + id, city_serializer.data, 360)
            return Response(city_serializer.data)