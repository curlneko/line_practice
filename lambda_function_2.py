import os
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 環境変数から設定を取得
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

def lambda_handler(event, context):
    try:
        print(event)
        print(context)

        # LINEのイベント情報を直接取得
        line_events = event.get("events", [])

        for e in line_events:
            # メッセージイベントの場合のみ処理
            if e["type"] == "message" and e["message"]["type"] == "text":
                reply_token = e["replyToken"]
                user_message = e["message"]["text"]

                # 返信メッセージ作成
                reply_message = TextSendMessage(text=f"あなたのメッセージ: {user_message}")
                line_bot_api.reply_message(reply_token, reply_message)

        return {"statusCode": 200, "body": "OK"}

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"statusCode": 500, "body": str(e)}

