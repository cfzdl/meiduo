from rest_framework import serializers
from django_redis import get_redis_connection
from redis.exceptions import RedisError
import logging

logger = logging.getLogger('djngo')


class CheckImageCodeSerializers(serializers.Serializer):
    """
    图片验证码校验序列化器
    """

    image_code_id = serializers.UUIDField()
    text = serializers.CharField(min_length=4, max_length=4)

    def validate(self, attrs):
        """校验数据是否正确"""
        image_code_id = attrs['image_code_id']
        text = attrs['text']

        #查询数据库中的数据
        redis_conn = get_redis_connection("verify_codes")
        real_image_code = redis_conn.get('img_%s' % image_code_id)

        if real_image_code is None:
            # 过期或不存在
            raise serializers.ValidationError('无效的图片验证码')

        # 删除redis中图片验证码，防止用户对同一个进行多次验证
        try:
            redis_conn.delete('img_%s' % image_code_id)

        except RedisError as e:
            logger.error(e)

        #对比
        real_image_code = real_image_code.decode()
        if real_image_code.lower() != text.lower():
            raise serializers.ValidationError("图片验证码错误！")

        # reids中保存发送短信的标志
        mobile = self.context['view'].kwargs['mobile']
        if mobile:
            send_flag = redis_conn.get('send_flag_%s' % mobile)
            if send_flag:
                raise serializers.ValidationError('发送短信过于频繁')

        return attrs


# class CheckSMSCodeSerializers(serializers.Serializer):
#
#     """
#     短信验证序列化器
#     """
#
#     def validate(self, attrs):
#
#         """验证60秒内是否发送过短信"""
#
#         redis_conn = get_redis_connection("verify_codes")
#         mobile = self.context['view'].kwargs['mobile']
#
#         send_flag = redis_conn.get('send_flag_%s' % mobile)
#
#         if send_flag:
#             raise serializers.ValidationError('发送短信过于频繁')
#
#         return attrs