from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import mixins
import re

from . import serializers
from verifications.serializers import CheckImageCodeSerializers
from .models import User
from .utils import get_user_by_account


class UsernameCountView(APIView):
    """
    用户名数量
    """

    def post(self, request, username):
        """
        获取指定username数量
        :param request:
        :param username:
        :return:
        """

        count = User.objects.filter(username=username).count()

        data = {
            'username': username,
            'count': count,
        }

        return Response(data)


class MobileCountView(APIView):
    """
    手机号数量
    """

    def get(self, request, mobile):
        """
        获取指定手机号数量
        :param request:
        :param mobile:
        :return:
        """

        count = User.objects.filter(mobile=mobile).count()

        data = {
            'mobile': mobile,
            'count': count,
        }

        return Response(data)


class UserView(CreateAPIView):
    """
    用户注册
    """
    serializer_class = serializers.CreateUserSerializer


class SMSCodeTokenView(GenericAPIView):
    """
    获取发送短信验证码的凭据
    """
    serializer_class = CheckImageCodeSerializers

    def get(self, request, account):
        # 验证图片验证码
        serializers = self.get_serializer(data=request.query_params)
        serializers.is_valid(raise_exception=True)

        # 根据account 查询user
        user = get_user_by_account(account)
        if user is None:
            return Response({'message': '用户不存在'}, status= status.HTTP_404_NOT_FOUND)

        # 根据user生成对应的access_token
        access_token = user.generate_send_sms_code_token()

        # 修改手机号
        mobile = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', user.mobile)

        # 返回tokrn
        return Response({
            'mobile': mobile,
            'access_token': access_token,
        })


class PasswordTokenView(GenericAPIView):
    """
    用户帐号设置密码的token
    """
    serializer_class = serializers.CheckSMSCodeSerializer

    def get(self, request, account):
        """
        根据用户帐号获取修改密码的token
        """
        # 校验短信验证码
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        user = serializer.user

        # 生成修改用户密码的access token
        access_token = user.generate_set_password_token()

        return Response({'user_id': user.id, 'access_token': access_token})



class PasswordView(mixins.UpdateModelMixin, GenericAPIView):
    """
    用户密码
    """
    queryset = User.objects.all()
    serializer_class = serializers.ResetPasswordSerializer

    def post(self, request, pk):
        return self.update(request, pk)