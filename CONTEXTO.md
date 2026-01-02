# Contexto do Projeto: SPED-ECD Parser Pro

## Estado Atual
- **Data:** 02/01/2026
- **Versão:** 1.5 (Estabilização e Padronização PT-BR)
- **Status:** Motor core estabilizado. A tentativa de integração com o Plano Referencial RFB (v1.4 - Experimental) foi documentada e engavetada para priorizar a performance do motor analítico analítico de auditoria.

## O Que Foi Feito
> Para o histórico detalhado de todas as versões, consulte o [CHANGELOG.md](./CHANGELOG.md).

1.  **Padronização PT-BR:**
    - Refatoração completa de nomenclaturas de "ficheiro" para "arquivo".
2.  **Pesquisa Técnica (RFB):**
    - Foi realizado um protótipo de leitura de tabelas da Receita Federal. O código foi simplificado na v1.5 para manter o foco no plano de contas da empresa.
3.  **Continuidade em Mudanças de Software (Registro I157):**
    - Suporte ao Registro I157 mantido para assegurar o *Forward Roll* em casos de transferência de saldos.
4.  **Consolidação de Dependências:**
    - Estabilização do ambiente Python com a instalação e configuração do `pyarrow` para exportações de alta performance.

## Próximos Passos
- Implementar interface visual ou CLI avançada para seleção de arquivos.
- Adicionar validações cruzadas entre Razão (I200/I250) e Balancete (I155).
- Integração nativa com DuckDB para consultas SQL de alta performance em grandes lotes.

