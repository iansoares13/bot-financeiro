import os
import gspread
import json
import tempfile
from oauth2client.service_account import ServiceAccountCredentials

# Define escopo de permissões do Google Sheets
escopos = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Nome da planilha e da aba
NOME_PLANILHA = "Controle Financeiro"
NOME_ABA = "Dados de Lançamentos"

def inserir_linha_google_sheets(json_dados, mensagem_original):
    try:
        # Salva o conteúdo do JSON da variável de ambiente em um arquivo temporário
        conteudo_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        if not conteudo_json:
            print("[ERRO] Variável de ambiente GOOGLE_SERVICE_ACCOUNT_JSON não encontrada.")
            return False

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp_json:
            temp_json.write(conteudo_json)
            temp_json_path = temp_json.name

        # Autenticação
        credenciais = ServiceAccountCredentials.from_json_keyfile_name(temp_json_path, escopos)
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

        # Remove o arquivo temporário
        os.remove(temp_json_path)
        return True

    except Exception as e:
        print(f"[ERRO GOOGLE SHEETS] {e}")
        return False
