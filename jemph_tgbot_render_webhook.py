import requests
import string
import random

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from io import BytesIO

app = FastAPI()

# Enable CORS support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

message_array = {}
BOT_TOKEN = "token here"
        
class Update(BaseModel):
    update_id: int
    message: dict

def id_generator(size=16, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def add_message(user_id, message, role):
    message_array[user_id].append({"role": role, "content": message})
    
def process_message(user_id, message):
	# code here
	pass

@app.post("/webhook")
async def telegram_webhook(update: Update):
    message = update.message
    chat_id = message["chat"]["id"]
    user_id = message["from"]["id"]
    message_id = message["message_id"]
    
    if "document" in message:
        document = message["document"]
        file_id = document["file_id"]

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile"
        params = {
            "file_id": file_id
        }
        response = requests.get(url, params=params)
        file_path = response.json()["result"]["file_path"]

        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        file_response = requests.get(file_url)
        
        response = process_message(user_id, file_response.text)
        
        w_document_io = BytesIO(response.encode('utf-8'))
        w_document_io.seek(0)
        send_document(chat_id, w_document_io, reply_to_message_id=message_id)
    elif "audio" in message:
        audio = message["audio"]
        file_id = audio["file_id"]
        send_message(chat_id, "Audio is not supported.", reply_to_message_id=message_id)
    elif "text" in message:
        text = message["text"]
        if "/start" in text:
            send_message(chat_id, "Hi There! Thanks for using Jaigen LITE.", reply_to_message_id=message_id)
        elif "/donate" in text:
            send_message(chat_id, "Support me via Ko-Fi: https://ko-fi.com/jemph", reply_to_message_id=message_id)
        elif "/clear" in text:
            global message_array
            message_array[user_id] = []
            send_message(chat_id, "Message History Cleared.", reply_to_message_id=message_id)
        else:
            response = process_message(user_id, text)
            if len(text) >= 4000:
                document_io = BytesIO(response.encode('utf-8'))
                document_io.seek(0)
                send_document(chat_id, document_io, reply_to_message_id=message_id)
            else:
                send_message(chat_id, response, reply_to_message_id=message_id)
    else:
        send_message(chat_id, "Your message is not supported.", reply_to_message_id=message_id)
    return {"status": "ok"}

def send_message(chat_id: int, text: str, reply_to_message_id=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "reply_to_message_id": reply_to_message_id,
        "parse_mode": "markdown"
    }
    response = requests.post(url, data=data)
    return response.json()

def send_document(chat_id: int, document, reply_to_message_id=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    files = {
        "document": ("result.txt", document)
    }
    data = {
        "chat_id": chat_id,
        "reply_to_message_id": reply_to_message_id
    }
    response = requests.post(url, files=files, data=data)
    return response.json()