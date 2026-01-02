# Contexto do Projeto: SPED-ECD Parser Pro

## Estado Atual
- **Data:** 02/01/2026
- **Versão:** 1.3 (Continuidade Histórica e Refinamento de UX)
- **Status:** Pipeline robusto com suporte a Forward Roll (continuidade de saldos) e priorização de relatórios financeiros na exportação.

## O Que Foi Feito
> Para o histórico detalhado de todas as versões, consulte o [CHANGELOG.md](./CHANGELOG.md).

1.  **Sincronização de Saldos (Forward Roll):**
    - Implementação de lógica de continuidade histórica no `processor.py`.
    - **Regra de Negócio:** O saldo inicial de um mês é agora forçado a ser o saldo final (já ajustado) do mês anterior. Isso resolve a quebra de sequência causada por encerramentos trimestrais ou mensais no SPED.
2.  **Arquitetura de Exportação e UX:**
    - **Priorização:** Relatórios de Balanço Patrimonial (BP) e DRE agora encabeçam a lista de exportação (`01_` e `02_`).
    - **Reforço de Formato:** Garantia de exportação Excel para todos os relatórios analíticos e sintéticos essenciais.
3.  **Integridade Contábil (Ajuste Pré-Fechamento):**
3.  **Processamento em Lote (Batch):**
    - Refinamento do pipeline para passar metadados do período (id_folder) durante todo o fluxo de exportação.
4.  **Estabilidade do Motor:**
    - Tratamento resiliente de tipos `Decimal` e nulos (`NaN`) durante o merge de ajustes de encerramento.

## Próximos Passos
- Implementar interface visual ou CLI avançada para seleção de arquivos.
- Adicionar validações cruzadas entre Razão (I200/I250) e Balancete (I155).
- Integração nativa com DuckDB para consultas SQL de alta performance em grandes lotes.

