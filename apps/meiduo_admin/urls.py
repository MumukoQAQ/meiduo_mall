from django.contrib import admin
from django.urls import path, include

from apps.meiduo_admin import views

from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register('skus/images', views.SkuImgView,basename='image')
router.register('skus', views.SkuAdminView,basename='sku')
router.register('goods/channels', views.GoodsChannelList,basename='goods')
router.register('goods/brands', views.BrandlList,basename='brands')
router.register('orders', views.OrderAdmin,basename='orders')
router.register('permission/perms', views.PermissionView,basename='permission')
router.register('permission/groups', views.GroupsView,basename='groups')
router.register('permission/admins', views.AdminUserList,basename='admin')


urlpatterns = [
    path('authorizations/', views.LoginView.as_view()),  # 登录

    path('statistical/total_count/', views.TotalUserView.as_view()),  # 总量
    path('statistical/month_increment/', views.MonthAddView.as_view()),  # 月活跃统计

    path('statistical/day_increment/', views.DailyAddView.as_view()),  # 日新增统计
    # path('statistical/goods_day_views/', DailyAddView.as_view()),  # 日新增统计

    path('statistical/day_active/', views.DailyActiveView.as_view()),  # 日活跃统计
    path('statistical/day_orders/', views.DailyOrderActiveView.as_view()),  # 日下单统计


    path('users/',views.UserListView.as_view()), # 用户列表
    path('skus/simple/',views.SkuListView.as_view()),

    path('goods/',views.SpuAdminView.as_view()),
    path('goods/<int:pk>/',views.SpuAdminView.as_view()),

    path('goods/brands/simple/',views.BrandList.as_view()),
    path('goods/channel/categories/',views.Catelist.as_view()),


    path('goods/specs/',views.SpecsList.as_view()),
    path('goods/specs/<int:id>/',views.SpecsList.as_view()),

    path('specs/options/', views.SpecsoptionsList.as_view()),
    path('specs/options/<int:id>/',views.SpecsoptionsList.as_view()),

    path('goods/specs/simple/',views.SpecsSimple.as_view()),

    # path('goods/channels/',views.GoodsChannelList.as_view()),

    path('goods/channel_types/',views.ChannelGroupView.as_view()),
    path('goods/categories/',views.Catelist.as_view()),

    path('orders/<int:id>/status/',views.EditOrderStatusView.as_view()),

    path('skus/categories/',views.CateView.as_view()),
    #
    path('goods/simple/',views.SpuView.as_view({"get":"get_all"})),
    path('goods/<int:id>/specs/',views.SpuView.as_view({"get":"get_info"})),


    path('permission/content_types/',views.ContentList.as_view()),
    path('permission/simple/',views.PermissionListView.as_view()),
    path('permission/groups/simple/',views.GroupsList.as_view()),

]

urlpatterns += router.urls
