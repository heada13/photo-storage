# from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError,LineBotApiError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from linebot.models.messages import ImageMessage

import logging
import sys
from datetime import datetime
import os
import boto3

# app = Flask(__name__)

logger = logging.getLogger()
logger.setLevel(logging.ERROR)

chanel_secret = os.getenv('CANEL_SECRET',None)
chanel_access_token = os.getenv('CHANEL_ACCESS_TOKEN',None)

if chanel_secret is None:
    logger.error('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if chanel_access_token is None:
    logger.error('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(chanel_access_token)
handler = WebhookHandler(chanel_secret)

# @app.route("/")
# def tset():
#   return "ok"

# @app.route("/callback", methods=['POST'])
# def callback():
#     # get X-Line-Signature header value
#     signature = request.headers['X-Line-Signature']

#     # get request body as text
#     body = request.get_data(as_text=True)
#     app.logger.info("Request body: " + body)

#     # handle webhook body
#     try:
#         handler.handle(body, signature)
#     except InvalidSignatureError:
#         print("Invalid signature. Please check your channel access token/channel secret.")
#         abort(400)

#     return 'OK'


# users = {}
s3 = boto3.client("s3")
bucket = "photo-storage-s3-hashimoto"

def lambda_handler(event,context):
    signature = event["headers"]["x-line-signature"]
    body = event["body"]

    # リターン値の設定
    ok_json = {"isBase64Encoded": False,
               "statusCode": 200,
               "headers": {},
               "body": ""}

    error_json = {"isBase64Encoded": False,
                  "statusCode": 403,
                  "headers": {},
                  "body": "Error"}

    @handler.add(MessageEvent, message=ImageMessage)
    def handle_message(event):
        
        message_id = event.message.id
        message_content = line_bot_api.get_message_content(message_id)
        content = bytes()
        for chunk in message_content.iter_content():
            content += chunk
        
        key = datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + '.png'
        s3.put_object(Bucket=bucket, Key=key, Body=content)

        # 画像保存するとメッセージの返信
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text='写真の保存に成功!'))

    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        logger.error("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            logger.error("  %s: %s" % (m.property, m.message))
        return error_json
    except InvalidSignatureError:
        return error_json

    return ok_json

        

# if __name__ == "__main__":
#     app.run()
