-- Executar como SYSADMIN
-- Para cada conjunto de arquivos: TRUNCATE + COPY.
-- Os arquivos permanecem no stage apos a carga; quem os remove e o inicio da carga seguinte.
-- Conjunto sem arquivo no stage nao trunca a tabela: mantem a carga anterior e avisa no resumo.

CREATE OR REPLACE PROCEDURE RAW.RECEITA_FEDERAL.SP_CARGA_MENSAL(DATA_REFERENCIA DATE)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
DECLARE
  conjuntos RESULTSET DEFAULT (
    SELECT column1 AS tabela, column2 AS padrao, column3 AS qtd_campos FROM VALUES
      ('CNAE',               '.*CNAECSV.*',  2),
      ('MOTIVO',             '.*MOTICSV.*',  2),
      ('MUNICIPIO',          '.*MUNICCSV.*', 2),
      ('NATUREZA_JURIDICA',  '.*NATJUCSV.*', 2),
      ('PAIS',               '.*PAISCSV.*',  2),
      ('QUALIFICACAO_SOCIO', '.*QUALSCSV.*', 2),
      ('SIMPLES',            '.*SIMPLES.*',  7),
      ('SOCIOS',             '.*SOCIOCSV.*', 11),
      ('EMPRESAS',           '.*EMPRECSV.*', 7),
      ('CNPJ',               '.*ESTABELE.*', 30)
  );
  resumo VARCHAR DEFAULT '';
BEGIN
  resumo := 'Carga referencia ' || TO_VARCHAR(:DATA_REFERENCIA) || CHR(10);

  FOR c IN conjuntos DO
    LET tabela VARCHAR := 'RAW.RECEITA_FEDERAL.' || c.tabela;

    EXECUTE IMMEDIATE 'LS @RAW.RECEITA_FEDERAL.STG_ARQUIVOS PATTERN = ''' || c.padrao || '''';
    LET qtd_arquivos INTEGER := (SELECT COUNT(*) FROM TABLE(RESULT_SCAN(LAST_QUERY_ID())));
    IF (qtd_arquivos = 0) THEN
      resumo := resumo || c.tabela || ': SEM ARQUIVO no stage - mantida a carga anterior' || CHR(10);
      CONTINUE;
    END IF;

    -- monta "t.$1, t.$2, ..." conforme a quantidade de campos do arquivo
    LET campos VARCHAR := '';
    LET qtd INTEGER := c.qtd_campos;
    FOR n IN 1 TO qtd DO
      campos := campos || 't.$' || n || ', ';
    END FOR;

    EXECUTE IMMEDIATE 'TRUNCATE TABLE ' || tabela;
    EXECUTE IMMEDIATE 'COPY INTO ' || tabela
      || ' FROM (SELECT ' || campos || 'METADATA$FILENAME, '''
      || TO_VARCHAR(:DATA_REFERENCIA) || '''::DATE, CURRENT_TIMESTAMP()'
      || ' FROM @RAW.RECEITA_FEDERAL.STG_ARQUIVOS t)'
      || ' PATTERN = ''' || c.padrao || '''';

    LET contagem INTEGER := (SELECT COUNT(*) FROM IDENTIFIER(:tabela));
    resumo := resumo || c.tabela || ': ' || contagem || ' linhas' || CHR(10);
  END FOR;

  RETURN resumo;
END;
$$;
