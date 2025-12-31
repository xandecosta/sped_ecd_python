from core.reader_ecd import ECDReader
from core.processor import ECDProcessor
import os
import glob
import pandas as pd


def test_integracao():
    # 1. Encontrar um arquivo de teste
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(base_dir, "data", "input")
    arquivos = glob.glob(os.path.join(input_dir, "*.txt"))

    if not arquivos:
        print("Nenhum arquivo de teste encontrado.")
        return

    arquivo = arquivos[0]
    print(f"--- Iniciando Teste de Integração: {os.path.basename(arquivo)} ---")

    # 2. Ler o arquivo
    reader = ECDReader(arquivo)
    registros = list(reader.processar_arquivo())  # Carrega em memória para o DataFrame
    print(f"Total de registros lidos: {len(registros)}")

    # 3. Processar para DataFrames
    proc = ECDProcessor(registros)

    # 4. Validar Plano de Contas
    df_plano = proc.processar_plano_contas()
    print(f"Plano de Contas (I050): {len(df_plano)} contas.")
    if not df_plano.empty:
        print(f"Exemplo: {df_plano.iloc[0].to_dict()}")

    # 5. Validar Saldos Mensais
    df_saldos = proc.processar_saldos_mensais()
    print(f"Saldos Mensais (I150+I155): {len(df_saldos)} registros.")

    # 6. Validar Lançamentos
    df_lctos = proc.processar_lancamentos(df_plano)
    print(f"Lançamentos (I200+I250): {len(df_lctos)} itens diários.")
    if not df_lctos.empty:
        print(f"Exemplo Lcto: {df_lctos.iloc[0].to_dict()}")


if __name__ == "__main__":
    test_integracao()
