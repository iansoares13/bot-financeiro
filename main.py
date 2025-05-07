import os
import openai
from flask import Flask, request
import requests
import json
from datetime import datetime

app = Flask(__name__)

# Configurações
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Banco temporário para armazenar os JSONs por chat_id
dados_temp = {}

# Enviar mensagem para o Telegram
def enviar_mensagem_telegram(chat_id, texto, botoes=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": texto, "parse_mode": "Markdown"}
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

        if chat_id in dados_temp:
            json_antigo = dados_temp[chat_id]
            resposta = consultar_gpt_corrigido(json_antigo, texto_usuario)
        else:
            resposta = consultar_gpt(texto_usuario)

        if not resposta:
            enviar_mensagem_telegram(chat_id, "Houve um erro ao processar sua mensagem.")
            return "OK"

        if resposta.get("faltando"):
            dados_temp[chat_id] = resposta
            faltam = ", ".join(resposta["faltando"])
            enviar_mensagem_telegram(chat_id, f"Faltam as seguintes informações: {faltam}. Por favor, envie apenas essas informações.")
        else:
            dados_temp[chat_id] = resposta
            resumo = (
                f"Resumo do lançamento:\n"
                f"📅 *Data:* {resposta['data']}\n"
                f"💸 *Tipo:* {resposta['tipo']}\n"
                f"R$ *Valor:* {resposta['valor']}\n"
                f"💳 *Pagamento:* {resposta['forma_pagamento']}\n"
                f"📂 *Categoria:* {resposta['categoria']} > {resposta['subcategoria']}\n"
                f"📝 *Descrição:* {resposta['descricao']}"
            )
            enviar_mensagem_telegram(chat_id, resumo, botoes=["✅ Confirmar Lançamento", "❌ Corrigir"])

    elif "callback_query" in data:
        chat_id = data["callback_query"]["message"]["chat"]["id"]
        resposta = data["callback_query"]["data"]
        if "Confirmar" in resposta:
            enviar_mensagem_telegram(chat_id, "✅ Lançamento confirmado!")
            dados_temp.pop(chat_id, None)
        elif "Corrigir" in resposta:
            enviar_mensagem_telegram(chat_id, "✏️ Ok! Envie apenas o que deseja corrigir.")
    
    return "OK"

# GPT - NOVO LANÇAMENTO
def consultar_gpt(frase):
    prompt = gerar_prompt(frase)
    try:
        resposta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        conteudo = resposta.choices[0].message.content
        return json.loads(conteudo)
    except Exception as e:
        print(f"[ERRO] GPT: {e}")
        return None

# GPT - CORREÇÃO
def consultar_gpt_corrigido(json_antigo, frase_corrigida):
    prompt = f"""Você é um interpretador financeiro inteligente. 
Você receberá um JSON anterior e uma frase complementar. Atualize o JSON, mantendo tudo o que não foi alterado. 
Se a frase corrigir ou adicionar alguma informação, ajuste os campos correspondentes mantendo os demais.

Formato da data: DD/MM/AAAA

JSON anterior:
{json.dumps(json_antigo, ensure_ascii=False, indent=2)}

Frase: {frase_corrigida}
"""
    try:
        resposta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        conteudo = resposta.choices[0].message.content
        return json.loads(conteudo)
    except Exception as e:
        print(f"[ERRO CORREÇÃO] GPT: {e}")
        return None

# Prompt original estruturado
def gerar_prompt(frase):
    return f"""Você é um interpretador financeiro inteligente. Analise a seguinte frase em linguagem natural e retorne um JSON com os seguintes campos, nesta ordem:

1. data (formato: "DD/MM/AAAA")
2. tipo (valores possíveis: "Receita", "Despesa" ou "Investimentos")
3. valor (como número decimal com vírgula, ex: 150,75)
4. forma_pagamento (valores possíveis: "Pix", "Crédito", "Débito", "Flash", "Dinheiro", "Outro")
5. categoria (usar apenas as categorias da lista fornecida abaixo)
6. subcategoria (usar apenas as subcategorias da respectiva categoria)
7. descricao (curta e clara, com base na frase original)

Se alguma informação obrigatória estiver ausente, adicione no JSON um campo extra chamado "faltando", com uma lista dos nomes dos campos ausentes.

Use somente as seguintes categorias e subcategorias:

Receitas:
- Salário
- Flash / VA / VR
- Diárias de Viagem (LINCE)
- Reembolso de Viagem (LINCE)
- Transferências / Pix de Outros
- Outros

Despesas:
- Moradia
  - Aluguel / Financiamento
  - Condomínio
  - IPTU
  - Luz
  - Água
  - Gás
  - Telefone Celular
  - Internet
  - Serviços / Manutenção
  - Itens para Casa
  - Seguro Residencial
  - Outros
- Transporte
  - Seguro
  - IPVA
  - Combustível
  - Metrô / Ônibus
  - Uber / 99
  - Estacionamento
  - Pedágio
  - Manutenção / Revisão
  - Limpeza
  - Outros
- Alimentação
  - Mercado / Padaria
  - Restaurante
  - Ifood
  - Outros
- Saúde
  - Farmácia
  - Plano de Saúde
  - Academia / Esportes
  - Consultas / Exames
  - Psicólogo / Terapia
  - Suplementos
  - Dentista Particular
  - Outros
- Pets
  - Plano de Saúde Pets
  - Ração
  - Areia Higiênica
  - Brinquedos / Utensílios
  - Consultas / Exames / Vacinas
  - Outros
- Cuidados Pessoais
  - Barbeiro / Salão
  - Roupa / Tênis / Acessórios
  - Outros
- Lazer
  - Ingressos (Cinema / Shows / Festas / Jogos)
  - Viagens / Turismo
  - Outros
- Assinaturas
  - Netflix
  - Amazon Prime Video
  - Disney+
  - Globoplay + Premier
  - Max
  - Paramount+
  - NBA League Pass
  - Ifood Clube
  - Livelo
  - Azul
  - Smiles
  - Wine
  - Chatgpt
  - Mantiqueira (Ovos)
  - Outros
- Aleatórios
  - Presentes
  - Outros

Investimentos:
- Depósitos Mensais
  - Fundo de Emergência
  - Fundos Imobiliários / Ações
  - Opções
  - Renda Fixa
  - Planos com Mozão

Regras:
- Nunca invente novas categorias. Nunca invente novas subcategorias.
- Se não conseguir classificar com precisão a subcategoria, use "Outros" da categoria correspondente.
- Se não conseguir classificar nenhuma categoria, use a categoria "Aleatórios".
- Se a frase contiver “ontem”, “hoje” ou datas como “dia 02/04”, converta isso para o formato “DD/MM/AAAA”.
- Se a data estiver ausente, use a data atual.
- Sempre retorne os campos no idioma português, mesmo que a frase esteja em inglês.
- "Flash" é o nome do cartão do Vale Alimentação que recebemos. Então podemos ter recebido o saldo depositado no flash como receita, ou também podemos utilizar ele para pagar comida no mercado ou restaurante. Se atente se é receita ou despesa.
- A resposta deve ser um JSON puro, sem explicações ou comentários.

Frase: {frase}
Data atual: {data_hoje}
"""

# Iniciar app Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
