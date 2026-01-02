# SPED-ECD Parser Pro (v1.5.0)

## Sobre o Projeto
Este projeto consiste em um parser robusto para arquivos do SPED Contábil (ECD), desenvolvido em Python. O objetivo é processar e validar arquivos de escrituração contábil digital seguindo padrões de desenvolvimento sênior, garantindo precisão financeira absoluta e escalabilidade.

## Principais Funcionalidades
- **Processamento em Lote (Batch):** Processa automaticamente todos os arquivos `.txt` na pasta de entrada.
- **Inteligência Contábil:** Baseado em schemas JSON hierárquicos, gera automaticamente chaves (PK/FK) e herança de saldos.
- **Motor de Balancetes:** Algoritmo *Bottom-Up* que propaga saldos de contas analíticas para sintéticas em todos os níveis.
- **Ajuste Pré-Fechamento:** Reversão inteligente de lançamentos de encerramento (tipo 'E') para análise de balancetes antes do zeramento, garantindo a integridade da equação $Inicial + Débitos - Créditos = Final$.
- **Precisão Financeira:** Uso mandatório de `decimal.Decimal` para evitar erros de arredondamento em auditorias.
- **Saídas Multiformato:** Exportação para **Parquet** (alta performance) e **Excel** (com prefixo de data para permitir múltiplas instâncias abertas).

## Estrutura do Projeto
- `/core`: Lógica principal (Reader, Processor).
- `/schemas`: Definições de layouts SPED por versão.
- `/utils`: Exportador e ferramentas de geração de schemas.
- `/tests`: Testes unitários e de integração.
- `/data/input`: Local para colocar os arquivos ECD (.txt).
- `/data/output`: Resultados organizados por período (YYYYMMDD).

## Como Usar

### 1. Configurando o Ambiente
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate # Linux/Mac
pip install -r requirements.txt
```

### 2. Executando o Pipeline
1. Coloque seus arquivos ECD `.txt` na pasta `data/input`.
2. Execute o script principal:
   ```bash
   python main.py
   ```
3. Confira os resultados na pasta `data/output`. Os arquivos serão organizados assim:
   - Uma subpasta para cada data final (`YYYYMMDD`).
   - Arquivos nomeados com prefixo temporal (ex: `20231231_02_Balancete.xlsx`) para facilitar a análise comparativa no Excel.

## Desenvolvimento
Siga as regras definidas em `.cursorrules` para manter a consistência e qualidade do código. O histórico de mudanças pode ser acompanhado no [CHANGELOG.md](./CHANGELOG.md).
