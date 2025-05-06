import re
from datetime import datetime, timedelta
from handlers.gpt_processor import classificar_com_gpt  # (criaremos depois)
from telegram import enviar_mensagem_telegram  # (criaremos em utils futuramente)

# Função principal chamada pelo main.py
def tratar_mensagem(user_message, chat_id):
    print(f"[INFO] Mensagem recebida: {user_message}")

    dados = {
        "valor": extrair_valor(user_message),
        "data": extrair_data(user_message),
        "descricao": extrair_descricao(user_message),
        "tipo": extrair_tipo(user_message),
        "parcelado": False,
        "n_parcelas": 1,
        "forma_pagamento": extrair_forma_pagamento(user_message)
    }

    # Verificar se tem indicativo de parcelamento
    if tem_indicativo_parcelamento(user_message):
        dados["parcelado"] = True
        dados["n_parcelas"] = extrair_n_parcelas(user_message)

    # Verifica campos obrigatórios
    campos_obrigatorios = ["valor", "descricao", "forma_pagamento"]
    pendentes = [campo for campo in campos_obrigatorios if not dados[campo]]

    if pendentes:
        enviar_mensagem_telegram(chat_id, f"Faltam dados obrigatórios: {', '.join(pendentes)}. Por favor, envie novamente.")
        return

    # Chama o GPT apenas quando tudo estiver ok
    json_classificado = classificar_com_gpt(dados)

    # Aqui você pode salvar, exibir resumo, ou pedir confirmação do usuário
    resposta_final = f"""
Resumo do lançamento:
🧾 {json_classificado['descricao']}
📆 {json_classificado['data']}
💰 R$ {json_classificado['valor']:.2f}
📂 {json_classificado['categoria']} > {json_classificado['subcategoria']}
"""

    enviar_mensagem_telegram(chat_id, resposta_final.strip())


# ---------- Funções auxiliares ----------

def extrair_valor(texto):
    match = re.search(r"(\d+[,.]?\d*)", texto)
    if match:
        return float(match.group(1).replace(",", "."))
    return None

def extrair_data(texto):
    hoje = datetime.today()
    if "ontem" in texto.lower():
        return (hoje - timedelta(days=1)).strftime("%Y-%m-%d")
    elif "hoje" in texto.lower():
        return hoje.strftime("%Y-%m-%d")
    elif match := re.search(r"dia (\d{1,2})", texto):
        dia = int(match.group(1))
        return hoje.replace(day=dia).strftime("%Y-%m-%d")
    return hoje.strftime("%Y-%m-%d")  # padrão

def extrair_descricao(texto):
    return texto  # por enquanto assume tudo como descrição

def extrair_tipo(texto):
    palavras_receita = ["recebi", "ganhei", "me mandaram", "depositaram"]
    if any(p in texto.lower() for p in palavras_receita):
        return "Receita"
    return "Despesa"

def extrair_forma_pagamento(texto):
    formas = ["cartão", "credito", "débito", "pix", "dinheiro"]
    for forma in formas:
        if forma in texto.lower():
            return forma.capitalize()
    return None

def tem_indicativo_parcelamento(texto):
    return "parcel" in texto.lower() or "x" in texto.lower()

def extrair_n_parcelas(texto):
    if match := re.search(r"(\d{1,2})x", texto.lower()):
        return int(match.group(1))
    elif match := re.search(r"parcelad[oa] em (\d{1,2})", texto.lower()):
        return int(match.group(1))
    return 1
