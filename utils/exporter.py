import pandas as pd
import os
import logging
from datetime import datetime
from typing import Dict


class ECDExporter:
    def __init__(self, path_saida: str):
        """
        Inicializa o exportador.
        Args:
            path_saida: Caminho base onde os arquivos serão salvos (ex: output/20211231).
        """
        self.path_saida = path_saida
        self.output_base = os.path.dirname(path_saida)
        self.id_folder = os.path.basename(path_saida)
        self._preparar_pastas()

    def _preparar_pastas(self) -> None:
        """Garante a existência da pasta de saída individual."""
        if not os.path.exists(self.path_saida):
            os.makedirs(self.path_saida)

    @staticmethod
    def aplicar_formatacao_regional(df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica formatação PT-BR seguindo as regras:
        - Colunas DT_*: Data DD/MM/AAAA
        - Colunas VL_*: Valor com vírgula decimal
        """
        df_out = df.copy()
        for col in df_out.columns:
            col_str = str(col).upper()

            # 1. Datas (Prefixo DT_)
            if col_str.startswith("DT_"):
                if pd.api.types.is_datetime64_any_dtype(df_out[col]):
                    df_out[col] = df_out[col].dt.strftime("%d/%m/%Y")
                else:
                    # Caso seja string ou outro tipo, tenta converter e formatar
                    try:
                        df_out[col] = pd.to_datetime(df_out[col]).dt.strftime(
                            "%d/%m/%Y"
                        )
                    except Exception:
                        pass

            # 2. Valores (Prefixo VL_)
            elif col_str.startswith("VL_"):
                # Converte para string com vírgula decimal
                df_out[col] = df_out[col].apply(
                    lambda x: str(x).replace(".", ",") if pd.notna(x) else ""
                )

        return df_out

    def exportar_lote(
        self,
        dicionario_dfs: Dict[str, pd.DataFrame],
        nome_base: str,
        prefixo: str = "",
        itens_adicionais: list = [],
    ) -> None:
        """
        Exporta DataFrames para Parquet e Excel e centraliza logs.
        """
        log_gerados = []

        for nome_tabela, df in dicionario_dfs.items():
            if df is None or df.empty:
                continue

            nome_final = f"{prefixo}_{nome_tabela}" if prefixo else nome_tabela

            # 1. Exportação para PARQUET
            caminho_parquet = os.path.join(self.path_saida, f"{nome_final}.parquet")
            df.to_parquet(caminho_parquet, index=False, engine="pyarrow")
            log_gerados.append(f"PARQUET: {os.path.basename(caminho_parquet)}")

            # 2. Exportação para EXCEL (Tabelas selecionadas)
            termos_excel = [
                "BP",
                "DRE",
                "Balancete",
                "Plano_Contas",
                "Lancamentos_Contabeis",
                "Saldos_Mensais",
                "baseRFB",
            ]
            if any(term in nome_tabela for term in termos_excel):
                caminho_xlsx = os.path.join(self.path_saida, f"{nome_final}.xlsx")

                # Aplicar formatação regional para Excel
                df_xlsx = self.aplicar_formatacao_regional(df)
                df_xlsx.to_excel(caminho_xlsx, index=False, engine="openpyxl")
                log_gerados.append(f"EXCEL:   {os.path.basename(caminho_xlsx)}")

        self._atualizar_log_centralizado(log_gerados + itens_adicionais)
        logging.info(f"Exportação concluída: {self.id_folder}")

    def _atualizar_log_centralizado(self, lista_arquivos: list) -> None:
        """
        Salva o log na pasta 'log_arquivo' com o padrão Log_Arquivos_PERIODO.txt.
        """
        log_dir = os.path.join(self.output_base, "file_logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        nome_log = f"Log_Arquivos_{self.id_folder}.txt"
        caminho_log = os.path.join(log_dir, nome_log)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Modo 'w' para sobrescrever se o processo rodou do zero
        with open(caminho_log, "w", encoding="utf-8") as f:
            f.write(f"ID PROCESSAMENTO: {self.id_folder}\n")
            f.write(f"PASTA DE DESTINO: {os.path.abspath(self.path_saida)}\n")
            f.write(f"DATA/HORA:        {timestamp}\n")
            f.write("-" * 50 + "\n")
            for item in lista_arquivos:
                f.write(f"{item}\n")
