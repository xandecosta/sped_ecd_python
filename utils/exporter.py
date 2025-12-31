import pandas as pd
import os
import logging
from datetime import datetime
from typing import Dict

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class ECDExporter:
    def __init__(self, path_saida: str):
        """
        Inicializa o exportador.
        Args:
            path_saida: Caminho base onde os ficheiros serão salvos.
        """
        self.path_saida = path_saida
        self.pasta_parquet = os.path.join(path_saida, "arquivos_PARQUET")
        self._preparar_pastas()

    def _preparar_pastas(self) -> None:
        """Cria a estrutura de pastas necessária."""
        for pasta in [self.path_saida, self.pasta_parquet]:
            if not os.path.exists(pasta):
                os.makedirs(pasta)
                logging.info(f"Pasta criada: {pasta}")

    def exportar_lote(
        self, dicionario_dfs: Dict[str, pd.DataFrame], nome_base: str
    ) -> None:
        """
        REPLICA O FLUXO R: Exporta múltiplos DataFrames para Parquet e Excel.

        Args:
            dicionario_dfs: Dicionário onde a chave é o nome da tabela e o valor é o DataFrame.
            nome_base: Nome do arquivo (ex: 'Dados_ECD_2023')
        """
        log_gerados = []

        for nome_tabela, df in dicionario_dfs.items():
            if df.empty:
                logging.warning(
                    f"Tabela {nome_tabela} está vazia. Ignorando exportação."
                )
                continue

            # 1. Exportação para PARQUET (Substituto do .rds)
            # Ideal para bases pesadas como Lançamentos e Saldos
            caminho_parquet = os.path.join(self.pasta_parquet, f"{nome_tabela}.parquet")
            df.to_parquet(caminho_parquet, index=False, engine="pyarrow")
            log_gerados.append(f"PARQUET: {os.path.basename(caminho_parquet)}")

            # 2. Exportação para EXCEL (Para conferência humana)
            # Sugestão: exportar para Excel apenas tabelas de resumo ou se solicitado
            if any(
                term in nome_tabela
                for term in ["Balancete", "PlanoContas", "BP", "DRE"]
            ):
                caminho_xlsx = os.path.join(self.path_saida, f"{nome_tabela}.xlsx")
                # Usamos o motor 'openpyxl' para suportar formatação
                df.to_excel(caminho_xlsx, index=False, engine="openpyxl")
                log_gerados.append(f"EXCEL:   {os.path.basename(caminho_xlsx)}")

        self._atualizar_log(log_gerados)
        logging.info(f"Exportação do lote '{nome_base}' concluída com sucesso.")

    def _atualizar_log(self, lista_ficheiros: list) -> None:
        """Atualiza o ficheiro de log de exportação, similar ao seu RDS_Gerados.txt."""
        caminho_log = os.path.join(self.path_saida, "Ficheiros_Gerados.txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(caminho_log, "a", encoding="utf-8") as f:
            f.write(f"\n--- Exportação em {timestamp} ---\n")
            for item in lista_ficheiros:
                f.write(f"{item}\n")
