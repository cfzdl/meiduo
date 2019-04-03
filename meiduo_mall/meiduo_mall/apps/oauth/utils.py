from django.conf import settings
from urllib.parse import urlencode
from urllib.parse import urlencode, parse_qs
from urllib.request import urlopen
import logging

from .exceptions import QQAPIException

logger = logging.getLogger('django')

class OAuthQQ(object):
    """
    用户qq登陆的工具
    提供了qq可能使用的方法
    """
    def __init__(self, app_id=None, app_key=None, redirect_url=None, state=None):
        self.app_id = app_id
        self.app_key = app_key
        self.redirect_url = redirect_url
        self.state = state

    def generate_qq_login_url(self):
        """
        拼接qq登陆的地址
        返回链接地址
        """
        url = 'https://graph.qq.com/oauth2.0/authorize?'
        data = {
            'response_type': 'code',
            'client_id': self.app_id,
            'redirect_yrl': self.redirect_url,
            'state': self.state,
            'scope': 'get_user_info',  # 获取用户的信息
        }
        quert_string = urlencode(data)
        url += quert_string

        return url


    def get_access_token(self, code):
        "获取access_token"
        url = 'https://graph.qq.com/oauth2.0/token?'
        req_data = {
            'grant_type': 'authorization_code',
            'client_id': self.app_id,
            'client_secret': self.app_key,
            'code': code,
            'redirect_uri': self.redirect_url
        }
        url += urlencode(req_data)

        try:
            # 发送请求
            response = urlopen(url)
            # 读取QQ返回的响应体数据

            response = response.read().decode()

            # 将返回的数据转换为字典
            resp_dict = parse_qs(response)

            access_token = resp_dict.get("access_token")[0]
        except Exception as e:
            logger.error(e)
            raise QQAPIException('获取access_token异常')

        return access_token

    def get_openid(self, access_token):
        """
        获取openid
        :param access_token:
        :return:
        """
        url = 'https://graph.qq.com/oauth2.0/me?access_token=' + access_token

        try:
            response = urlopen(url)
            response_data = response.read().decode()  # 返回的response 是HttpResponse对象，read后是bytes，decode 后是json
            data = response_data.loads(response_data[10:-4])
        except Exception:
            data = parse_qs(response_data)
            logger.error('code=%s msg=%s' % (data.get('code'), data.get('msg')))
            raise QQAPIException('获取openid异常')

        openid = data.get('openid', None)
        return openid
