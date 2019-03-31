from celery import Celery


celery_app = Celery("meiduo")  # 创建celery对象，取名为meiduo

# 导入配置文件
celery_app.config_from_object('celery_tasks.config')

# 自动注册celery任务
celery_app.autodiscover_tasks(['celery_tasks.sms'])