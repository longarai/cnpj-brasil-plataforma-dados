# Carga mensal — passo a passo (2 cliques)

A Receita Federal publica uma versão nova dos dados do CNPJ todo mês. Só a versão mais
recente importa: a carga limpa (TRUNCATE) e recarrega as tabelas do zero.

## 1. Baixar os arquivos do mês

- Acessar https://arquivos.receitafederal.gov.br/dados/cnpj/dados_abertos_cnpj/
- Entrar na pasta do mês mais recente (ex.: `2026-08/`)
- Baixar todos os zips: Empresas (10), Estabelecimentos (10), Socios (10), Simples,
  Cnaes, Motivos, Municipios, Naturezas, Paises, Qualificacoes
- **Apagar os arquivos antigos de `C:\RF`** e descompactar tudo lá
  (a pasta deve conter só os arquivos do mês novo, sem subpastas)

## 2. Rodar a carga (2 cliques)

Dar dois cliques em:

```
ingestao\carga_mensal.bat
```

A janela preta vai mostrar o progresso. **Não fechar a janela** — o envio dos ~28 GB
leva horas (depende da internet). O que acontece por baixo:

1. Apaga do stage do Snowflake os arquivos do mês anterior
2. Envia os arquivos novos compactados (`PUT`)
3. Chama a procedure `RAW.RECEITA_FEDERAL.SP_CARGA_MENSAL`, que limpa e recarrega
   cada tabela — os arquivos ficam guardados no stage até a próxima carga mensal
4. Imprime o resumo com a contagem de linhas por tabela

A data de referência é lida automaticamente do nome dos arquivos (`D60811` = 11/08/2026).

## 3. Conferir o resumo no final

- Deve listar as 10 tabelas com contagens maiores que zero
- As contagens só crescem de um mês para o outro — se vier bem menor que o mês
  anterior, algo deu errado
- Se aparecer `SEM ARQUIVO no stage`, aquele conjunto não estava em `C:\RF` —
  baixar o que faltou e rodar o `.bat` de novo (pode rodar quantas vezes precisar,
  não duplica nada; a tabela que ficou para trás mantém a carga anterior até isso)
- As camadas STAGING e MARTS (Dynamic Tables) se atualizam sozinhas depois do RAW

## Alternativa sem Python (direto no Snowsight)

Se os arquivos já estiverem no stage:

```sql
CALL RAW.RECEITA_FEDERAL.SP_CARGA_MENSAL('2026-08-11');
```

## Se der erro

- `Nenhum arquivo em C:\RF` → a pasta está vazia; refazer o passo 1
- Erro de conexão/senha → conferir os dados em `config.py`
- Janela fechou no meio do envio → rodar o `.bat` de novo do início
