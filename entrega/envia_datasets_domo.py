# -*- coding: utf-8 -*-
"""Envia os datasets do painel (views VW_DOMO_*) do Snowflake para o Domo.

Na primeira execucao cria cada dataset no Domo (webform + stream); nas seguintes
apenas substitui os dados. Os IDs criados ficam guardados em datasets_domo.json.

Credenciais ficam em config.py (copie de config.exemplo.py). Uso: python envia_datasets_domo.py
"""
import csv
import io
import json
import sys
from pathlib import Path

import requests
import snowflake.connector

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import SNOWFLAKE, DOMO  # noqa: E402

DATASETS = [
    ("CNPJ - Empresas por Municipio", "MARTS.EMPRESAS.VW_DOMO_EMPRESAS_MUNICIPIO"),
    ("CNPJ - Empresas por CNAE",      "MARTS.EMPRESAS.VW_DOMO_EMPRESAS_CNAE"),
    ("CNPJ - Aberturas por Mes",      "MARTS.EMPRESAS.VW_DOMO_ABERTURAS_MES"),
    ("CNPJ - Top 15 Municipios",      "MARTS.EMPRESAS.VW_DOMO_TOP15_MUNICIPIO"),
    ("CNPJ - Top 15 CNAEs",           "MARTS.EMPRESAS.VW_DOMO_TOP15_CNAE"),
    ("CNPJ - Detalhe Analitico",      "MARTS.EMPRESAS.VW_DOMO_CNPJ_DETALHE"),
]
ARQ_IDS = Path(__file__).with_name("datasets_domo.json")


def autenticar():
    r = requests.post(
        f"{DOMO['host']}/api/content/v2/authentication",
        json={"method": "password", "emailAddress": DOMO["email"], "password": DOMO["senha"]},
        timeout=30,
    )
    r.raise_for_status()
    return {"X-DOMO-Authentication": r.json()["sessionToken"], "Content-Type": "application/json"}


def tipo_domo(col):
    # type_code do conector Snowflake: 0 = numero, 3 = data
    if col.type_code == 0:
        return "DECIMAL" if (col.scale or 0) > 0 else "LONG"
    if col.type_code == 3:
        return "DATE"
    return "STRING"


def criar_dataset(headers, nome, colunas):
    corpo = {
        "name": nome,
        "description": "Plataforma de dados - CNPJ Receita Federal (carga mensal)",
        "columns": [{"type": t, "name": n} for n, t in colunas],
    }
    r = requests.post(f"{DOMO['host']}/api/data/v2/webforms", headers=headers, json=corpo, timeout=60)
    r.raise_for_status()
    d = r.json()
    return {"streamId": d["id"], "datasetId": d["dataSource"]["id"]}


def subir_dados(headers, stream_id, csv_texto):
    r = requests.post(f"{DOMO['host']}/api/data/v1/streams/{stream_id}/executions", headers=headers, timeout=60)
    r.raise_for_status()
    execucao = r.json()["executionId"]   # atencao: a chave e "executionId", nao "id"
    h = dict(headers)
    h["Content-Type"] = "text/csv"
    r = requests.put(
        f"{DOMO['host']}/api/data/v1/streams/{stream_id}/executions/{execucao}/part/1",
        headers=h, data=csv_texto.encode("utf-8"), timeout=600,
    )
    r.raise_for_status()
    r = requests.put(
        f"{DOMO['host']}/api/data/v1/streams/{stream_id}/executions/{execucao}/commit",
        headers=headers, timeout=120,
    )
    r.raise_for_status()


def main():
    ids = json.loads(ARQ_IDS.read_text(encoding="utf-8")) if ARQ_IDS.exists() else {}
    headers = autenticar()
    conn = snowflake.connector.connect(**SNOWFLAKE)
    cur = conn.cursor()
    try:
        for nome, view in DATASETS:
            cur.execute(f"SELECT * FROM {view}")
            colunas = [(c.name, tipo_domo(c)) for c in cur.description]
            buffer = io.StringIO()
            escritor = csv.writer(buffer, lineterminator="\n")
            total = 0
            for linha in cur:
                escritor.writerow(["" if v is None else v for v in linha])
                total += 1
            if nome not in ids:
                ids[nome] = criar_dataset(headers, nome, colunas)
                ARQ_IDS.write_text(json.dumps(ids, indent=2), encoding="utf-8")
                print(f"dataset criado no Domo: {nome} ({ids[nome]['datasetId']})", flush=True)
            subir_dados(headers, ids[nome]["streamId"], buffer.getvalue())
            print(f"enviado: {nome} - {total} linhas", flush=True)
    finally:
        cur.close()
        conn.close()
    print("ENVIO CONCLUIDO", flush=True)


if __name__ == "__main__":
    main()
