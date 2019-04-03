import re
from django.contrib.auth.backends import ModelBackend

from .models import User


def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义jwt认证成功返回数据
    """
    return {
        'token': token,
        'user_id': user.id,
        'username': user.username
    }


def get_user_by_account(account):
    """
    根据账号信息，查找用户对象
    :param account: 可以是username， mobile
    :return: user, None
    """
    try:
        # 判断account是否是手机号
        if re.match(r'1[3-9]\d{9}$', account):
            # 根据手机号查询用户
            user = User.objects.get(mobile=account)
        else:
            # 根据用户名查询用户
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileAuthBackend(ModelBackend):
    """
    自定义认证方法的后端
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 根据username查询用户   username可以是用户名也可以是手机号
        user = get_user_by_account(username)
        #校验用户是否存在和密码是否正确
        if user is not None and user.check_password(password):

            return user