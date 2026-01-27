# Algoritmos de Auditoria Forense (SPED-ECD)

Este documento detalha a lógica e os algoritmos implementados no módulo `core/auditor.py` para a realização de auditoria forense automatizada em arquivos da Escrituração Contábil Digital (ECD).

## 1. Integridade Estrutural

### 1.1 Cruzamento Diário vs. Balancete

**Objetivo:** Verificar se a soma dos lançamentos do Diário (I200/I250) coincide com os saldos informados no Balancete (I155).

**Algoritmo:**

1. Agrupar os lançamentos do Diário por `COD_CTA` (Conta) e `PERIODO` (Mês/Ano).
2. Somar os campos `VL_D` (Débito) e `VL_C` (Crédito) para cada grupo.
3. Obter os movimentos mensais do Balancete (`VL_DEB` e `VL_CRED`) para a mesma chave.
4. Realizar um *Outer Join* entre as duas visões.
5. Calcular a divergência: `DIF_DEB = Somatório(VL_D) - VL_DEB` e `DIF_CRED = Somatório(VL_C) - VL_CRED`.
6. Reportar qualquer conta cujo valor absoluto da diferença seja maior que zero.

### 1.2 Validação da Hierarquia Nativa

**Objetivo:** Validar se a estrutura de consolidação sintética informada no arquivo é matematicamente consistente.

**Algoritmo:**

1. Iterar por cada período (mês) presente no balancete.
2. Identificar todas as contas sintéticas (`IND_CTA = 'S'`).
3. Para cada conta sintética:
   - Localizar todas as contas filhas diretas (`COD_CTA_SUP` == conta atual).
   - Somar o saldo final (`VL_SLD_FIN_SIG`) das filhas.
   - Comparar o somatório com o saldo informado na conta sintética pai.
4. Reportar divergências de soma ou contas sintéticas sem filhas que possuam saldo.

---

## 2. Coerência Referencial (Normas RFB)

### 2.1 Consistência de Natureza

**Objetivo:** Garantir que o mapeamento para o Plano de Contas Referencial respeita a natureza da conta (Ativo/Passivo/DRE).

**Lógica de Validação:**

- **Nat 01 (Ativo):** O código referencial deve obrigatoriamente iniciar com `1`.
- **Nat 02 (Passivo):** O código referencial deve obrigatoriamente iniciar com `2`.
- **Nat 03 (PL):** O código referencial deve obrigatoriamente iniciar com `2`.
- **Nat 04 (Resultado):** O código referencial deve obrigatoriamente iniciar com `3`.
- **Nat 05/09:** Não devem estar mapeadas no Grupo 1 (Ativo) ou Grupo 2 (Passivo - exceto contas de resultado acumulado).

### 2.2 Auditoria de Contas "Órfãs"

**Objetivo:** Identificar contas analíticas com movimentação financeira relevante que não possuem mapeamento para o Plano Referencial.

**Algoritmo:**

1. Filtrar contas analíticas (`IND_CTA = 'A'`).
2. Identificar aquelas cujo Mapping Referencial (`COD_CTA_REF`) é nulo ou vazio.
3. Aplicar filtro de relevância: Saldo Inicial, Débito, Crédito ou Saldo Final devem ser diferentes de zero.
4. Reportar as ocorrências, destacando o maior saldo absoluto encontrado no período.

---

## 3. Análise Forense de Padrões

### 3.1 Lei de Benford (Teste Estatístico)

**Objetivo:** Detectar possíveis manipulações de valores através da análise de frequência do primeiro dígito.

**Algoritmo:**

1. Extrair todos os valores de Débito e Crédito (`VL_D > 0` e `VL_C > 0`) dos lançamentos diários.
2. Capturar o primeiro dígito significativo (1-9) de cada valor.
3. Calcular a frequência observada de cada dígito.
4. Comparar com a Frequência Teórica de Benford: $P(d) = \log_{10}(1 + \frac{1}{d})$.
5. Calcular o **MAD (Mean Absolute Deviation)** e o teste **Qui-Quadrado**.
6. **Classificação:**
   - **APROVADO:** MAD < 0.012
   - **ALERTA:** MAD entre 0.012 e 0.020
   - **REPROVADO:** MAD > 0.020 (indica forte desvio estatístico)

### 3.2 Detecção de Lançamentos Duplicados

**Objetivo:** Identificar erros de digitação ou fraudes por duplicidade de lançamentos.

**Algoritmo:**

1. Buscar no Diário lançamentos com a mesma **Data**, **Conta** e **Valor**.
2. Separar em dois subgrupos:
   - **Duplicatas Estruturais:** Mesmo `NUM_LCTO` (pode ser erro de exportação do sistema).
   - **Duplicatas Contábeis:** Lançamentos com números diferentes que repetem o fato contábil no mesmo dia.
3. Reportar casos com saldo diferente de zero.

### 3.3 Verificação de Omissão de Encerramento

**Objetivo:** Confirmar se as contas de resultado foram devidamente zeradas para o encerramento do exercício.

**Algoritmo:**

1. Isolar contas de natureza `04` (Resultado).
2. Selecionar os saldos do último mês do exercício.
3. Somar todos os saldos finais (`VL_SLD_FIN_SIG`).
4. O somatório **deve ser zero**. Caso contrário, reportar omissão de encerramento ou erro na transferência para o PL.

---

## 4. Indicadores de Qualidade Profissional

### 4.1 Inversão de Natureza

**Objetivo:** Detectar saldos anômalos (Ativo Credor ou Passivo Devedor).

**Algoritmo:**

1. Identificar Natureza 01 (Ativo) com saldo final negativo.
2. Identificar Natureza 02 (Passivo) com saldo final positivo.
3. Ignorar contas cujos nomes contenham termos redutores (ex: "(-) ", "REDUTORA").
4. Reportar as ocorrências remanescentes como Alerta.

### 4.2 Estouro de Caixa

**Objetivo:** Identificar momentos em que as contas de disponibilidade ficaram com saldo credor.

**Algoritmo:**

1. Identificar contas de caixa e bancos através do mapeamento referencial (`1.01.01.*`) ou palavras-chave no nome da conta ("CAIXA").
2. Verificar se em algum mês o saldo final (`VL_SLD_FIN_SIG`) foi negativo.
3. Reportar o impacto financeiro (valor do maior estouro).

### 4.3 Passivo Fictício (Estaticidade)

**Objetivo:** Identificar obrigações que permanecem no balancete sem movimentação, indicando possíveis passivos já liquidados ou inexistentes.

**Algoritmo:**

1. Selecionar contas de Passivo (`COD_NAT = '02'`).
2. Calcular o somatório anual de Débitos e Créditos.
3. Identificar contas com saldo relevante (ex: > R$ 1.000,00) que tiveram **zero** movimentação no período auditado.
4. Reportar para verificação física/circularização.
