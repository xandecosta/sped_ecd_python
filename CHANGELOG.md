# Changelog - SPED-ECD Parser Pro

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo. O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-br/1.0.0/).

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
