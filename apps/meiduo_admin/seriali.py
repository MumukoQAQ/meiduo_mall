from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from rest_framework.generics import ListAPIView, RetrieveAPIView

from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import ModelViewSet

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from apps.users.models import User


class UserlistSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True)  # write_only只保存 不返回给前端
    password2 = serializers.CharField(write_only=True)  # write_only只保存 不返回给前端

    class Meta:
        model = User
        fields = ('id', 'username', 'mobile', 'email', 'password', 'password2')

    def validate(self, data):  # 添加自定义验证方法
        password = data.get('password')
        password2 = data.get('password2')
        if password != password2:
            raise serializers.ValidationError({"error": "密码不匹配"})
        return data

    def create(self, validated_data):
        # 重写保存方法 实现密码加密
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


from apps.goods.models import SKUImage, SKU


class SkuImgSerializer(serializers.ModelSerializer):
    image = serializers.CharField()
    sku = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = SKUImage
        fields = ['id', 'sku', 'image']


class SkuListSerializer(ModelSerializer):
    class Meta:
        model = SKU
        fields = ['id', 'default_image', 'name', ]


from apps.goods.models import SPUSpecification, SpecificationOption, SKUSpecification


class SKUSpecificationSerialzier(serializers.ModelSerializer):
    """
        SKU规格表序列化器
    """
    spec_id = serializers.IntegerField()
    option_id = serializers.IntegerField()

    class Meta:
        model = SKUSpecification  # SKUSpecification中sku外键关联了SKU表
        fields = ("spec_id", 'option_id')


from apps.goods.models import GoodsCategory, SPU


class SkuAdminSerializer(ModelSerializer):
    category_id = serializers.IntegerField()
    category = serializers.StringRelatedField(read_only=True)  # 两种方式都可以获取外键数据

    spu_id = serializers.IntegerField()
    spu = serializers.CharField(source='spu.name', read_only=True)

    specs = SKUSpecificationSerialzier(many=True, write_only=True)

    class Meta:
        model = SKU
        exclude = ['default_image', 'comments', 'update_time', 'caption']  # 排除

    def create(self, validated_data):
        specs_data = validated_data.pop('specs')
        # 保存sku
        sku = SKU.objects.create(**validated_data)
        for spec_data in specs_data:
            SKUSpecification.objects.create(sku=sku, **spec_data)
            # 返回sku
        return sku


class CateSerializer(ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = '__all__'


class AllSpuSerializer(ModelSerializer):
    spu = serializers.StringRelatedField()

    class Meta:
        model = SPUSpecification
        fields = ['id', 'name', 'spu', 'spu_id']


class GoodsOptineSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecificationOption
        fields = ('id', 'value')


class SpuSerializer(ModelSerializer):
    spu = serializers.StringRelatedField()
    options = GoodsOptineSerializer(many=True)

    class Meta:
        model = SPUSpecification
        fields = ['id', 'name', 'spu', 'spu_id', 'options']


class SpuAdminSerializer(ModelSerializer):
    brand_id = serializers.IntegerField()
    brand = serializers.StringRelatedField()

    category1 = serializers.StringRelatedField()
    category2 = serializers.StringRelatedField()
    category3 = serializers.StringRelatedField()

    class Meta:
        model = SPU
        # fields = "__all__"
        exclude = ['create_time', 'update_time']


from apps.goods.models import Brand


class BrandSerializer(ModelSerializer):
    class Meta:
        model = Brand
        fields = "__all__"


class TypeSerializer(serializers.ModelSerializer):
    subs = serializers.SerializerMethodField()

    class Meta:
        model = GoodsCategory
        fields = "__all__"

    def get_subs(self, obj):
        """
        递归获取子类别
        """
        if obj.subs.all().exists():
            return TypeSerializer(obj.subs.all(), many=True).data
        return None


class SpecsSerializer(serializers.ModelSerializer):
    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()

    class Meta:
        model = SPUSpecification
        fields = "__all__"


class SpecsoptionsSerializer(serializers.ModelSerializer):
    spec = serializers.CharField(source="spec.name", read_only=True)
    spec_id = serializers.IntegerField()

    class Meta:
        model = SpecificationOption
        fields = "__all__"


from apps.goods.models import GoodsChannel, GoodsChannelGroup


class GoodsChannelSerializer(serializers.ModelSerializer):
    group = serializers.StringRelatedField()
    group_id = serializers.IntegerField()

    category_id = serializers.IntegerField()
    category = serializers.StringRelatedField()

    class Meta:
        model = GoodsChannel
        fields = "__all__"


class ChannelGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsChannelGroup
        fields = "__all__"


class BrandAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = "__all__"


from apps.orders.models import OrderInfo, OrderGoods


class OrderSKuSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ["name", "default_image"]


class OrderGoodsSerializer(serializers.ModelSerializer):
    sku = OrderSKuSerializer(many=False)

    class Meta:
        model = OrderGoods
        fields = ["count", "price", "sku"]


class OrderSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    skus = OrderGoodsSerializer(many=True)

    class Meta:
        model = OrderInfo
        fields = "__all__"


# 用户
from apps.users.models import User
# 组
from django.contrib.auth.models import Group
# 权限
from django.contrib.auth.models import Permission


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = "__all__"


from django.contrib.auth.models import ContentType


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ["id", "name"]  # name ContentType属性方法


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"


class AdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["id", "username", "email", "mobile", "password", "groups","user_permissions"]

    def __init__(self, *args, **kwargs):
        super(AdminSerializer, self).__init__(*args, **kwargs)
        # 在创建用户时使密码字段必填
        if not self.instance:
            self.fields['password'].required = True

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data.get("password"))
        user.is_staff = True
        user.save()

        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password',None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance

