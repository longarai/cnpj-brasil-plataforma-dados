# Qualidade dos dados — o que foi validado e o que o cadastro tem de estranho

Todo número publicado neste repositório foi **recalculado direto no Snowflake e comparado**
com o que está no portal. Esta página registra o resultado dessa conferência e, mais
importante, o que a base pública tem de imperfeito — porque quem usa esses dados precisa
saber onde eles enganam.

Competência validada: **11/07/2026**.

---

## 1. Conferência dos números publicados

Cada indicador do portal foi recalculado a partir de `MARTS.EMPRESAS.FATO_CNPJ` e comparado
com o valor exibido. **Resultado: 12 de 12 conferem, sem divergência.**

| Indicador | Publicado | Recalculado |
|---|---:|---:|
| Total de CNPJs | 72.318.968 | 72.318.968 |
| Empresas ativas | 27.800.285 | 27.800.285 |
| MEIs ativos | 13.457.959 | 13.457.959 |
| Optantes do Simples ativos | 20.710.130 | 20.710.130 |
| Municípios com CNPJ | 5.291 | 5.291 |
| Cidade de São Paulo | 6.487.716 | 6.487.716 |
| Estado do Rio de Janeiro | 6.130.236 | 6.130.236 |
| Aberturas em 2025 | 5.194.268 | 5.194.268 |
| MEIs abertos em 2025 | 2.779.188 | 2.779.188 |
| Abertas até 2011 (veteranas) | 23.377.006 | 23.377.006 |
| Veteranas ainda ativas | 4.238.067 | 4.238.067 |
| Microempresas ativas | 22.264.765 | 22.264.765 |

As séries dos gráficos também foram conferidas ponto a ponto: **situação cadastral** (5
categorias), **porte** (4), **sobrevivência por década** (7 décadas × 2 medidas), **aberturas
por mandato** (6 períodos × 2 medidas) e o **top 10 de municípios**. Nenhuma divergência.

**Testes de integridade que passaram:**

- A soma do agregado por município é **exatamente igual** ao total do fato (72.318.968)
- A soma das aberturas por mês também fecha com o total
- `MATRIZ` (69.062.850) + `FILIAL` (3.256.118) = 72.318.968
- 72.318.968 CNPJs, **todos distintos**, nenhum nulo, nenhum fora dos 14 dígitos
- Nenhuma data de início ou de situação no futuro; nenhum capital social negativo

---

## 2. O que o cadastro tem de estranho

Aqui estão as armadilhas reais da base. Nenhuma delas é erro do pipeline — são
características do dado público, e ignorá-las leva a conclusões erradas.

### O capital social é declarado pela empresa, não pelo estabelecimento

Esta é a pegadinha mais perigosa. O capital social vem do arquivo de **Empresas**, ligado ao
CNPJ básico (os 8 primeiros dígitos). Quando você junta com os estabelecimentos, **cada
filial herda o capital inteiro da matriz**.

Consequência prática: uma consulta ingênua de "maiores empresas de Santo André por capital
social" devolvia **seis agências do Banco do Brasil**, cada uma exibindo os R$ 120 bilhões de
capital do banco inteiro:

```
00.000.000/7847-61   ESCRITORIO CORPORATE BANKING ABC - SANTO ANDRE   R$ 120 bi
00.000.000/4194-78   BAIRRO JARDIM - SANTO ANDRE (SP)                 R$ 120 bi
00.000.000/0264-09   SANTO ANDRE (SP)                                 R$ 120 bi
...
```

**Como está tratado aqui:** todas as listas de "maiores por capital" filtram
`MATRIZ_FILIAL = 'MATRIZ'`. Com o filtro, Santo André mostra seis empresas de verdade e
distintas. Se você for reaproveitar estes dados, **não some capital social por município** —
o número sairia multiplicado pelo número de filiais.

### O capital social não é auditado — e tem valor fantasioso

A Receita registra o que a empresa declara, sem validar. O resultado:

- **177.959 CNPJs** declaram capital acima de **R$ 1 bilhão**
- O valor máximo encontrado é **R$ 999.999.999.999** (o teto do campo), declarado por
  dezenas de holdings recém-abertas, várias sem nome de fantasia
- Entre as quinze maiores do país por capital declarado aparecem uma cafeteria de Nova
  Iguaçu (R$ 500 bi) e uma costureira de Silves/AM (R$ 464 bi)

**Como está tratado aqui:** o dado é exibido como está — ele é verdadeiro no sentido de que
é exatamente o que foi declarado — mas sempre rotulado como **"capital social declarado"**.
Não use esse campo como medida de porte econômico.

### Outros pontos de atenção

| O que | Números | O que significa |
|---|---|---|
| CEP ausente ou fora do padrão | 248.172 (0,34%) | preencher o endereço completo exige tratar esses casos |
| Porte em branco | 3.147 | aparece como "não informado" nos gráficos, não é descartado |
| Datas muito antigas | início mínimo em **23/10/1891** | são reais: empresas centenárias ainda cadastradas |
| Sócios por empresa | máximo de **2.585** | cooperativas e associações; não é erro |
| 2026 é ano parcial | vai até **11/07/2026** | qualquer comparação anual com 2026 é injusta — os gráficos avisam |
| Picos de baixas em 2008 e 2018 | 4,2 mi e 2,5 mi | são **baixas administrativas em massa**, não fechamentos daquele ano |

---

## 3. Como reproduzir esta validação

Os dois scripts que geraram este relatório estão no repositório de trabalho e podem ser
adaptados para qualquer competência:

- **perfilagem de colunas** — mínimo, máximo, nulos, distintos e valores suspeitos de cada
  coluna do fato
- **conferência série a série** — recalcula cada número publicado e compara com o portal,
  falhando se houver qualquer divergência

O princípio: **nenhum número vai para o ar sem ser recalculado na fonte.** É por isso que
cada gráfico do portal traz o botão `</> SQL` — a consulta que o originou fica à vista.
