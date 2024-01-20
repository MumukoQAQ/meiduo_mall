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
from .views import registrationChecks, userRegistration, ImageCodeView, \
    MobileCodeView, UserLoginView, UserInfoView, SetEmailView, VerifyEmailVIew, AddressView,BrowsingHistory

username = registrationChecks.as_view(
    {
        'get': 'checkTheUsername'
    }
)

phone = registrationChecks.as_view(
    {
        'get': 'checkPhoneNumber'
    }
)

get_user = registrationChecks.as_view(
    {
        'get': 'get_user'
    }
)

user_log = UserLoginView.as_view(
    {
        "post": "user_login",
        "delete": "user_logout",
    }
)

address_url = AddressView.as_view({
    "get": "get_address",
    "post": "post_address",
    "delete": "delete_address",
    "put": "edit_address",

})

edit_address = AddressView.as_view({
    "put": "put_title",
})

set_default = AddressView.as_view({
    "put": "set_default",
})


urlpatterns = [
    path('usernames/<username:username>/count/', username),
    path('mobiles/<mobile:mobile>/count/', phone),
    path('register/', userRegistration.as_view()),
    path('getuser/', get_user),

    path('image_codes/<uuid:uuid>/', ImageCodeView.as_view()),
    path('sms_codes/<mobile:mobile>/', MobileCodeView.as_view()),
    path('login/', user_log),
    path('logout/', user_log),


    path('info/', UserInfoView.as_view()),
    path('password/',UserInfoView.as_view()),

    path('emails/', SetEmailView.as_view()),
    path('emails/verification/', VerifyEmailVIew.as_view()),

    path('addresses/create/', address_url),
    path('addresses/', address_url),
    path('addresses/<int:id>/', address_url),
    path('addresses/<int:id>/title/', edit_address),
    path('addresses/<int:id>/default/', set_default),

    path('browse_histories/',BrowsingHistory.as_view()),

]
