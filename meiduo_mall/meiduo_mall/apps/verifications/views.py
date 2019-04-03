from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView
from django_redis import get_redis_connection
from django.http.response import HttpResponse
import random
from rest_framework.response import Response
from rest_framework import status

from meiduo_mall.libs.captcha.captcha import captcha
from . import constants
from . import serializers
from users.models import User
from meiduo_mall.libs.yuntongxun.sms import CCP
from celery_tasks.sms.tasks import send_sms_code




class ImageCodeView(APIView):
    """图片验证码"""

    def get(self, request, image_code_id):

        # 生成验证码图片
        text, image = captcha.generate_captcha()

        # 保存真实值到redis中
        redis_conn = get_redis_connection("verify_codes")
        redis_conn.setex('img_%s' % image_code_id,  constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # 返回图片
        return HttpResponse(image, content_type='images/jpg')

# class ImageCodeView(APIView):
#     """
#     图片验证码
#     """
#
#     def get(self, request, image_code_id):
#
#         # 生成验证码图片
#         name, text, image = captcha.generate_captcha()
#
#         # 获取redis连接对象
#         redis_conn = get_redis_connection("verify_codes")
#         redis_conn.setex("img_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
#
#         return  HttpResponse(image, content_type='image/jpeg')


class SMSCodeView(GenericAPIView):


    serializer_class = serializers.CheckImageCodeSerializers

    def get(self, request, mobile):

        serializers = self.get_serializer(data=request.query_params)
        serializers.is_valid(raise_exception=True)

        # redis_conn = get_redis_connection("verify_codes")
        # send_flag = redis_conn.get('send_flag_%s' % mobile)

        # if send_flag:
        #     return Response({'message': '发送短信过于频繁'}, status=status.HTTP_400_BAD_REQUEST)

        # 校验通过
        # 生成短信验证码
        sms_code = '%06d' % random.randint(0, 999999)

        # 保存验证码及发送记录
        redis_conn = get_redis_connection("verify_codes")

        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # redis_conn.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 使用redis中的pipeline一次执行多个命令
        pl = redis_conn.pipeline()

        # pl 收集命令
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 执行命令
        pl.execute()

        # 发送短信
        ccp = CCP()
        time = str(constants.SMS_CODE_REDIS_EXPIRES // 60)
        ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_CODE_TEMP_ID)

        # 使用celery完成异步任务
        # send_sms_code.delay(mobile, sms_code)

        return Response({'message': 'ok'})



class SMSCodeByTokenView(APIView):
    """
    根据access_token发送短信
    """
    def get(self, request):
        # 获取,验证access_token
        access_token = request.query_params.get('access_token')
        if not access_token:
            return Response({'message': "缺少access_token"}, status=status.HTTP_400_BAD_REQUEST)

        # 获取手机号
        mobile = User.check_send_sms_code_token(access_token)
        if not mobile:
            return Response({'message': "无效access_token"}, status=status.HTTP_400_BAD_REQUEST)

        # 验证发送短信次数
        redis_conn = get_redis_connection('verify_codes')
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            return Response({'message': "验证短信过于频繁"}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        # 生成验证码
        # 发送短信
        sms_code = '%06d' % random.randint(0, 999999)

        # 保存验证码及发送记录
        redis_conn = get_redis_connection("verify_codes")

        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # redis_conn.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 使用redis中的pipeline一次执行多个命令
        pl = redis_conn.pipeline()

        # pl 收集命令
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 执行命令
        pl.execute()

        # 发送短信
        ccp = CCP()
        time = str(constants.SMS_CODE_REDIS_EXPIRES // 60)
        ccp.send_template_sms(mobile, [sms_code, time], constants.SMS_CODE_TEMP_ID)

        # 使用celery完成异步任务
        # send_sms_code.delay(mobile, sms_code)

        return Response({'message': 'ok'})
