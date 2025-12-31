# Contexto do Projeto: SPED-ECD Parser Pro

## Estado Atual
- **Data:** 31/12/2025
- **Fase:** Qualidade e Infraestrutura (Testes)
- **Status:** Suíte de testes 100% robusta e independente de dados reais. Core validado.

## O Que Foi Feito
1.  **Refinamento de Testes Unitários:**
    - **Mocks Dinâmicos:** Uso de `tmp_path` do pytest para gerar arquivos ECD sob demanda na memória. O projeto não depende mais de arquivos externos para rodar os testes.
    - **Testes de Exceção:** Verificação de tratamento de erros para arquivos inexistentes.
    - **Validação de Ciclo de Vida:** Confirmação de que o `periodo_ecd` é capturado corretamente no registro `0000`.
    - **Limpeza de Código:** Remoção de variáveis não utilizadas e avisos de lint no arquivo de testes.

2.  **Ajustes no Core (v2.2.1):**
    - **Correção de Indexação:** Ajustado o offset para `i+1` para alinhar corretamente os campos do layout (incluindo o `REG`).

## Próximos Passos
- Implementar o módulo de **Exportação** (`core/exporter.py`) para consolidar DataFrames.
- Integração de blocos e salvamento em Parquet.
