from flask import Flask, request
import requests

app = Flask(__name__)

BOT_TOKEN = '7746984055:AAHSetP4wdcVPp1kcbs0p3pYNNqPDM1tty0'
URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

@app.route('/', methods=['POST'])
def webhook():
    data = request.json
    chat_id = data['message']['chat']['id']
    text = data['message'].get('text', '')

    # Resposta inicial
    msg = f"Recebi: {text}\nEstou validando suas informações..."
    requests.post(URL, json={
        "chat_id": chat_id,
        "text": msg
    })

    return '', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81)
