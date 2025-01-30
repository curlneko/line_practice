import os
import re
import boto3
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, PostbackAction
from datetime import datetime
import uuid

# DynamoDBクライアント
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))

# 環境変数からLINEの設定を取得
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

# 正しい試験名のフォーマット（yyyy-mm-dd）
exam_name_pattern = re.compile(r"^[\w\sぁ-んァ-ン一-龥々ー]+:\d{4}-\d{2}-\d{2}$")

def lambda_handler(event, context):
    print(event)
    print(context)

    try:
        # LINEのイベント情報を取得
        line_events = event.get("events", [])

        for e in line_events:
            # メッセージイベント
            if e["type"] == "message" and e["message"]["type"] == "text":
                user_message = e["message"]["text"]
                reply_token = e["replyToken"]

                # 「試験登録」の場合
                if user_message == "試験登録":
                    print("試験登録")
                    reply_message = TextSendMessage(text="試験名:yyyy-mm-ddで登録してください。")
                    line_bot_api.reply_message(reply_token, reply_message)

                # 「試験名：yyyy-mm-dd」の形式の場合
                elif exam_name_pattern.match(user_message):
                    print("試験名：yyyy-mm-dd")
                    exam_name, exam_date = user_message.split(":")
                    try:
                        # DynamoDBに試験を登録
                        table.put_item(
                            Item={
                                'id': str(uuid.uuid4()),  # UUIDをパーティションキーとして設定
                                'name': exam_name.strip(),
                                'date': exam_date.strip(),
                                'created_at': datetime.now().isoformat()
                            }
                        )
                        reply_message = TextSendMessage(text="登録しました")
                    except Exception as e:
                        reply_message = TextSendMessage(text="登録に失敗しました。もう一度試してください。")
                    # reply_message = TextSendMessage(text="登録しました")
                    line_bot_api.reply_message(reply_token, reply_message)

                # 「試験一覧」の場合
                elif user_message == "試験一覧":
                    print("試験一覧")
                    # DynamoDBから試験一覧を取得
                    response = table.scan()
                    exams = response.get('Items', [])
                    if exams:
                        exam_list = "\n".join([f"{exam['name']} : {exam['date']}" for exam in exams])
                        reply_message = TextSendMessage(text=f"登録された試験一覧:\n{exam_list}")
                    else:
                        reply_message = TextSendMessage(text="まだ試験は登録されていません。")
                    # reply_message = TextSendMessage(text="まだ試験は登録されていません。")
                    line_bot_api.reply_message(reply_token, reply_message)

                # 上記以外のメッセージの場合
                else:
                    print("上記以外のメッセージの場合")
                    buttons_template = ButtonsTemplate(
                        title="選択してください",
                        text="試験登録または試験一覧を選んでください",
                        actions=[
                            PostbackAction(label="試験登録", data="action=register"),
                            PostbackAction(label="試験一覧", data="action=list")
                        ]
                    )
                    reply_message = TemplateSendMessage(alt_text="試験登録 or 試験一覧", template=buttons_template)
                    line_bot_api.reply_message(reply_token, reply_message)

        # Postbackイベントの処理
        for e in line_events:
            if e["type"] == "postback":
                postback_data = e["postback"]["data"]
                reply_token = e["replyToken"]

                if postback_data == "action=register":
                    reply_message = TextSendMessage(text="試験名:yyyy-mm-ddで登録してください。")
                    line_bot_api.reply_message(reply_token, reply_message)
                elif postback_data == "action=list":
                    # DynamoDBから試験一覧を取得
                    response = table.scan()
                    exams = response.get('Items', [])
                    if exams:
                        exam_list = "\n".join([f"{exam['name']} : {exam['date']}" for exam in exams])
                        reply_message = TextSendMessage(text=f"登録された試験一覧:\n{exam_list}")
                    else:
                        reply_message = TextSendMessage(text="まだ試験は登録されていません。")
                    # reply_message = TextSendMessage(text="まだ試験は登録されていません。")
                    line_bot_api.reply_message(reply_token, reply_message)

        return {"statusCode": 200, "body": "OK"}

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": str(e)}

