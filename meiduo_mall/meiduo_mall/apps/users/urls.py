from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token

from . import views

urlpatterns = [
    url(r'usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
    url(r'mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
    url(r'^users/', views.UserView.as_view()),
    url(r'^authorizations/$', obtain_jwt_token),
    url(r'^accounts/(?P<account>\w{4,20})/sms/token/$', views.SMSCodeTokenView.as_view()),  # 获取发送短信验证码的token
    url(r'^accounts/(?P<account>\w{4,20})/password/token/$', views.PasswordTokenView.as_view()),  # 获取修改密码的token
    url(r'users/(?P<pk>\d+)/password/$', views.PasswordView.as_view()),  # 重置密码


]