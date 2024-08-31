如果已經會使用python跟OPENAI聊天了
可以套用到line上, 以生活化及簡單的方式跟OPENAI聊天
並且可以創造個人特色的AI機器人

這裡使用Nogrk建立一個暫時的公有網址, 連接到私有ip
再將Nogrk產生的網址存到line message api
這樣就可以實現用line和AI對話囉~

### 建立Line機器人的聊天帳號
首先, 到line developers註冊或登入
https://developers.line.biz/zh-hant/
![image](https://hackmd.io/_uploads/r1HCJFJ30.png)


如果有line可以直接選擇line帳號登入(一般都會有吧?)
![image](https://hackmd.io/_uploads/ByEckF1nA.png =50%x)

創建Provider
![image](https://hackmd.io/_uploads/SkpFltJnR.png)
輸入Provider name => Create
![image](https://hackmd.io/_uploads/S1XeVBx3C.png =50%x)

選擇創建"Message API", 並依內容填寫
![image](https://hackmd.io/_uploads/HJMYVSeh0.png)
![image](https://hackmd.io/_uploads/BylhPPtk30.png)
![image](https://hackmd.io/_uploads/B1Dl_tyh0.png)

創建完成Message API後, 在Basic setting頁面, 下方有個Your user ID需要記下來
![image](https://hackmd.io/_uploads/rJsT5Y1nR.png)

![image](https://hackmd.io/_uploads/SJ3ciFJ3R.png =80%x)
然後再到Messaging API頁面, 掃描下面QRcode可以加入好友
![image](https://hackmd.io/_uploads/BkF5_qJ2C.png =80%x)

在Webhook setting這裡要輸入架設的openai網址
(我這裡是先將openai發佈到私有網域上, 再使用ngrok建立一個暫時的公有網址連接到私有網域)
點選Edit, 並點選開啟Use webhook
其他不用變更
![image](https://hackmd.io/_uploads/rkzj6FyhA.png)
再下方Channel access taken點選issue會出現一串字, 這個需要設定在openai的程式內, 可以點選旁的的小方框"複製"
![image](https://hackmd.io/_uploads/Sk4Xx9k3A.png)

接下來到line管理頁面, 停止系統自動回復功能
https://tw.linebiz.com/login/
![image](https://hackmd.io/_uploads/SkqfWrlhC.png)
選擇帳號
![image](https://hackmd.io/_uploads/SkOpZSl2R.png)
在左邊欄位選擇"自動回覆訊息", 在點選右邊內容的按鈕, 停止自動回覆
![image](https://hackmd.io/_uploads/BycKzBg30.png)
以上line部分就設置完成囉~

### 執行程式
第9~10行, auth_token和YouruserID為前面line messaging API的資訊, 複製後放在這裡
第21, 22行可以設AI角色, 有很多條件的話可以一直往後加, 或是寫在一起
※ 此聊天機器人沒有記錄訊息, 每次回應都是都是對當次的訊息回覆
```py=
import flask     
from flask import  request
import requests
from openai import OpenAI

app = flask.Flask(__name__)

# line環境變數
auth_token=*****
YouruserID=*****


# 初始化, 如果有設環境變數
client = OpenAI()

# 設定AI機器人
def aichat(msg):
    completion = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages = [
        {"role": "system", "content": "請用繁體中文回答"},    
        {"role": "system", "content": "你是承太郎, 請用嚴厲的語氣, 性格叛逆，口頭禪是'Yare Yare Daze', 絕招是'歐拉歐拉歐拉~', 替身使者是白金之星},    
        {"role": "user", "content": msg}    # 設定使用者訊息
        ]
    )
    # 將AI回應的訊息指派給ai_msg
    ai_msg= completion.choices[0].message.content

    # 顯示AI訊息
    print(ai_msg)    
    
    return ai_msg


# 將AI回應的訊息傳到line
def LineText(replyToken,str1):
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


# 接收 Line 的 POST 請求，將輸入的訊息回傳給AI
@app.route("/", methods=[ 'POST'])
def LinePOST():
    data = request.json
    replyToken = data['events'][0]['replyToken']  # 代幣
    text = data['events'][0]['message']['text']  # 訊息內容
    
    # 呼叫聊天機器人的函式, 並將回傳的訊息存到變數ai_msg
    ai_msg = aichat(text)    

    LineText(replyToken, ai_msg)
    return ""

if __name__ == '__main__':
    app.run(port=8080)
```

### 儲存聊天紀錄
如果想要保存之前聊天紀錄, 可以建立一個全域變數的list, 這個list用來保存所有對話訊息。每次接收到新的訊息後，並使用.append將每次聊天的紀錄加到這個list中，然後將整個list發送給 OpenAI。

```py=
import flask     
from flask import request
import requests
from openai import OpenAI

app = flask.Flask(__name__)

# Line 環境變數
auth_token = '*****"
YouruserID = "*****"

# 初始化 OpenAI 客戶端
client = OpenAI()

# 初始化對話列表
conversation = [{"role": "system", "content": "請用繁體中文回答"},
                {"role": "system", "content": "你是承太郎, 請用嚴厲的語氣, 性格叛逆，口頭禪是'Yare Yare Daze', 絕招是'歐拉歐拉歐拉~', 替身使者是白金之星}]

def aichat(msg):
    global conversation

    # 將訊息添加到對話中
    conversation.append({"role": "user", "content": msg})

    # 發送請求給 OpenAI
    completion = client.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=conversation
    )

    # 將AI 的回應指派給ai_msg
    ai_msg = completion.choices[0].message.content

    # 將 AI 的回應添加到對話中
    conversation.append({"role": "assistant", "content": ai_msg})

    print(ai_msg)
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
    ai_msg = aichat(text)

    LineText(replyToken, ai_msg)
    return ""

if __name__ == '__main__':
    app.run(port=8080)
```

### 儲存不同使用者的聊天訊息
上面程式可以儲存聊天紀錄了, 但是如果將私有ip發布公有網址上, 讓其他人也可以使用你的line聊天機器人, 這樣會有個問題, 因為建立了全域變數的list可以儲存聊天紀錄, 其他人一起使用的話聊天紀錄會混合在一起, 這會導致AI在回應時參考到不相關的訊息，結果可能會令人困惑。

因此修改為, 建立一個全域變數字典可以儲存每個使用者的聊天訊息, 以user_id 為key，這樣可以確保每個使用者的對話都是獨立的。

另外, 避免儲存訊息的全域變數資料量過大, 加入判斷式, 若對話紀錄超過10筆，使用刪除最舊的兩筆
(一次傳送及回應訊息是兩筆資料, 且第0和第1是我設定AI的訊息, 所以刪除第2~3筆資料)


```py=
import flask     
from flask import request
import requests
from openai import OpenAI

app = flask.Flask(__name__)

# Line 環境變數,  "*****"替換為自己的
auth_token="*****"
YouruserID="*****"

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

    print(ai_msg)
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
   
    LineText(replyToken, ai_msg)
    return ""

if __name__ == '__main__':
    app.run(port=8080)
```

### 來看看聊天結果
![image](https://hackmd.io/_uploads/Hy1BzLg3R.png =60%x)
