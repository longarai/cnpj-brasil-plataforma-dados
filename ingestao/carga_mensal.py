# -*- coding: utf-8 -*-
"""Carga mensal dos dados abertos do CNPJ (Receita Federal) no Snowflake.

Credenciais em config.py (copie de config.exemplo.py). Uso: python carga_mensal.py
"""
import re
import sys
from pathlib import Path

import snowflake.connector

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import SNOWFLAKE, PASTA_ARQUIVOS  # noqa: E402

STAGE = "@RAW.RECEITA_FEDERAL.STG_ARQUIVOS"
PASTA = Path(PASTA_ARQUIVOS)


def data_referencia(nome_arquivo):
    # D<ultimo digito do ano><mes><dia>: D60711 = 11/07/2026
    d = re.search(r"\.D(\d)(\d{2})(\d{2})(\.|$)", nome_arquivo)
    return f"202{d[1]}-{d[2]}-{d[3]}"


def main():
    arquivos = [a for a in sorted(PASTA.iterdir()) if a.is_file()]
    if not arquivos:
        raise SystemExit(f"Nenhum arquivo em {PASTA}")
    referencia = data_referencia(arquivos[0].name)
    print(f"{len(arquivos)} arquivos | referencia {referencia}", flush=True)

    conn = snowflake.connector.connect(client_session_keep_alive=True, **SNOWFLAKE)
    cur = conn.cursor()
    try:
        cur.execute(f"REMOVE {STAGE}")
        print("stage limpo", flush=True)
        print("enviando arquivos...", flush=True)
        cur.execute(f"PUT 'file://{PASTA.as_posix()}/*' {STAGE} AUTO_COMPRESS=TRUE PARALLEL=8")
        for r in cur.fetchall():
            print(f"  {r[0]}: {r[6]}", flush=True)
        cur.execute(f"CALL RAW.RECEITA_FEDERAL.SP_CARGA_MENSAL('{referencia}')")
        print(cur.fetchone()[0], flush=True)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
