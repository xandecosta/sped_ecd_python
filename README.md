# SPED-ECD Parser Pro (v1.9.0)


## Sobre o Projeto
Este projeto consiste em um parser robusto para arquivos do SPED Contábil (ECD), desenvolvido em Python. O objetivo é processar e validar arquivos de escrituração contábil digital seguindo padrões de desenvolvimento sênior, garantindo precisão financeira absoluta e escalabilidade.

## Principais Funcionalidades
- **Gestão Referencial Integrada:** Motor completo para padronização e auditoria (evolução e integridade) dos planos de contas da Receita Federal.
- **Processamento em Lote (Batch):** Processa automaticamente todos os arquivos `.txt` na pasta de entrada.
- **Inteligência Contábil:** Baseado em schemas JSON hierárquicos, gera automaticamente chaves (PK/FK) e herança de saldos.
- **Motor de Balancetes:** Algoritmo *Bottom-Up* que propaga saldos de contas analíticas para sintéticas em todos os níveis.
- **Ajuste Pré-Fechamento:** Reversão inteligente de lançamentos de encerramento (tipo 'E') para análise de balancetes antes do zeramento, garantindo a integridade da equação $Inicial + Débitos - Créditos = Final$.
- **Precisão Financeira:** Uso mandatório de `decimal.Decimal` para evitar erros de arredondamento em auditorias.
- **Saídas Multiformato:** Exportação para **Parquet** (alta performance) e **Excel** (com prefixo de data para permitir múltiplas instâncias abertas).
- **Ponte Virtual (Cross-Temporal Bridging):** Motor de inferência forense que recupera mapeamentos de anos adjacentes para gerar balancetes RFB em exercícios omissos (ex: 2014).
- **Robustez Técnica:** Código 100% tipado e validado via **Pyright**, garantindo estabilidade contra erros de tipo e maior facilidade de manutenção.

## Estrutura do Projeto
- `/core`: Lógica principal (Reader, Processor).
- `/schemas`: Definições de layouts SPED e Planos Referenciais padronizados.
- `/utils`: Gestão referencial, exportador e ferramentas de consolidação.
- `/tests`: Testes unitários e de integração.
- `/data/input`: Local para colocar os arquivos ECD (.txt).
- `/data/output`: Resultados organizados por período (YYYYMMDD).

## Como Usar

### 1. Configurando o Ambiente
```bash
python -m venv venv
source venv/Scripts/activate # Windows
.\venv\Scripts\activate  # Windows alternative
source venv/bin/activate # Linux/Mac
pip install -r requirements.txt
```

### 2. Executando o Pipeline
1. **Prepare os Planos Referenciais:** Antes de processar seus arquivos ECD, você deve preparar a biblioteca de planos da RFB executando o gestor:
   ```bash
   python utils/ref_plan_manager.py
   ```
   *Isso irá baixar/converter os planos, gerar o catálogo e realizar a auditoria de integridade.*

2. **Processamento ECD:** Coloque seus arquivos ECD `.txt` na pasta `data/input` e execute o script principal:
   ```bash
   python main.py
   ```
3. Confira os resultados na pasta `data/output`. Os arquivos serão organizados assim:
   - Uma subpasta para cada data final (`YYYYMMDD`).
   - Arquivos nomeados com prefixo temporal (ex: `20231231_02_Balancete.xlsx`) para facilitar a análise comparativa no Excel.

## Desenvolvimento
Siga as regras definidas em `.cursorrules` para manter a consistência e qualidade do código. O histórico de mudanças pode ser acompanhado no [CHANGELOG.md](./CHANGELOG.md).
