import flask     
from flask import request
import requests
from openai import OpenAI
import os

app = flask.Flask(__name__)

auth_token = os.getenv('auth_token')
YouruserID = os.getenv('USER_ID')

print("AUTH_TOKEN:", auth_token)
print("USER_ID:", YouruserID)

# 初始化 OpenAI 客戶端
client = OpenAI()

# 儲存每個使用者的對話歷史
user_conversations = {}

def aichat(user_id, msg):
    global user_conversations

    # 確認使用者是否已有對話記錄，若無則初始化
    if user_id not in user_conversations:
        user_conversations[user_id] = [{"role": "system", "content": "請用繁體中文回答"}, 
                                       {"role": "system", "content": "你是承太郎, 請用嚴厲的語氣, 性格叛逆，口頭禪是'Yare Yare Daze', 絕招是'歐拉歐拉歐拉~', 替身使者是白金之星"}]

    # 將新的使用者訊息添加到對話中
    user_conversations[user_id].append({"role": "user", "content": msg})

    # 發送請求給 OpenAI
    completion = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=user_conversations[user_id]
    )

    # 獲取 AI 的回應
    ai_msg = completion.choices[0].message.content

    # 將 AI 的回應添加到對話中
    user_conversations[user_id].append({"role": "assistant", "content": ai_msg})

    # 若對話紀錄超過10筆，刪除最舊的兩筆
    if len(user_conversations[user_id]) > 10:
        del user_conversations[user_id][2:4]

    return ai_msg

# 將 AI 回應的訊息傳到 Line
def LineText(replyToken, str1):
    global auth_token
    global YouruserID

    message = {
        "replyToken": replyToken,
        "messages": [
            {
                "type": "text",
                "text": str1,
            }
        ]
    }

    hed = {'Authorization': 'Bearer ' + auth_token}
    url = 'https://api.line.me/v2/bot/message/reply'
    response = requests.post(url, json=message, headers=hed)
    return ""

# 接收 Line 的 POST 請求，將輸入的訊息回傳給 AI
@app.route("/", methods=['POST'])
def LinePOST():
    data = request.json

    replyToken = data['events'][0]['replyToken']  # 代幣
    text = data['events'][0]['message']['text']  # 訊息內容
    user_id = data['events'][0]['source']['userId']  # 使用者 ID
    ai_msg = aichat(user_id, text)
    print(f'user:{text}')
    print(f'ai:{ai_msg}')
    LineText(replyToken, ai_msg)
    return ""

@app.route("/", methods=['GET'])
def get_handler():
    return "This is a GET response"

@app.route("/", methods=['HEAD'])
def head_handler():
    return "", 200


if __name__ == '__main__':
    app.run(port=5000)