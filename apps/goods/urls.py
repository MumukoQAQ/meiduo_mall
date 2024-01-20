"""meiduo_mall URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from .views import IndexView,GoodsListView,HotGoodsView,MySearchView,GoodsDetailiView

from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('index/', IndexView.as_view()),
    path('list/<int:id>/skus/', GoodsListView.as_view()),
    path('hot/<int:id>/', HotGoodsView.as_view()),
    path('search/', MySearchView()),
    # path('detail/visit/<int:id>/', GoodsDetailiView.as_view()),
    path('detail/visit/<int:group_id>/', csrf_exempt(GoodsDetailiView.as_view())),
]
