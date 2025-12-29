# SPED-ECD Parser Pro

## Sobre o Projeto
Este projeto consiste em um parser robusto para arquivos do SPED Contábil (ECD), desenvolvido em Python. O objetivo é processar e validar arquivos de escrituração contábil digital seguindo padrões de desenvolvimento sênior.

## Estrutura do Projeto
- `/core`: Lógica principal de processamento e parsing.
- `/schemas`: Definições de layouts (JSON) das versões do ECD.
- `/tests`: Testes unitários automatizados.
- `/utils`: Funções utilitárias e auxiliares.

## Configuração do Ambiente

### Pré-requisitos
- Python 3.10 ou superior

### Configurando o Virtual Environment (venv)

1. **Crie o ambiente virtual:**
   ```bash
   python -m venv venv
   ```

2. **Ative o ambiente virtual:**
   - No Windows (CMD/PowerShell):
     ```bash
     .\venv\Scripts\activate
     ```
   - No Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

3. **Instale as dependências (futuro):**
   ```bash
   pip install -r requirements.txt
   ```

## Desenvolvimento
Siga as regras definidas em `.cursorrules` para manter a consistência e qualidade do código.
