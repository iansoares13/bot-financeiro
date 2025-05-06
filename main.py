
import os
import openai
from flask import Flask, request
import requests
import json

app = Flask(__name__)

# Configurações
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Enviar mensagem de texto para o Telegram
def enviar_mensagem_telegram(chat_id, texto, botoes=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto}
    
    if botoes:
        payload["reply_markup"] = {
            "inline_keyboard": [[{"text": btn, "callback_data": btn} for btn in botoes]]
        }

    requests.post(url, json=payload)

# Rota principal
@app.route("/", methods=["POST"])
def receber_mensagem():
    data = request.get_json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        texto_usuario = data["message"].get("text", "")

        resposta = consultar_gpt(texto_usuario)

        if not resposta:
            enviar_mensagem_telegram(chat_id, "Houve um erro ao processar sua mensagem.")
            return "OK"

        # Verifica se tem campos faltando
        if resposta.get("faltando"):
            faltam = ", ".join(resposta["faltando"])
            enviar_mensagem_telegram(chat_id, f"Faltam as seguintes informações: {faltam}. Por favor, envie os dados.")
        else:
            resumo = (
                f"Resumo do lançamento:\n"
                f"Descrição: {resposta['descricao']}\n"
                f"Data: {resposta['data']}\n"
                f"Valor: R$ {resposta['valor']:.2f}\n"
                f"Categoria: {resposta['categoria']} > {resposta['subcategoria']}\n"
                f"Forma de pagamento: {resposta['forma_pagamento']}"
            )
            enviar_mensagem_telegram(chat_id, resumo, botoes=["✅ Confirmar Lançamento", "❌ Corrigir"])

    elif "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]
        resposta = data["callback_query"]["data"]
        if "Confirmar" in resposta:
            enviar_mensagem_telegram(chat_id, "Lançamento confirmado!")
        elif "Corrigir" in resposta:
            enviar_mensagem_telegram(chat_id, "Ok! Envie novamente os dados corrigidos.")

    return "OK"

# Envia a frase para o GPT e retorna o JSON interpretado
def consultar_gpt(frase):
    prompt = (
        "Você é um interpretador financeiro inteligente. "
        "Analise a seguinte frase em linguagem natural e retorne um JSON com os seguintes campos:\n"
        "- tipo (valores possíveis: 'Receita' ou 'Despesa')\n"
        "- data (formato: 'AAAA-MM-DD')\n"
        "- valor (número decimal, ex: 150.75)\n"
        "- categoria\n"
        "- subcategoria\n"
        "- forma_pagamento\n"
        "- descricao (curta e clara)\n\n"
        "Se alguma informação obrigatória estiver ausente, devolva um campo adicional chamado 'faltando', com uma lista contendo os nomes dos campos faltantes.\n\n"
        f"Frase: {frase}"
    )

    try:
        resposta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        conteudo = resposta.choices[0].message.content
        return json.loads(conteudo)
    except Exception as e:
        print(f"[ERRO] GPT: {e}")
        return None

# Iniciar app Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
