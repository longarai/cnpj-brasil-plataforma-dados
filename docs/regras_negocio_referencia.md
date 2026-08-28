# Regras de negócio de referência — scripts antigos do Gabriel (LZ.CNPJ, ~2021-2025)

Pontos bons extraídos dos scripts usados há 5 anos, para reaproveitar na construção
das camadas STAGING e MARTS. Fonte: scripts enviados pelo Gabriel em 27/08/2026.

## Chave

- **CNPJ completo (14 dígitos)** = `CNPJ_BASICO || CNPJ_ORDEM || CNPJ_DV`

## Decodificações SEM arquivo de domínio (precisam de CASE fixo)

A Receita não publica arquivo de domínio para estes códigos — decodificar via CASE:

- **SITUACAO_CADASTRAL**: 01=NULA, 02=ATIVA, 03=SUSPENSA, 04=INAPTA, 08=BAIXADA
- **PORTE_EMPRESA**: 00=NÃO INFORMADO, 01=MICRO EMPRESA, 03=EMPRESA DE PEQUENO PORTE, 05=DEMAIS
- **IDENTIFICADOR_MATRIZ_FILIAL**: 1=MATRIZ, 2=FILIAL
- **FAIXA_ETARIA (sócios)**: 1=00 a 12 anos, 2=13 a 20, 3=21 a 30, 4=31 a 40, 5=41 a 50,
  6=51 a 60, 7=61 a 70, 8=71 a 80, 9=80 anos ou mais, 0=Não se aplica
- **OPCAO_SIMPLES / OPCAO_MEI**: quando o CNPJ não está no arquivo do Simples,
  assumir `'N'` (no antigo: `NVL(t3.OPCAO_SIMPLES,'N')`)

## Decodificações COM arquivo de domínio (usar as tabelas do RAW, não CASE)

Hoje o RAW já tem as tabelas oficiais — preferir JOIN a CASE fixo:
CNAE, MOTIVO (situação cadastral), MUNICIPIO, NATUREZA_JURIDICA, PAIS, QUALIFICACAO_SOCIO.

## Campos derivados que funcionaram bem

- **SOCIOS (concatenados)**: `LISTAGG(NOME_SOCIO, ', ') WITHIN GROUP (ORDER BY NOME_SOCIO)`
  agrupado por CNPJ_BASICO — vira uma coluna única com todos os sócios da empresa
- **TODOS_CNAES**: mesma ideia com as descrições de CNAE (principal + secundários).
  Atenção: `CNAE_FISCAL_SECUNDARIA` vem como lista separada por vírgula em um campo só
  (ex: `"8599603,8219999"`) — abrir com `SPLIT_TO_TABLE` antes de juntar com a tabela CNAE
- **TIPO_EMAIL**: e-mail contendo `CONTAB` ou `CONTADOR` (em maiúsculas) = "E-mail Contábil";
  vazio/nulo = "Sem E-mail"; senão = "E-mail Particular" — identifica quando o cadastro
  aponta para o contador em vez do dono
- **TIPO_TELEFONE**: primeiro dígito do telefone 7, 8 ou 9 = "Celular";
  ambos os telefones vazios = "Sem Telefone"; senão = "Telefone Fixo"
  (no script antigo email+telefone viravam um campo só concatenado com " - ";
  na nova modelagem manter como DUAS colunas separadas, melhor para filtrar no painel)
- **NOME_EMPRESA**: `NOME_FANTASIA` se preenchido, senão `RAZAO_SOCIAL`
- **ANO_MES_INICIO / ANO_INICIO**: substring da data de início de atividade (AAAAMM / AAAA)

## Validação usada na época (manter como teste)

- Conferir o LISTAGG de sócios de um CNPJ conhecido (ex.: básico `07785468`)
- Conferir contagens totais por conjunto contra os números do mês anterior
  (empresas/estabelecimentos/sócios/simples só crescem entre versões)
