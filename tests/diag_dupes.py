from core.reader_ecd import ECDReader
from core.processor import ECDProcessor
import os
import glob


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

    # Nota: processar_saldos_mensais não existe mais como método público independente,
    # ele foi integrado ao gerar_balancetes().
    res_balancetes = processor.gerar_balancetes()
    for nome, df in res_balancetes.items():
        check_dupes(f"Balancete_{nome}", df)

    res_demos = processor.processar_demonstracoes()
    for nome, df in res_demos.items():
        check_dupes(f"Demo_{nome}", df)


if __name__ == "__main__":
    diagnosticar()
