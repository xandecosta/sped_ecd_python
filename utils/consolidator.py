import os
import pandas as pd
import logging
from typing import Any


class ECDConsolidator:
    """
    Consolida múltiplos outputs de períodos individuais em arquivos únicos.
    """

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.consolidated_dir = os.path.join(output_dir, "consolidado")
        self.tables = [
            "01_BP",
            "02_DRE",
            "03_Balancetes_Mensais",
            "04_Balancete_baseRFB",
            "05_Plano_Contas",
            "06_Lancamentos_Contabeis",
        ]
        self.excel_tables = ["01_BP", "02_DRE", "03_Balancetes_Mensais"]

    def _preparar_pasta(self):
        if not os.path.exists(self.consolidated_dir):
            os.makedirs(self.consolidated_dir)

    def consolidar(self):
        """
        Percorre as pastas de saída e agrupa os dados por tabela.
        """
        print("\n>>> INICIANDO CONSOLIDAÇÃO DOS RELATÓRIOS...")
        self._preparar_pasta()

        # Localiza todas as subpastas de período (não recursivo, apenas filhos diretos)
        subpastas = [
            os.path.join(self.output_dir, f)
            for f in os.listdir(self.output_dir)
            if os.path.isdir(os.path.join(self.output_dir, f)) and f != "consolidado"
        ]

        if not subpastas:
            print("      [AVISO] Nenhuma pasta de período encontrada para consolidar.")
            return

        for tabela in self.tables:
            dfs = []
            print(f"      Processando: {tabela}")

            for pasta in subpastas:
                # O nome do arquivo no disco segue o padrão YYYYMMDD_Tabela.parquet
                periodo = os.path.basename(pasta)
                arquivo_parquet = os.path.join(pasta, f"{periodo}_{tabela}.parquet")

                if os.path.exists(arquivo_parquet):
                    try:
                        df = pd.read_parquet(arquivo_parquet)
                        if not df.empty:
                            dfs.append(df)
                    except Exception as e:
                        logging.error(f"Erro ao ler {arquivo_parquet}: {e}")

            if dfs:
                df_final = pd.concat(dfs, ignore_index=True)

                # 1. Salva Parquet Consolidado
                path_parquet = os.path.join(
                    self.consolidated_dir, f"consolidado_{tabela}.parquet"
                )
                df_final.to_parquet(path_parquet, index=False, engine="pyarrow")

                # 2. Salva Excel Consolidado (apenas se estiver na lista permitida)
                if any(tabela.startswith(prefix) for prefix in self.excel_tables):
                    path_excel = os.path.join(
                        self.consolidated_dir, f"consolidado_{tabela}.xlsx"
                    )
                    # Proteção simples contra limite de linhas do Excel
                    if len(df_final) < 1048576:
                        df_final.to_excel(path_excel, index=False, engine="openpyxl")
                    else:
                        logging.warning(
                            f"Tabela {tabela} excedeu limite do Excel ({len(df_final)} linhas). Excel não gerado."
                        )
            else:
                print(f"      [AVISO] Dados não encontrados para a tabela {tabela}")

        print(f"      [OK] Consolidação finalizada em: {self.consolidated_dir}")


if __name__ == "__main__":
    # Teste manual rápido
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_dir, "data", "output")
    consolidator = ECDConsolidator(output_path)
    consolidator.consolidar()
