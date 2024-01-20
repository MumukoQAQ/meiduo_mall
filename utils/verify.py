from PIL import Image, ImageDraw, ImageFont
import random
import string
import json
import io


def generate_code(code_length=5):
    # Create a new image with a white background
    width, height = 120, 50
    image = Image.new('RGB', (width, height), (255, 255, 255))

    # Create a draw object to draw on the image
    draw = ImageDraw.Draw(image)

    # Create a font object
    font = ImageFont.truetype('AGENCYR.TTF', 36)

    # Create a random code
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=code_length))

    # Draw the code on the image
    for i, c in enumerate(code):
        draw.text((10 + i * 20, 10), c, fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)),
                  font=font)

    # Add some random noise lines
    for i in range(0, random.randint(1, 5)):
        draw.line([(random.randint(0, width), random.randint(0, height)),
                   (random.randint(0, width), random.randint(0, height))],
                  fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')  # 确保保存格式与 content_type 匹配
    img_byte_arr = img_byte_arr.getvalue()
    return code, img_byte_arr


# 短信发送
from ronglian_sms_sdk import SmsSDK

accId = ''
accToken = ''
appId = ''


def send_message(mobile, sms_code):
    sdk = SmsSDK(accId, accToken, appId)
    tid = '1'  # 模板参数
    datas = (f'{sms_code}', '5')
    resp = sdk.sendMessage(tid, mobile, datas)
    response = json.loads(resp)
    if response['statusCode'] == "000000":
        return True
    return False


# 邮件发送
from meiduo_mall import settings
from django.core.mail import send_mail


def sendAVerificationEmail(email,token):
    verify_url = 'http://meiduo:8080/success_verify_email.html?token=%s'%token
    subject = "美多商城邮箱验证"
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用美多商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)
    try:
        send_mail(subject=subject,
                  from_email=settings.EMAIL_FROM,
                  message='',
                  recipient_list=[email],
                  html_message=html_message)
    except Exception as e:
        pass

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

def generateTokens(data):
    serializer = Serializer(settings.SECRET_KEY,expires_in=180)
    token = serializer.dumps(data)
    return token.decode()

def decryptTheToken(token):
    serializer = Serializer(settings.SECRET_KEY)
    data = serializer.loads(token)
    return data

