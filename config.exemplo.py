# -*- coding: utf-8 -*-
"""Modelo de configuracao. Copie este arquivo para `config.py` e preencha com
os seus dados. `config.py` esta no .gitignore e nunca vai para o repositorio.

    cp config.exemplo.py config.py   (Linux/Mac)
    copy config.exemplo.py config.py (Windows)
"""

# ---- Snowflake ----
SNOWFLAKE = dict(
    account="SEU_ACCOUNT_IDENTIFIER",   # ex.: ABCDEFG-HI12345
    user="SEU_USUARIO",
    password="SUA_SENHA",
    role="SYSADMIN",                    # ACCOUNTADMIN para criar/atualizar Dynamic Tables
    warehouse="COMPUTE_WH",
)

# ---- Domo (opcional, so para o push de datasets) ----
DOMO = dict(
    host="https://SUA-INSTANCIA.domo.com",
    email="seu-email@exemplo.com",
    senha="SUA_SENHA_DOMO",
)

# Pasta local onde ficam os arquivos .csv baixados da Receita Federal
PASTA_ARQUIVOS = r"C:\RF"
