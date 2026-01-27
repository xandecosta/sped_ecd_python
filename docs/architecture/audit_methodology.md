# Metodologia de Auditoria Forense (Módulo ECDAuditor)

Este documento descreve detalhadamente a lógica, os fundamentos contábeis e os critérios de validação utilizados pelo motor de auditoria forense para arquivos SPED-ECD.

---

## 1. Visão Geral

A auditoria forense do sistema não se limita a validações de layout (já realizadas pelo PVA). Seu objetivo é identificar fraudes, manipulações de resultados, erros de transporte de saldos e inconsistências qualitativas que possam comprometer a fidedignidade das demonstrações contábeis.

### Matriz de Status e Impacto

- **APROVADO**: O teste não identificou divergências acima da tolerância matemática (zero para Decimal).
- **ALERTA**: Identificadas inconsistências qualitativas ou desvios estatísticos que exigem análise humana, sem necessariamente indicar erro aritmético.
- **REPROVADO**: Divergência matemática confirmada ou anomalia grave que invalida a integridade dos dados.
- **IMPACTO**: Representa o valor monetário absoluto envolvido na irregularidade.

---

## 2. Grupo 1: Integridade Estrutural

Foca na amarração matemática entre os diferentes registros da ECD.

### 1.1 Cruzamento Diário vs. Balancete

**Objetivo**: Verificar se a soma dos lançamentos analíticos (I250) corresponde à movimentação informada nos saldos mensais (I155).

- **Processamento**:
    1. Agrega todos os lançamentos do Diário por `COD_CTA` e `PERIODO`.
    2. **Filtro Forense**: O motor ignora automaticamente lançamentos do tipo 'E' (Encerramento) no Diário, uma vez que o balancete processado já reflete os saldos restaurados ao estado pré-encerramento para permitir a análise de continuidade.
    3. **Isolamento de Contas**: O teste é aplicado exclusivamente a contas analíticas (`IND_CTA == 'A'`), eliminando falsos positivos causados por grupos sintéticos.
    4. Compara a soma dos lançamentos com os campos `VL_DEB` e `VL_CRED` do registro I155.
    5. **Composição da Prova**: Caso haja divergência, o sistema identifica as chaves (Conta + Período) com erro e extrai todos os registros I250 correspondentes para a aba `EVIDENCIAS_DETALHADAS`.
- **Fundamento**: Princípio da Partida Dobrada e Integridade de Transporte.

### 1.2 Validação da Hierarquia Nativa

**Objetivo**: Recalcular a consolidação das contas sintéticas a partir das analíticas.

- **Processamento**:
    1. Varre o Plano de Contas (I050) e os saldos (I155).
    2. Para cada conta sintética, soma o saldo de seus filhos diretos (`COD_CTA_SUP`).
    3. Compara o saldo informado com o saldo recalculado.
- **Fundamento**: Estrutura Conceitual para Relatórios Financeiros (NBC TG Estrutura Conceitual).

---

## 3. Grupo 3: Coerência Referencial

Valida a conformidade com as regras de mapeamento da Receita Federal.

### 3.1 Consistência de Natureza

**Objetivo**: Garantir que a natureza contábil da conta (Ativo, Passivo, Resultado) seja coerente com o grupo onde ela foi mapeada no Plano Referencial.

- **Lógica de Validação**:
    - Conta Ativo (01) deve apontar para Referencial Grupo 1.
    - Conta Passivo/PL (02/03) deve apontar para Referencial Grupo 2.
    - Contas de Resultado (04) devem apontar para Referencial Grupo 3.
- **Status**: Gera **ALERTA** se detectar cruzamentos indevidos (ex: conta de Receita mapeada no Ativo).

### 3.2 Auditoria de Contas "Órfãs"

**Objetivo**: Identificar contas analíticas com movimentação financeira relevante que não possuem mapeamento para o plano referencial (campo I051 ausente).

- **Critério de Seleção**: Contas com `IND_CTA == 'A'` e saldo final ou movimentação superior a R$ 0,00.

---

## 4. Grupo 4: Análise Forense de Padrões

Utiliza métodos estatísticos e detecção de anomalias temporais.

### 4.1 Lei de Benford (Teste do Primeiro Dígito)

**Objetivo**: Detectar se os valores dos lançamentos foram "inventados" ou manipulados artificialmente através da análise da frequência natural dos dígitos iniciais.

