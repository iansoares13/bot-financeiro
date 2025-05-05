# main.py
import os
import openai
from flask import Flask, request
from dotenv import load_dotenv
import requests

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

openai.api_key = OPENAI_API_KEY

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

@app.route('/', methods=['POST'])
def webhook():
    data = request.json

    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"].get("id")
        user_message = data["message"].get("text")

        try:
            # Envia mensagem para o ChatGPT
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um assistente financeiro pessoal."},
                    {"role": "user", "content": user_message},
                ]
            )
            reply = response["choices"][0]["message"]["content"]
        except Exception as e:
            reply = f"Erro ao consultar o ChatGPT: {e}"

        send_message(chat_id, f"Recebi: {user_message}\n{reply}")

    return {"ok": True}

if __name__ == '__main__':
    app.run(debug=True)
