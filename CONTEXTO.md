# Contexto do Projeto: SPED-ECD Parser Pro

## Estado Atual
- **Data:** 31/12/2025
- **Versão:** 1.1 (Estável - Batch Processing)
- **Status:** Pipeline de processamento em lote concluído com organização automática por período contábil.

## O Que Foi Feito
1.  **Versão 1.1 - Refinamento e Estabilidade:**
    - **Soma de Decimais:** Correção crítica na agregação hierárquica usando lambdas robustos para tipos `Decimal`.
    - **Limpeza de Dados:** Eliminação de colunas redundantes (`REG` global) para garantir exportação limpa para Parquet.
2.  **Processamento em Lote (Batch):**
    - Implementação de loop resiliente em `main.py` para processar múltiplos arquivos sequencialmente.
    - Isolamento de erros: falhas em um arquivo não interrompem o restante do lote.
3.  **Organização Organizacional:**
    - **Nomenclatura Dinâmica:** Subpastas de saída nomeadas pela data final do período (`YYYYMMDD`).
    - **Estrutura Flat:** Agrupamento de Parquet e Excel em uma única pasta por período, facilitando o acesso.
4.  **Core e Testes:**
    - Testes unitários 100% automatizados com mocks.
    - Classe `ECDProcessor` documentada com lógica contábil detalhada.

## Próximos Passos
- Implementar interface CLI amigável para seleção de arquivos.
- Adicionar validações de integridade entre Razão (I200) e Balancete (I155).
- Estudar integração com bases de dados SQL (DuckDB/PostgreSQL).
