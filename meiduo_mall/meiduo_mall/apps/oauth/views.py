from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_jwt.settings import api_settings

from .utils import OAuthQQ
from .exceptions import QQAPIException
from .models import OAuthQQUser
from .serializers import OAuthQQUserSerializer

# Create your views here.


class OAuthQQURLView(APIView):
    """
        提供QQ登录的网址
        前端请求的接口网址  /oauth/qq/authorization/?state=xxxxxxx
        state参数是由前端传递，参数值为在QQ登录成功后，我们后端把用户引导到哪个美多商城页面
    """
    def get(self, request):
        # 提取state参数
        state = request.query_params.get('state')
        if not state:
            state = '/'  # 如果前端没有传来state数据，我们自己给他定义到主页

        # 按照qq的说明文档， 拼接用户的qq登陆地址
        oauth_qq = OAuthQQ(state=state)
        login_url = oauth_qq.generate_qq_login_url()

        # 返回链接
        return Response


class OAuthQQUserView(APIView):
    """
    获取qq用户对应的账户信息
    """
    parser_classes = OAuthQQUserSerializer

    def get(self, request):

        #  获取code
        code = request.query_params.get('code')
        if not code:
            return Response({'message': "code不存在"}, status=status.HTTP_404_NOT_FOUND)

        #发送code获得access——token
        oauth_qq = OAuthQQ()

        try:

            access_token = oauth_qq.get_access_token(code)

            # 获得access_token 获得openid
            openid = oauth_qq.get_openid(access_token)
        except QQAPIException:
            return Response({'message': 'QQ获取openid异常'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


        try:
            oauth_user = OAuthQQUser.objects.get(openid=openid)
        except  OAuthQQUser.DoesNotExist:
            # 没绑定，返回用来绑定身份的ACCESS_TOKEN，返回
            access_token = OAuthQQUser.generate_save_user_token(openid)
            return Response({'access_token': access_token})

        else:
            # 如果用户绑定了，直接登陆凭证JWT
            user = oauth_user.user

            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            return Response({
                'token': token,
                'username': user.username,
                'user_id': user.id
            })


    def post(self, request):

        # 调用序列化器检查对象
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 保存用户对象与openid的对应关系
        user = serializer.save()

        # 返回用户登录成功的JWT token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        return Response({
            'token': token,
            'username': user.username,
            'user_id': user.id
        })