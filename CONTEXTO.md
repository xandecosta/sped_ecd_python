# Contexto do Projeto: SPED-ECD Parser Pro

## Estado Atual
- **Data:** 03/01/2026
- **Versão:** 1.6.1 (Integração Referencial I051 e Sincronização de Bases)
- **Status:** Plano de contas integrado com mapeamento referencial. Bases CSV sincronizadas com novos códigos de instituição (10 e 20).

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

## Roadmap e Evolução Arquitetônica

O projeto segue um crescimento orgânico e estabilizado. Para manter a escalabilidade e a saúde do código a longo prazo, as seguintes diretrizes de arquitetura e POO (Programação Orientada a Objetos) foram estabelecidas como prioridades futuras:

### 1. Transição para Modelos de Domínio (POO Madura)
- **Entidades Contábeis:** Evoluir de DataFrames para objetos de domínios como `Conta`, `Lancamento` e `Balancete`.
- **Encapsulamento:** Mover regras de negócio (ex: `is_analitica`, `validar_partida_dobrada`) para dentro destas classes, reduzindo o tamanho do `processor.py`.

### 2. Abstração e Plug-and-Play
- **BaseReader:** Implementar uma interface abstrata para permitir o suporte a novos formatos de entrada (ECF, EFD, PDFs bancários) sem alterar o motor core.
- **Validação com Fortes Tipos:** Utilizar `Dataclasses` ou `Pydantic` para garantir a integridade dos dados logo na entrada (`Reader`).

### 3. Desacoplamento de Relatórios (Strategy Pattern)
- Separar a geração de BP, DRE e Balancetes em geradores específicos (ex: `ProfitLossGenerator`), facilitando testes unitários isolados e manutenção focada.

### 4. Upgrade de Performance e UX
- **DuckDB Integration:** Substituir ou apoiar o Pandas com DuckDB para realizar joins de auditoria (ex: I150 x I155) em grandes lotes com alta performance.
- **Auditoria Reversível:** Implementar um log de transformação de dados que permita rastrear e justificar cada alteração de saldo, garantindo segurança jurídica para perícias contábeis.
- **CLI/Interface Avançada:** Desenvolver uma interface mais robusta para seleção de arquivos e acompanhamento do progresso de processamento.

### 5. Algoritmo de Detecção do Plano Referencial (Funil de Metadados)
O sistema utiliza um "Funil de Seleção" baseado no Registro `0000` para garantir que o plano de contas da Receita Federal (RFB) aplicado seja o correto para o período e instituição:

1.  **Extração do DNA:** Captura `COD_PLAN_REF` (Instituição) e o Ano da `DT_FIN` (Vigência) do Registro `0000`.
2.  **Filtragem por Instituição:** Busca a chave primária no `ref_catalog.json` correspondente ao código.
3.  **Filtragem por Vigência (Range):** Localiza a faixa de anos (`range: [min, max]`) que engloba o ano do arquivo.
4.  **Seleção por Versão:** Dentro da faixa, identifica os planos disponíveis (`plans`), selecionando o `alias` desejado e priorizando a **maior versão** disponível.
5.  **Resolução Física:** Mapeia o nome do arquivo CSV padronizado em `schemas/ref_plans/data/` para carregamento imediato via DuckDB/Pandas.

---
*Este roadmap serve como bússola para futuras iterações, garantindo que o projeto evolua de uma ferramenta de processamento para uma plataforma de inteligência pericial contábil.*

