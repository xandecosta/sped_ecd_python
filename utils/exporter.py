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
            path_saida: Caminho base onde os arquivos serão salvos.
        """
        self.path_saida = path_saida
        self._preparar_pastas()

    def _preparar_pastas(self) -> None:
        """Cria a estrutura de pastas necessária."""
        if not os.path.exists(self.path_saida):
            os.makedirs(self.path_saida)
            logging.info(f"Pasta criada: {self.path_saida}")

    def exportar_lote(
        self,
        dicionario_dfs: Dict[str, pd.DataFrame],
        nome_base: str,
        prefixo: str = "",  # <--- ALTERAÇÃO: Adicionado prefixo opcional
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

            # -----------------------------------------------------------------
            # NOVO: Lógica de Nome de Arquivo com Prefixo (Data)
            # Isso permite abrir múltiplos arquivos no Excel simultaneamente
            # -----------------------------------------------------------------
            nome_final = f"{prefixo}_{nome_tabela}" if prefixo else nome_tabela
            # -----------------------------------------------------------------

            # 1. Exportação para PARQUET (Substituto do .rds)
            # Ideal para bases pesadas como Lançamentos e Saldos
            caminho_parquet = os.path.join(
                self.path_saida, f"{nome_final}.parquet"
            )  # <--- ALTERAÇÃO: Usando nome_final
            df.to_parquet(caminho_parquet, index=False, engine="pyarrow")
            log_gerados.append(f"PARQUET: {os.path.basename(caminho_parquet)}")

            # 2. Exportação para EXCEL (Para conferência humana)
            # Sugestão: exportar para Excel apenas tabelas de resumo ou se solicitado
            # Defina quais desses nomes devem gerar um arquivo Excel
            termos_excel = [
                "BP",
                "DRE",
                "Balancetes_Mensais",
                "Plano_Contas",
                "Lancamentos_Contabeis",
                "Saldos_Mensais",
                "baseRFB",
            ]
            if any(term in nome_tabela for term in termos_excel):
                caminho_xlsx = os.path.join(
                    self.path_saida, f"{nome_final}.xlsx"
                )  # <--- ALTERAÇÃO: Usando nome_final
                df.to_excel(caminho_xlsx, index=False, engine="openpyxl")
                log_gerados.append(f"EXCEL:   {os.path.basename(caminho_xlsx)}")

        self._atualizar_log(log_gerados)
        logging.info(f"Exportação do lote '{nome_base}' concluída com sucesso.")

    def _atualizar_log(self, lista_arquivos: list) -> None:
        """Atualiza o arquivo de log de exportação, similar ao seu RDS_Gerados.txt."""
        caminho_log = os.path.join(self.path_saida, "Arquivos_Gerados.txt")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with open(caminho_log, "a", encoding="utf-8") as f:
            f.write(f"\n--- Exportação em {timestamp} ---\n")
            for item in lista_arquivos:
                f.write(f"{item}\n")
