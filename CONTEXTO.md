# Contexto do Projeto: SPED-ECD Parser Pro

## Estado Atual
- **Data:** 05/01/2026
- **Versão:** 1.7.0 (Tipagem Estática e Estabilização de Testes)
- **Status:** Balancete baseRFB totalmente funcional. Código refatorado para conformidade com Pyright e infraestrutura de testes corrigida.

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
5.  **Robustez Técnica e Tipagem:**
    *   Refatoração profunda para conformidade com **Pyright**, elevando a segurança do código contra erros de tipo em tempo de execução.
    *   Estabilização do ambiente de testes de integração com correção de caminhos e mocks.


## Roadmap e Evolução Arquitetônica (v2.0 - Visão Forense)

Este roadmap define a estratégia para transformar o parser em uma plataforma de auditoria de larga escala. A prioridade é "Data-First": primeiro garantimos a fluidez e persistência dos dados, para depois aplicar inteligência semântica e validações periciais.

### 1. Infraestrutura de Dados e Performance (O Alicerce)
*Foco: Garantir que séries históricas grandes sejam processáveis e consultáveis sem estourar a memória RAM.*
- **Integração DuckDB:** Implementar o DuckDB como motor de persistência e consulta. Os arquivos Parquet gerados pelo ETL serão tratados como um "Data Lake Contábil" unificado.
- **Consolidação Temporal:** Criar lógica de unificação para permitir consultas transversais em toda a série histórica (ex: "Evolução do saldo da conta X de 2014 a 2025").
- **Log de Auditoria de Transformação:** Implementar um registro de rastreabilidade que vincule cada linha do banco de dados ao arquivo TXT de origem, garantindo segurança jurídica em perícias.

### 2. Transição para Modelos de Domínio (A Inteligência)
*Foco: Evoluir de tabelas genéricas para objetos que "entendem" as regras do SPED e da contabilidade.*
- **Entidades de Domínio (POO):** Implementar classes `Conta`, `Lancamento` e `Empresa` utilizando `Dataclasses` ou `Pydantic`.
- **Encapsulamento Contábil:** Mover a lógica de sinais (Devedor/Credor), natureza de conta e o algoritmo *Bottom-Up* para dentro dos métodos destas classes.
- **Validação de Tipagem Forte:** Garantir integridade financeira absoluta (Decimal) e de datas no momento da criação dos objetos, isolando erros de entrada (input).

### 3. Auditoria Forense e Integridade (A Prova)
*Foco: Automatizar o "pente fino" contábil nos séries históricas consolidadas.*
- **Testes de Continuidade (Forward Roll):** Validação automática se o Saldo Final de um exercício é exatamente o Saldo Inicial do exercício seguinte em toda a linha do tempo.
- **Cruzamentos de Dados (Cross-Check):** Implementar via SQL (DuckDB) o cruzamento entre os Registros de Lançamentos (I200/I250) e o Balancete (I155/I157).
- **Integridade Hierárquica:** Testar se a soma das contas analíticas coincide com os totais das contas sintéticas em todos os níveis e períodos.

### 4. Abstração e Interface (A Entrega)
*Foco: Tornar a ferramenta extensível a novos impostos e amigável para o usuário.*
- **BaseReader Abstrato:** Interface para permitir a inclusão de novos módulos (ECF, EFD-Contribuições) sem alterar o núcleo do motor de processamento.
- **Geradores de Relatórios (Strategy Pattern):** Módulos independentes para geração de Balanço Patrimonial, DRE e análises horizontais/verticais.
- **CLI/Interface de Usuário:** Desenvolver um painel de controle para gestão de lotes de arquivos e monitoramento do progresso do processamento histórico.

### 5. Algoritmo de Detecção do Plano Referencial (Funil de Metadados)
*Módulo de estabilidade para garantir a aplicação correta das tabelas da RFB ao longo das décadas:*
1. **Extração do DNA:** Identifica `COD_PLAN_REF` e o ano de vigência.
2. **Filtragem por Instituição:** Localiza a entidade no catálogo referencial.
3. **Filtragem por Vigência:** Cruza a data do arquivo com os períodos de validade dos planos.
4. **Resolução Física:** Mapeia e carrega o CSV correspondente para o motor analítico.

*Este roadmap serve como bússola para futuras iterações, garantindo que o projeto evolua de uma ferramenta de processamento para uma plataforma de inteligência pericial contábil.*

