import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Define escopo de permissões do Google Sheets
escopos = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Nome da planilha e da aba
NOME_PLANILHA = "Controle Financeiro"
NOME_ABA = "Dados de Lançamentos"

# Caminho do arquivo JSON com credenciais
CAMINHO_CREDENCIAL = "google-credentials.json"

def inserir_linha_google_sheets(json_dados, mensagem_original):
    try:
        # Autenticação
        credenciais = ServiceAccountCredentials.from_json_keyfile_name(CAMINHO_CREDENCIAL, escopos)
        cliente = gspread.authorize(credenciais)

        # Acessa planilha e aba
        planilha = cliente.open(NOME_PLANILHA)
        aba = planilha.worksheet(NOME_ABA)

        # Converte valor para vírgula
        valor = str(json_dados["valor"]).replace(".", ",")

        linha = [
            json_dados["data"],
            json_dados["tipo"],
            valor,
            json_dados["forma_pagamento"],
            json_dados["categoria"],
            json_dados["subcategoria"],
            json_dados["descricao"],
            mensagem_original
        ]

        aba.append_row(linha, value_input_option="USER_ENTERED")
        return True

    except Exception as e:
        print(f"[ERRO GOOGLE SHEETS] {e}")
        return False
