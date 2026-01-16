# Arquitetura de Geração do Balancete baseRFB

Este documento descreve detalhadamente o processo de criação dos balancetes baseados no Plano de Contas Referencial da Receita Federal (baseRFB), abrangendo cenários de dados completos e cenários de contingência (inferência histórica).

---

## 1. Fluxo em Situação Normal
Ocorre quando o arquivo ECD (txt) contém todos os metadados necessários para o mapeamento.

### Inputs (Entradas)
1.  **Registro 0000**: Campo `COD_PLAN_REF` informa o código do plano referencial (ex: "1" para PJ em Geral, "10" para PJ em Geral - Lucro Presumido).
    > **Nota Crítica**: Os códigos e seus significados mudaram drasticamente a partir de 2014. Um código "10" pré-2014 não é equivalente ao mesmo código pós-2014. O sistema deve respeitar a vigência temporal do código para selecionar o schema de nomes correto.
2.  **Registro I050**: Plano de contas contábil da empresa (`COD_CTA`, `NIVEL`, `IND_CTA`).
3.  **Registro I051**: Mapeamento explícito entre a conta contábil da empresa (`FK_PAI` ligada ao `PK` do I050) e a conta referencial (`COD_CTA_REF`).
4.  **Registros I155 / I355**: Saldos das contas contábeis ao final do período.
5.  **Catálogo Referencial (`ref_catalog.json`)**: Mapeia o `COD_PLAN_REF` + `Ano` para o arquivo CSV de estrutura referencial.

### Processamento
1.  **Identificação do Plano**: O `ECDProcessor` localiza o arquivo CSV correspondente em `schemas/ref_plans/data` usando o código informado no arquivo.
2.  **Vínculo Contábil-Referencial**: É realizado um *join* interno entre as contas que possuem saldo e seus registros I051 correspondentes.
3.  **Consolidação de Saldos**: Os valores são agrupados pelo `COD_CTA_REF`.
4.  **Propagação da Hierarquia**: Utiliza-se a estrutura do CSV referencial (campos `COD_CTA` e `COD_CTA_SUP`) para somar os saldos das contas analíticas para as contas sintéticas do plano da Receita.

### Outputs (Saídas)
-   **Internal DataFrame**: `04_Balancetes_RFB`.
-   **Colunas**: `COD_CTA_REF`, `DESC_CTA_REF`, `NIVEL_REF`, `VL_SLD_FIN`, `IND_DC_FIN`.

---

## 2. Fluxo em Situação Específica (Inferência Cross-Temporal)
Ocorre quando o arquivo ECD é omisso (ausência de `I051` e/ou `COD_PLAN_REF`), comum em períodos de transição de sistemas ou layouts antigos (ex: 2014).

### Inputs (Entradas)
1.  **Registro I050 (Ano Alvo)**: Estrutura do plano de contas contábil analítico (`COD_CTA` e `COD_SUP`).
2.  **Base de Conhecimento (`HistoricalMapper`)**: Dados acumulados de outros anos da mesma empresa (CNPJ).
3.  **Mapeamentos Históricos**: Dicionários de mapeamento por conta (`COD_CTA`) e por grupo (`COD_SUP`).

### Processamento (A "Ponte Virtual")
Este processo ignora a omissão do arquivo atual e busca a verdade nos anos adjacentes.

1.  **Cálculo de Similaridade (Métrica de Cobertura)**:
    -   O sistema compara as contas analíticas (`IND_CTA == 'A'`) do ano alvo (ex: 2014) com anos anteriores (2013) e posteriores (2015).
    -   **Fórmula**: `Cobertura = (Contas Coincidentes / Total de Contas do Ano Alvo)`.
    -   Se a cobertura for > 50%, o ano vizinho é eleito como "Mestre de Mapeamento".
