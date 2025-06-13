import os
import requests
from datetime import datetime

CLIENT_ID = os.getenv("CLIENT_ID")
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
EXCEL_USER_EMAIL = os.getenv("EXCEL_USER_EMAIL")
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
    url = f"https://graph.microsoft.com/v1.0/users/{EXCEL_USER_EMAIL}/drive/root:/{EXCEL_FOLDER_NAME}/{EXCEL_FILE_NAME}"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    print("[DEBUG] Arquivo localizado:", resp.json())
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

    url = f"https://graph.microsoft.com/v1.0/users/{EXCEL_USER_EMAIL}/drive/items/{arquivo_id}/workbook/worksheets('{EXCEL_WORKSHEET}')/tables/0/rows/add"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {"values": dados}
    response = requests.post(url, headers=headers, json=body)
    print("[DEBUG] Resposta Excel:", response.status_code, response.text)
    return response.status_code == 201 or response.status_code == 200
