from celery_tasks.main import celery_app
from utils.verify import send_message
import logging
logger = logging.getLogger('django')

# name：异步任务别名
@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    """
    发送短信异步任务
    :param mobile: 手机号
    :param sms_code: 短信验证码
    """
    try:
        send_ret = send_message(mobile,sms_code)
        return send_ret
    except Exception as e:
        logger.error(e)