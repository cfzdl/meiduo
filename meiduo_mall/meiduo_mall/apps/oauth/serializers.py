from rest_framework import serializers
from django_redis import get_redis_connection

from .models import OAuthQQUser
from users.models import User

class  OAuthQQUserSerializer(serializers.Serializer):
    """
       QQ登录创建用户序列化器
       """
    access_token = serializers.CharField(label='操作凭证')
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
    password = serializers.CharField(label='密码', max_length=20, min_length=8)
    sms_code = serializers.CharField(label='短信验证码')


    def validate(self, data):
        """验证qq数据"""

        access_token = data['access_token']
        openid = OAuthQQUser.check_save_user_token(access_token)

        if not openid:
            raise serializers.ValidationError("无效的access_token")

        data["openid"]=openid

        # 验证短信验证码
        mobile = data["mobile"]
        sms_code = data["sms_data"]
        redis_conn = get_redis_connection('verify_codes')
        real_sms_code = redis_conn.get('sms_%s' % mobile)

        if sms_code != real_sms_code:
            raise serializers.ValidationError("无效的短信验证码")

        # 如果用户存在， 检查用户密码
        try:
            user = User.objects.get(mobile=mobile)

        except User.DoesNotExist:
            pass

        else:
            password = data["password"]
            if not user.check_password(password):
                raise serializers.ValidationError("用户密码不正确")
            data['user'] = user

        return data


    def create(self, validated_data):

        user = validated_data.get("user")

        if not user:
            # 用户不存在
            user = User.objects.create_user(
                username=validated_data['mobile'],
                password=validated_data['password'],
                mobile=validated_data['mobile'],
            )

            # 和qq用户关联
            OAuthQQUser.objects.create_user(
                openid = validated_data.get('openid'),
                user = validated_data.get('user'),
            )

            return user
