# main.py
from flask import Flask, request
from handlers.message_handler import handle_message

app = Flask(__name__)

@app.route('/', methods=['POST'])
def webhook():
    data = request.json

    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_message = data["message"]["text"]

        handle_message(chat_id, user_message)

    return {"ok": True}

if __name__ == '__main__':
    app.run(debug=True)

