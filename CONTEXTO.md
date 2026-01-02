# Contexto do Projeto: SPED-ECD Parser Pro

## Estado Atual
- **Data:** 01/01/2026
- **Versão:** 1.2 (Melhoria de Integridade e UX)
- **Status:** Pipeline de processamento em lote robusto, com suporte a reversão de encerramento matematicamente íntegra e organização de arquivos otimizada para Excel.

## O Que Foi Feito
> Para o histórico detalhado de todas as versões, consulte o [CHANGELOG.md](./CHANGELOG.md).

1.  **Integridade Contábil (Ajuste Pré-Fechamento):**
    - Implementação de lógica de reversão de lançamentos de encerramento (tipo 'E').
    - **Correção Matemática:** O ajuste agora subtrai valores de `VL_DEB` e `VL_CRED`, mantendo a equação $Inicial + Débitos - Créditos = Final$ válida mesmo após "deszerar" o saldo.
2.  **Melhoria de UX (Exportação):**
    - **Prefixo Temporal:** Adição de prefixo `YYYYMMDD_` nos nomes dos arquivos (Excel e Parquet).
    - **Resolução de Conflitos:** Permite abrir simultaneamente múltiplos balancetes de diferentes períodos no Microsoft Excel.
3.  **Processamento em Lote (Batch):**
    - Refinamento do pipeline para passar metadados do período (id_folder) durante todo o fluxo de exportação.
4.  **Estabilidade do Motor:**
    - Tratamento resiliente de tipos `Decimal` e nulos (`NaN`) durante o merge de ajustes de encerramento.

## Próximos Passos
- Implementar interface visual ou CLI avançada para seleção de arquivos.
- Adicionar validações cruzadas entre Razão (I200/I250) e Balancete (I155).
- Integração nativa com DuckDB para consultas SQL de alta performance em grandes lotes.

