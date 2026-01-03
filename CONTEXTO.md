# Contexto do Projeto: SPED-ECD Parser Pro

## Estado Atual
- **Data:** 03/01/2026
- **Versão:** 1.6.0 (Modernização da Biblioteca Referencial e Organização de Schemas)
- **Status:** Estrutura de schemas reorganizada. Biblioteca de planos referenciais migrada para CSV e padronizada para 9 colunas.

## O Que Foi Feito
> Para o histórico detalhado de todas as versões, consulte o [CHANGELOG.md](./CHANGELOG.md).

1.  **Modernização da Biblioteca Referencial:**
    *   Migração de JSON para CSV (UTF-8, pipe-separated) para todos os planos da RFB.
    *   Correção de alinhamento de colunas (fixo em 9 colunas) eliminando erros de deslocamento de dados.
2.  **Arquitetura de Schemas Organizada:**
    *   Separação física entre Leiautes da ECD (`/schemas/ecd_layouts`) e Planos Referenciais (`/schemas/ref_plans`).
    *   Remoção de índices redundantes e consolidação no catálogo hierárquico único.
3.  **Refatoração de Utilitários:**
    *   Renomeação de scripts na pasta `utils` para nomes semânticos (Standardizer, Discovery, Compiler).
    *   Atualização do `ECDReader` para suportar a nova estrutura de diretórios.
4.  **Estabilização Forense:**
    *   Reversão de lógica experimental no motor core para manter foco na estabilidade analítica v1.5.

## Próximos Passos
- Implementar interface visual ou CLI avançada para seleção de arquivos.
- Integração nativa com DuckDB para consultas SQL de alta performance em grandes lotes.
- Re-integrar o Balancete BaseRFB utilizando a nova biblioteca CSV padronizada.

