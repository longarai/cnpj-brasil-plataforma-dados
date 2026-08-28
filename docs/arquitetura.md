# Arquitetura de Dados — Snowflake → Domo

> 📸 Este documento descreve o desenho. Para vê-lo funcionando no ambiente real — stage,
> Dynamic Tables, grafo de atualização, linhagem e consulta final — veja
> **[o_pipeline_por_dentro.md](o_pipeline_por_dentro.md)**.

Warehouse único `COMPUTE_WH` (decisão: não criar warehouse novo para não gerar custo).
Objetos da ingestão criados com role `SYSADMIN`; Dynamic Tables com `ACCOUNTADMIN`
(a role dona precisa enxergar o warehouse para o refresh automático).

## Camadas (medalhão, nomenclatura Snowflake/dbt)

| Banco | Papel | Organização | Tipo de objeto |
|---|---|---|---|
| `RAW` | Bruto, fiel ao arquivo | 1 schema por origem | Tabelas + stage + file format + procedure de carga |
| `STAGING` | Tipado, limpo, decodificado | 1 schema por origem | Dynamic Tables |
| `MARTS` | Pronto para consumo/painel | 1 schema por assunto de negócio | Dynamic Tables (estrela) + views de consumo |

Regra de ouro: **origem organiza a entrada (RAW/STAGING), negócio organiza a saída (MARTS)**.
Com 50 origens no futuro, continuam existindo só 3 bancos — cada origem nova é um schema novo.

## Origem 1: Receita Federal (dados abertos CNPJ)

- ~28 GB/mês, CSV `;` aspas Latin-1 sem cabeçalho, versão mensal substitui a anterior
- Ingestão: `carga_mensal.py` (PUT) + `RAW.RECEITA_FEDERAL.SP_CARGA_MENSAL` (TRUNCATE + COPY + REMOVE)
- **Padrão único de ingestão, sempre em 3 fases**: (1) limpa o stage interno (remove os
  arquivos do mês anterior); (2) TODOS os arquivos do mês novo sobem para o stage;
  (3) a procedure carrega tudo do stage para as tabelas. **Os arquivos permanecem no
  stage até a próxima carga mensal** (decisão 27/08/2026) — servem de cópia do mês
  vigente e permitem recarregar qualquer tabela sem novo upload
  (`CALL SP_CARGA_MENSAL(...)` direto no Snowsight)
- 10 tabelas RAW: CNPJ (arquivo "Estabelecimentos" — menor grão, CNPJ completo de
  14 dígitos), EMPRESAS, SOCIOS, SIMPLES + 6 domínios
- Padrão de nomes: termo único `RECEITA_FEDERAL` (nunca abreviar para "RF"); objetos não
  repetem o nome do schema (`RAW.RECEITA_FEDERAL.STG_ARQUIVOS`, `...FF_CSV`)
- Detalhes operacionais: `carga_mensal_passo_a_passo.md`

## STAGING.RECEITA_FEDERAL (a construir)

Dynamic Tables 1:1 com a origem, aplicando as regras de `regras_negocio_referencia.md`:
tipagem de datas e valores, CNPJ completo de 14 dígitos, decodificações (por JOIN nos
domínios quando existir arquivo; por CASE fixo quando não existir), TIPO_EMAIL,
TIPO_TELEFONE, NOME_EMPRESA.

## MARTS — modelagem para o painel (estudo 27/08/2026)

### Modelo: estrela (star schema) dentro do MARTS

- **Fato**: `FATO_CNPJ` — grão = 1 CNPJ completo (14 dígitos), com situação, datas,
  capital social, opções Simples/MEI, sócios concatenados, todos os CNAEs
- **Dimensões**: `DIM_CNAE`, `DIM_MUNICIPIO`, `DIM_NATUREZA_JURIDICA`, `DIM_TEMPO`
  (as demais classificações de baixa cardinalidade — porte, situação, matriz/filial —
  ficam decodificadas como atributos texto no próprio fato)
- Materialização: **Dynamic Tables** — persistem o resultado dos joins/agregações pesadas
  (LISTAGG de sócios e CNAEs em dezenas de milhões de linhas) e se atualizam sozinhas
  quando o RAW recebe a carga do mês

### O que o Domo lê: views achatadas e agregados, não a estrela crua

O nosso Domo recebe dados por **push da API** (dataset webform + stream, método já validado).
Práticas do próprio Domo ([Data Processing Best Practices](https://domohelp.domo.com/hc/en-us/articles/360042935434-Data-Processing-and-Tools-Best-Practices)):
cada card trabalha sobre UM dataset; juntar datasets dentro do Domo (Magic ETL/DataFusion)
custa manutenção e execução lá. Padrão de mercado: **estrela no warehouse, dataset achatado
(flat) por assunto para o BI**.

Portanto:

- `MARTS.EMPRESAS.VW_DOMO_<painel>` — **views** simples em cima da estrela, uma por dataset
  do Domo, já achatadas (fato + descrições das dimensões). View (e não Dynamic Table) porque
  o trabalho pesado já foi materializado na estrela — o achatamento final é leve e é lido
  só na hora do push mensal
- **Agregados pequenos para o painel** (ex.: empresas ativas por UF/município/CNAE/mês,
  aberturas × fechamentos por mês, adesão Simples/MEI) — Dynamic Tables agregadas; são esses
  datasets pequenos (milhares de linhas) que vão ao Domo, não os 66 milhões de
  estabelecimentos. A base detalhada fica consultável no Snowflake

### Por que Dynamic Table na estrela e view na ponta

Dynamic Tables persistem fisicamente o resultado — painel/export lê resultado pronto em vez
de recalcular ([comparativos](https://www.hexstream.com/tech-corner/materialized-views-vs-dynamic-tables-in-snowflake-for-engineers-who-have-been-burned),
[guia](https://dataengineeracademy.com/blog/snowflake-dynamic-tables-explained-for-data-engineers/)).
Boas práticas: quebrar pipeline em cadeia de Dynamic Tables (joins primeiro, agregação
depois), cada uma com um passo lógico. Views ficam para transformações leves de última milha.

## Fluxo mensal completo

1. Baixar arquivos novos em `C:\RF` e rodar `carga_mensal.py`
2. RAW recarregado → STAGING e MARTS (Dynamic Tables) se atualizam sozinhas
3. Script de push (a construir) envia os datasets das `VW_DOMO_*` para o Domo via Stream API
4. Painel no Domo reflete o mês novo
