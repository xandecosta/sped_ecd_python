# SPED-ECD Parser Pro (v1.1)

## Sobre o Projeto
Este projeto consiste em um parser robusto para arquivos do SPED Contábil (ECD), desenvolvido em Python. O objetivo é processar e validar arquivos de escrituração contábil digital seguindo padrões de desenvolvimento sênior, garantindo precisão financeira absoluta e escalabilidade.

## Principais Funcionalidades
- **Processamento em Lote (Batch):** Processa automaticamente todos os arquivos `.txt` na pasta de entrada.
- **Inteligência Contábil:** Baseado em schemas JSON hierárquicos, gera automaticamente chaves (PK/FK) e herança de saldos.
- **Motor de Balancetes:** Algoritmo *Bottom-Up* que propaga saldos de contas analíticas para sintéticas em todos os níveis.
- **Precisão Financeira:** Uso mandatório de `decimal.Decimal` para evitar erros de arredondamento em auditorias.
- **Saídas Multiformato:** Exportação automática para **Parquet** (alta performance) e **Excel** (conferência humana).

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
3. Confira os resultados na pasta `data/output`, onde cada período terá sua própria pasta contendo os arquivos Parquet e Excel.

## Desenvolvimento
Siga as regras definidas em `.cursorrules` para manter a consistência e qualidade do código.
