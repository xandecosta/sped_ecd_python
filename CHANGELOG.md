# Changelog - SPED-ECD Parser Pro

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo. O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-br/1.0.0/).

## [1.6.0] - 2026-01-03
### Adicionado
- **Suporte Nativo a CSV:** Planos referenciais agora são armazenados em CSV (UTF-8, delimitador pipe) para maior performance e facilidade de conferência.
- **Estrutura de Schemas Categorizada:** Criação da subpasta `ecd_layouts` e `ref_plans` para separar definições da ECD de dados da RFB.

### Alterado
- **Padronização de Dados:** Correção do alinhamento de colunas em todos os planos referenciais (garantindo 9 colunas fixas).
- **Refatoração Semântica:** Renomeação dos scripts utilitários em `utils/` para nomes descritivos: `ref_plan_standardizer.py`, `ref_plan_discovery.py` e `ecd_layout_compiler.py`.
- **Motor Core:** Atualização do `ECDReader` para carregar definições da nova estrutura de pastas.

### Removido
- **Redundância:** Supressão do arquivo `ref_index.json` e do script `compile_ref_index.py`.

## [1.5.0] - 2026-01-02
### Alterado
- **Estabilização do Motor Core:** Simplificação das classes `ECDReader` e `ECDProcessor`, removendo métodos experimentais de mapeamento referencial para garantir 100% de estabilidade nas análises periciais.
- **Padronização PT-BR:** Refatoração sistemática de termos em Português de Portugal para Português do Brasil (ex: "ficheiro" -> "arquivo") no código, testes e logs.
- **Arquitetura de Exportação:** Renomeação do log de auditoria para `Arquivos_Gerados.txt` e inclusão de dependência `pyarrow` no workflow.

## [1.4.0] - 2026-01-02 (Pesquisa Técnica)
### Nota de Desenvolvimento
- **Mapeamento RFB (Shelved):** Durante esta fase, foi testada a integração com o Plano de Contas Referencial da Receita Federal. Devido à complexidade de manutenção das tabelas dinâmicas, a funcionalidade foi engavetada para priorizar o motor analítico direto. A v1.5.0 consolida a versão estável sem este módulo.
- **Suporte ao Registro I157:** Implementação mantida para assegurar a continuidade histórica em transferências de planos de contas.

## [1.3.0] - 2026-01-02
### Adicionado
- **Continuidade Histórica (Forward Roll):** Implementação de transporte automático de saldo final para o inicial do mês seguinte. Isso garante a integridade da série temporal mesmo em arquivos com encerramentos mensais ou trimestrais.
- **Priorização de Relatórios:** Reorganização do pipeline de exportação para que as demonstrações contábeis (BP e DRE) sejam os primeiros arquivos da lista (`01_BP.xlsx`, `02_DRE.xlsx`).

### Alterado
- **Fluxo de Processamento:** Ajuste na ordem de execução do `main.py` para gerar demonstrações antes do processamento dos planos de contas e lançamentos, otimizando a disponibilidade de dados.
- **Configuração de Exportação:** Reforço na lista de termos para exportação compulsória em Excel no `exporter.py`.

## [1.2.0] - 2026-01-01
### Adicionado
- **Prefixo Temporal:** Inclusão de prefixo `YYYYMMDD_` nos arquivos exportados (Excel e Parquet). Isso resolve o bloqueio do Excel que impedia a abertura simultânea de múltiplos balancetes de diferentes períodos.
- **Tratamento de Tipos:** Conversão resiliente de nulos para `Decimal("0.00")` durante o merge de ajustes de encerramento, evitando erros de cálculo em contas sem movimentação.

### Corrigido
- **Integridade Contábil:** Ajuste crítico na reversão de lançamentos de encerramento (tipo 'E'). Agora, além do saldo final, os valores são subtraídos de `VL_DEB` e `VL_CRED`, garantindo que a equação $Saldo Inicial + Débitos - Créditos = Saldo Final$ permaneça válida matematicamente.

## [1.1.0] - 2025-12-31
### Adicionado
- **Batch Processing:** Implementação de processamento em lote resiliente. O sistema agora processa todos os arquivos `.txt` da pasta de entrada sequencialmente, sem interromper o fluxo em caso de erro em um arquivo isolado.
- **Organização por Período:** Criação automática de pastas de saída nomeadas pela data final (`YYYYMMDD`) extraída do registro `0000`.
- **Estrutura Flat:** Simplificação da estrutura de saída, salvando arquivos diretamente na pasta do período sem subdiretórios redundantes.

### Alterado
- **Refatoração Core:** Otimização na detecção de colunas e remoção do campo global `REG` das tabelas finais para garantir um output mais limpo no Parquet.
- **Testes Unitários:** Implementação de mocks dinâmicos usando `tmp_path` (pytest), permitindo testes 100% em memória sem dependência de arquivos físicos externos.

## [1.0.0] - 2025-12-31
### Adicionado
- **Release Inicial:** Pipeline completo de ETL (Extract, Transform, Load).
- **Motor de Propagação:** Implementação do algoritmo *Bottom-Up* em `ECDProcessor` para consolidar saldos de contas analíticas para sintéticas em todos os níveis.
- **Módulo Exporter:** Suporte a exportação multiformato (Parquet para performance e Excel para conferência).

## [0.5.0] - 2025-12-31
### Adicionado
- **Arquitetura PK/FK:** Introdução de chaves primárias baseadas em `DT_FIN` + `LINHA` e chaves estrangeiras para manter a integridade entre registros pai e filho.
- **Precisão Financeira:** Adoção mandatória do tipo `decimal.Decimal` em todo o processamento de valores para evitar erros de ponto flutuante.

## [0.2.0] - 2025-12-30
### Adicionado
- **Detecção Dinâmica:** Identificação automática da versão do layout SPED via registro `I010`.
- **Gerador de Schemas:** Script utilitário para converter as tabelas de parametrização do SPED em schemas JSON hierárquicos.
- **Leitura Otimizada:** Uso de Generators e `yield` para processar arquivos de grande porte com baixo consumo de memória.

## [0.1.0] - 2025-12-29
### Adicionado
- Estrutura inicial do projeto (pastas, `venv`, `.gitignore`).
- Documentação base (`README.md`, `CONTEXTO.md`).
- Regras de desenvolvimento em `.cursorrules`.
