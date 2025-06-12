import os
import requests
from datetime import datetime

CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
EXCEL_FILE_NAME = "Controle Financeiro.xlsx"
EXCEL_FOLDER_NAME = "Planilhas Bot Financeiro"
EXCEL_WORKSHEET = "Dados de Lançamentos"

# Autentica e retorna o token de acesso
def obter_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": CLIENT_ID,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    resp = requests.post(url, headers=headers, data=data)
    return resp.json().get("access_token")

# Localiza o ID do arquivo Excel
def buscar_arquivo_excel(token):
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{EXCEL_FOLDER_NAME}/{EXCEL_FILE_NAME}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    return resp.json().get("id")

# Insere os dados na planilha
def inserir_linha_excel(json_dados, mensagem_original):
    token = obter_token()
    arquivo_id = buscar_arquivo_excel(token)

    # Garante o valor com vírgula
    valor = str(json_dados["valor"]).replace(".", ",")

    dados = [[
        json_dados["data"],
        json_dados["tipo"],
        valor,
        json_dados["forma_pagamento"],
        json_dados["categoria"],
        json_dados["subcategoria"],
        json_dados["descricao"],
        mensagem_original
    ]]

    # Define o corpo do conteúdo
    body = {"values": dados}

    # Encontra a última linha preenchida
    range_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{arquivo_id}/workbook/worksheets('{EXCEL_WORKSHEET}')/usedRange"
    range_resp = requests.get(range_url, headers={"Authorization": f"Bearer {token}"})
    range_data = range_resp.json()
    last_row = range_data.get("address", "").split("!")[-1].split(":")[-1]
    row_num = int(''.join(filter(str.isdigit, last_row))) + 1 if last_row else 2  # Pula o cabeçalho

    # Define o range destino para inserir (linha nova)
    cell_range = f"A{row_num}:H{row_num}"  # 8 colunas
    url = f"https://graph.microsoft.com/v1.0/me/drive/items/{arquivo_id}/workbook/worksheets('{EXCEL_WORKSHEET}')/range(address='{cell_range}')"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.patch(url, headers=headers, json=body)
    return response.status_code == 200
