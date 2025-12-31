from core.reader_ecd import ECDReader
from core.processor import ECDProcessor
import os
import glob
import pandas as pd


def diagnosticar():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(base_dir, "data", "input")
    arquivos = glob.glob(os.path.join(input_dir, "*.txt"))

    if not arquivos:
        print("Nenhum arquivo encontrado.")
        return

    arquivo = arquivos[0]
    print(f"Analisando: {os.path.basename(arquivo)}")

    reader = ECDReader(arquivo)
    registros = list(reader.processar_arquivo())
    processor = ECDProcessor(registros)

    def check_dupes(name, df):
        if df is None:
            return
        dupes = df.columns[df.columns.duplicated()].tolist()
        if dupes:
            print(f"!!! Tabela '{name}' tem colunas duplicadas: {dupes}")
        else:
            print(f"Tabela '{name}' OK.")

    df_plano = processor.processar_plano_contas()
    check_dupes("Plano", df_plano)

    df_lctos = processor.processar_lancamentos(df_plano)
    check_dupes("Lancamentos", df_lctos)

    df_saldos = processor.processar_saldos_mensais()
    check_dupes("Saldos", df_saldos)

    df_balancete = processor.gerar_balancetes()
    check_dupes("Balancete", df_balancete)

    demos = processor.processar_demonstracoes()
    check_dupes("BP", demos["BP"])
    check_dupes("DRE", demos["DRE"])


if __name__ == "__main__":
    diagnosticar()