2.  **Criação da Ponte Literal (Funil de Três Rodadas)**:
    -   **Rodada 1 (Busca por Código no Vizinho)**: O sistema realiza uma busca literal do `COD_CTA` do ano alvo no vizinho eleito. Se a conta existir no vizinho, seu mapeamento é herdado.
    -   **Rodada 2 (Busca por Grupo no Vizinho)**: Para contas não localizadas na Rodada 1, o sistema busca o `COD_SUP` da conta no ano alvo e identifica qual o `COD_CTA_REF` mais frequente para esse mesmo grupo no vizinho.
    -   **Rodada 3 (Consenso Global)**: Caso as rodadas anteriores falhem, o sistema consulta a base de conhecimento completa de todos os anos processados (estatística histórica) para encontrar o mapeamento mais frequente para aquele `COD_CTA`.
3.  **Inferência de Schema**:
    -   Como o arquivo de 2014 não diz qual seu plano, o sistema assume o `COD_PLAN_REF` do vizinho ou o consenso histórico da empresa.
    -   **Consistência de Nomes**: O sistema busca o arquivo de estrutura (`.csv`) correspondente ao código e ano inferidos para garantir que as descrições das contas correspondam aos códigos "emprestados". 
4.  **Geração do Balancete**:
    -   Segue o processamento normal, utilizando o mapeamento "injetado" via memória histórica em vez de registros físicos `I051`.

### Outputs (Saídas)
-   **Internal DataFrame**: `04_Balancetes_RFB` (Gerado via ponte virtual).
-   **Regras da coluna `ORIGEM_MAP` nos Balancetes Mensais**:
    -   Preenchimento exclusivo para **contas analíticas** (`IND_CTA` = "A"). Contas sintéticas devem permanecer vazias neste campo.
    -   Valores possíveis:
        -   `I051`: O mapeamento veio do próprio arquivo ECD (registro I051).
        -   `ANO_COD_CTA`: Mapeamento herdado via conta idêntica no arquivo do ano informado (Ponte Rodada 1).
        -   `ANO_COD_SUP`: Mapeamento herdado via grupo superior no arquivo do ano informado (Ponte Rodada 2).
        -   `CONSENSO_HISTORICO`: Mapeamento recuperado da memória estatística global de todos os anos (Ponte Rodada 3).
        -   `SEM_MAPEAMENTO`: Nenhuma correspondência encontrada em nenhuma rodada.

---

## 3. Matriz de Input/Output de Processamento

| Etapa            | Input Principal                         | Ferramenta                            | Output Esperado                      |
| :--------------- | :-------------------------------------- | :------------------------------------ | :----------------------------------- |
| **Leitura**      | Arquivo .txt                            | `ECDReader`                           | Lista de Dicionários (Registros)     |
| **Inferência**   | Lista de Registros + `HistoricalMapper` | `HistoricalMapper.find_best_neighbor` | `COD_PLAN_REF` + Mapeamento Virtual  |
| **Consolidação** | Registros I155/I355 + Mapeamento        | `ECDProcessor.gerar_balancetes`       | DataFrame de Saldos agrupado por Ref |
| **Hierarquia**   | DataFrame de Saldos + CSV Referencial   | `ECDProcessor._propagar_hierarquia`   | Balancete Referencial Completo       |
| **Exportação**   | DataFrame Final                         | `ECDExporter`                         | Arquivo .xlsx / .parquet             |

---

## 4. Pontos de Melhoria e Evoluções

### 4.1 Memória Persistente (Banco de Dados de Conhecimento)
Atualmente, o `HistoricalMapper` opera em memória volátil, perdendo seu aprendizado ao final de cada execução do `main.py`.
- **Objetivo**: Implementar a persistência do conhecimento em um banco de dados (ex: SQLite ou arquivos Parquet de histórico).
- **Benefício**: Resolverá o problema de "Arquivos Órfãos". Se um arquivo problemático for processado sozinho, o sistema poderá consultar mapeamentos validados em execuções de meses ou anos anteriores, mesmo que os arquivos originais não estejam mais na pasta de entrada.
- **Fluxo**: Ao iniciar o aprendizado, o sistema carrega o "Cérebro Master" e, ao final, salva as novas descobertas.