- **Metodologia**:
    1. Extrai o primeiro dígito significativo de todos os valores absolutos do Diário.
    2. Compara a frequência observada com a distribuição esperada pela Lei de Benford.
    3. **Indicador de Risco (MAD)**: Utiliza o *Mean Absolute Deviation* (Desvio Médio Absoluto).
        - **MAD > 0.012**: Status **ALERTA**. Indica conformidade marginal ou padrões operacionais enviesados (ex: parcelamentos fixos).
        - **MAD > 0.020**: Status **REPROVADO**. Indica altíssima probabilidade de dados fabricados ou omissão sistemática de centavos/valores.
    4. **Composição da Prova (Drill-Down)**: O sistema identifica os dígitos com maior excesso de frequência e mapeia os 10 valores exatos que mais contribuem para a anomalia, apontando as contas e históricos predominantes.

### 4.2 Detecção de Duplicidades

**Objetivo**: Localizar lançamentos com características idênticas que podem indicar erros de processamento ou fraudes.

- **Filtro de Ruído Forense**: O motor aplica dois filtros inteligentes para evitar falsos positivos comuns em contabilidades reais:
    - **Filtro A (Materialidade)**: Ignora lançamentos idênticos com valor absoluto inferior a **R$ 50,00** se a conta envolver termos como "BANCO", "TARIFA" ou "TED".
    - **Filtro B (Processamento em Lote)**: Se o sistema detectar mais de **5 lançamentos idênticos** na mesma data e conta, o motor assume tratar-se de um padrão operacional (ex: folha de pagamento ou cobrança em massa) e reduz a criticidade do achado.
- **Impacto**: O impacto é calculado pela soma absoluta dos lançamentos classificados como "Suspeitos" após a filtragem de ruído.

### 4.3 Omissão de Encerramento (DRE não zerada)

**Objetivo**: Verificar se houve o encerramento das contas de resultado (zeramento) ao final do exercício.

- **Processamento**: Soma os saldos finais de todas as contas de natureza '04' na última data do arquivo. Saldo diferente de zero indica erro grave de apuração de lucro/prejuízo.

---

## 5. Grupo 5: Indicadores Profissionais (Análise Qualitativa)

### 5.1 Inversão de Natureza

Identifica contas que apresentam saldo contrário à sua natureza (ex: conta de Ativo com saldo credor) sem estarem classificadas como contas redutoras no plano.

### 5.2 Estouro de Caixa

Caso específico de inversão de natureza para o grupo de Disponibilidades (Caixa e Equivalentes). Um saldo credor no caixa indica omissão de receita ou passivo fictício.

### 5.3 Passivo Fictício (Estaticidade)

**Objetivo**: Detectar contas de obrigações (Fornecedores, Empréstimos) que apresentam saldo relevante mas permanecem "estáticas" por todo o exercício.

- **Fundamento**: Uma dívida que não apresenta pagamento (débito) nem novos encargos (crédito) por meses sugere que a obrigação pode não existir mais ou foi liquidada por fora da contabilidade oficial.
- **Lógica**: Identifica contas de natureza `02` com variação de saldo idêntica a zero durante todo o período coberto pela ECD.

### 5.4 Consistência PL vs. Resultado

**Objetivo**: Validar a amarração técnica entre o lucro/prejuízo apurado na DRE e a conta de destino no Patrimônio Líquido.

- **Fundamento**: Todo o resultado do exercício deve ser transferido para o PL através de lançamentos de encerramento.
- **Processamento**:
    1. Soma o saldo final de todas as contas de Resultado (Analíticas, Natureza `04`).
    2. Soma todos os lançamentos de encerramento (`IND_LCTO == 'E'`) que atingiram contas de Patrimônio Líquido (Natureza `03`).
    3. Calcula a divergência: `abs(Lucro_DRE - Transferencia_PL)`.
- **Tolerância**: O sistema admite uma divergência de até **R$ 100,00** para acomodar pequenos ajustes de arredondamento em sistemas legados. Acima disso, gera um status de **ALERTA**.

---

## 6. Fluxo de Output e Evidências

Toda a metodologia converge para o arquivo `<DATA>_07_Auditoria.xlsx`.

A maior inovação forense é a aba **EVIDENCIAS_DETALHADAS**, que atua como o elo final da auditabilidade. Em vez de obrigar o auditor a buscar o lançamento suspeito no PVA, o sistema já extrai as linhas do Diário (I250) que "não batem" com o Balancete, permitindo a conferência imediata.
