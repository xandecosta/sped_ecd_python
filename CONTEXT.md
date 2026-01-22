# Contexto do Projeto: SPED-ECD Parser Pro

## Estado Atual

- **Data:** 15/01/2026
- **Versão:** 1.9.0 (Arquitetura de Ponte Virtual - Bridging)
- **Status:** Balancete baseRFB gerado com sucesso para anos omissos (ex: 2014) via inferência histórico-temporal. Auditoria de mapeamento integrada aos balancetes mensais.

## O Que Foi Feito

> Para o histórico detalhado de todas as versões, consulte o [CHANGELOG.md](./CHANGELOG.md).

1. **Mapeamento e Consolidação RFB (V2.0 Core):**
    - Implementação de processos que viabilizam o mapeamento de contas analíticas para o plano referencial da RFB.
    - Consolidação de balancetes no formato referencial, permitindo auditoria direta contra o "Balancete baseRFB".
2. **Ponte Virtual (Virtual I051):**
    - Criação do módulo `HistoricalMapper` para aprender mapeamentos de anos adjacentes e preencher lacunas de arquivos sem registro I051.
    - Implementação de "Funil de 3 Rodadas" (Identidade, Grupo e Consenso Global).
    - Documentação detalhada do processo em [`bridging_logic.md`](./docs/architecture/bridging_logic.md).
3. **Unificação de Gestão Referencial:**
    - Fim da fragmentação de scripts em `utils/`. O `RefPlanManager.py` agora centraliza padronização, auditoria e descoberta de layouts.
4. **Novo Motor de Auditoria e Integridade:**
    - Implementação de pipeline multitarefa que gera relatórios de evolução histórica e detecta conflitos estruturais.
5. **Saneamento e Estabilização:**
    - Limpeza de arquivos CSV obsoletos e automação da regeração de schemas.
    - Estabilização técnica com conformidade Pyright (typing.cast) em todo o pipeline.

## Roadmap e Evolução Arquitetônica (v2.0+)

### 1. Infraestrutura de Dados (Próximos Passos)

- **Integração DuckDB (Planejado):** Implementar o DuckDB como motor de persistência para permitir consultas transversais em toda a série histórica de balancetes consolidados.
- **Consolidação Temporal:** Unificação de múltiplos anos em um único "Data Lake Contábil".

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
