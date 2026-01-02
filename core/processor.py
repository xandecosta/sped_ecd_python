import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from decimal import Decimal

# Configuração de logs para exibição de status do processamento
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class ECDProcessor:
    """
    Motor de Processamento de Dados ECD (SPED-Contábil).
    Transforma registros brutos em DataFrames Pandas estruturados, realizando
    limpeza, enriquecimento e cálculos hierárquicos.
    """

    def __init__(self, registros: List[Dict[str, Any]]):
        """
        Inicializa o processador.
        Args:
            registros: Lista de dicionários (saída do ECDReader.processar_arquivo).
        """
        if not registros:
            logging.warning("Nenhum registro fornecido ao ECDProcessor.")
            self.df_bruto = pd.DataFrame()
        else:
            self.df_bruto = pd.DataFrame(registros)

        self.blocos: Dict[str, pd.DataFrame] = {}

        if not self.df_bruto.empty:
            self._separar_blocos()

    def _separar_blocos(self) -> None:
        """
        Divide o DataFrame bruto em blocos específicos por registro (REG).
        Limpa os prefixos dos nomes das colunas para facilitar a manipulação.
        """
        for reg in self.df_bruto["REG"].unique():
            # Filtra o registro e remove colunas vazias
            df_reg = (
                self.df_bruto[self.df_bruto["REG"] == reg]
                .dropna(axis=1, how="all")
                .copy()
            )

            # 1. Remove a coluna 'REG' global redundante para evitar colisão no rename
            if "REG" in df_reg.columns:
                df_reg = df_reg.drop(columns=["REG"])

            # 2. Normalização: Remove o prefixo do registro (ex: 'I150_DT_INI' -> 'DT_INI')
            prefixo = f"{reg}_"
            df_reg.columns = [
                str(c).replace(prefixo, "") if str(c).startswith(prefixo) else c
                for c in df_reg.columns
            ]

            # 3. Fallback de segurança: Garante que não existem colunas duplicadas
            # (Útil se houver campos no schema com nomes idênticos após remoção de prefixo)
            # Usamos pd.Series para evitar alertas de tipagem do linter no Index
            df_cols = pd.Series(df_reg.columns)
            df_reg = df_reg.loc[:, ~df_cols.duplicated().values].copy()

            self.blocos[f"dfECD_{reg}"] = df_reg

        logging.info(f"Blocos segregados com sucesso: {list(self.blocos.keys())}")

    def processar_plano_contas(self) -> pd.DataFrame:
        """
        Processa o Registro I050 (Plano de Contas).
        Retorna: DataFrame com contas analíticas e sintéticas formatadas.
        """
        df = self.blocos.get("dfECD_I050")
        if df is None:
            return pd.DataFrame()

        # Seleciona colunas essenciais para auditoria
        colunas_alvo = [
            "PK",
            "DT_ALT",
            "COD_NAT",
            "IND_CTA",
            "NIVEL",
            "COD_CTA",
            "COD_CTA_SUP",
            "CTA",
        ]
        df_res = df[[c for c in colunas_alvo if c in df.columns]].copy()

        # Higienização de strings e criação da coluna 'CONTA' (Código + Descrição)
        if "CTA" in df_res.columns:
            df_res["CTA"] = df_res["CTA"].str.strip().str.upper()
            if "COD_CTA" in df_res.columns:
                df_res["CONTA"] = df_res["COD_CTA"].astype(str) + " - " + df_res["CTA"]

        return df_res

    def processar_saldos_mensais(self) -> pd.DataFrame:
        """
        Processa Registros I150 (Período) e I155 (Saldos Mensais).
        Une os detalhes de saldo ao seu respectivo período.
        """
        df_i150 = self.blocos.get("dfECD_I150")
        df_i155 = self.blocos.get("dfECD_I155")

        if df_i150 is None or df_i155 is None:
            return pd.DataFrame()

        # Merge entre período e saldos via PK -> FK_PAI
        df_saldos = pd.merge(
            df_i150[["PK", "DT_INI", "DT_FIN"]],
            df_i155,
            left_on="PK",
            right_on="FK_PAI",
            how="inner",
            suffixes=("_pai", ""),
        )
        return df_saldos

    def processar_lancamentos(self, df_plano: pd.DataFrame) -> pd.DataFrame:
        """
        Processa Registros I200 (Lançamentos) e I250 (Itens de Lançamento).
        Calcula sinais de Débito/Crédito e enriquece com o Plano de Contas.
        """
        df_i200 = self.blocos.get("dfECD_I200")
        df_i250 = self.blocos.get("dfECD_I250")

        if df_i200 is None or df_i250 is None:
            return pd.DataFrame()

        # Join Cabeçalho (I200) com Detalhes (I250)
        df_lctos = pd.merge(
            df_i200[["PK", "NUM_LCTO", "DT_LCTO", "VL_LCTO", "IND_LCTO"]],
            df_i250,
            left_on="PK",
            right_on="FK_PAI",
            how="inner",
            suffixes=("_cab", ""),
        )

        # Lógica de Sinais (VL_D para Débitos, VL_C para Créditos e VL_SINAL para saldo líquido)
        # Mantém a precisão usando Decimal
        df_lctos["VL_D"] = df_lctos.apply(
            lambda r: r["VL_DC"] if r["IND_DC"] == "D" else Decimal("0.00"), axis=1
        )
        df_lctos["VL_C"] = df_lctos.apply(
            lambda r: r["VL_DC"] if r["IND_DC"] == "C" else Decimal("0.00"), axis=1
        )
        df_lctos["VL_SINAL"] = df_lctos.apply(
            lambda r: r["VL_DC"] if r["IND_DC"] == "D" else -r["VL_DC"], axis=1
        )

        # Merge com Plano de Contas para identificação das contas
        if not df_plano.empty:
            df_lctos = pd.merge(
                df_lctos,
                df_plano[["COD_CTA", "CONTA", "NIVEL"]],
                on="COD_CTA",
                how="left",
                suffixes=("", "_plano"),
            )

        return df_lctos

    def gerar_balancetes(self) -> pd.DataFrame:
        """
        Gera Balancetes Mensais Dinâmicos com Propagação Hierárquica.
        Lógica Bottom-Up: Soma saldos de contas analíticas para as sintéticas.
        """
        df_plano = self.processar_plano_contas()
        df_i150 = self.blocos.get("dfECD_I150")
        df_i155 = self.blocos.get("dfECD_I155")

        if df_plano.empty or df_i150 is None or df_i155 is None:
            logging.warning("Dados incompletos para geração de balancetes.")
            return pd.DataFrame()

        # Unir cabeçalho de período com saldos mensais
        df_saldos_base = pd.merge(
            df_i150[["PK", "DT_FIN"]], df_i155, left_on="PK", right_on="FK_PAI"
        )

        # Função auxiliar para aplicar sinal devedor/credor com precisão Decimal
        def _aplicar_sinal(valor, indicador):
            if pd.isna(valor):
                return Decimal("0.00")
            val = Decimal(str(valor))
            return val if indicador == "D" else -val

        # Cálculo de saldos iniciais/finais com sinal algébrico
        df_saldos_base["VL_SLD_INI_SIG"] = df_saldos_base.apply(
            lambda r: _aplicar_sinal(r["VL_SLD_INI"], r["IND_DC_INI"]), axis=1
        )
        df_saldos_base["VL_SLD_FIN_SIG"] = df_saldos_base.apply(
            lambda r: _aplicar_sinal(r["VL_SLD_FIN"], r["IND_DC_FIN"]), axis=1
        )

        # ---------------------------------------------------------------------
        # INCLUSÃO: AJUSTE PRÉ-FECHAMENTO (REVERSÃO DE ENCERRAMENTO 'E') - CORRIGIDO
        # ---------------------------------------------------------------------
        df_lctos = self.processar_lancamentos(df_plano)
        if not df_lctos.empty and "IND_LCTO" in df_lctos.columns:
            df_e = df_lctos[df_lctos["IND_LCTO"] == "E"].copy()
            if not df_e.empty:
                # Agrupamos Débitos, Créditos e o Sinal de encerramento por conta e data
                # Precisamos de VL_D e VL_C para limpar as colunas de movimentação
                ajustes = (
                    df_e.groupby(["COD_CTA", "DT_LCTO"])
                    .agg({"VL_SINAL": "sum", "VL_D": "sum", "VL_C": "sum"})
                    .reset_index()
                )

                ajustes.rename(
                    columns={
                        "VL_SINAL": "VL_AJUSTE_E",
                        "VL_D": "VL_D_E",
                        "VL_C": "VL_C_E",
                        "DT_LCTO": "DT_FIN",
                    },
                    inplace=True,
                )

                # Merge com a base de saldos
                df_saldos_base = pd.merge(
                    df_saldos_base, ajustes, on=["COD_CTA", "DT_FIN"], how="left"
                )

                # Preenchimento de nulos para garantir que contas sem lançamentos 'E' não fiquem NaN
                cols_ajuste = ["VL_AJUSTE_E", "VL_D_E", "VL_C_E"]
                for col in cols_ajuste:
                    df_saldos_base[col] = df_saldos_base[col].apply(
                        lambda x: x if isinstance(x, Decimal) else Decimal("0.00")
                    )

                # 1. Ajuste do Saldo Final: Reverte o zeramento
                df_saldos_base["VL_SLD_FIN_SIG"] = (
                    df_saldos_base["VL_SLD_FIN_SIG"] - df_saldos_base["VL_AJUSTE_E"]
                )

                # 2. Ajuste de Movimentação: Remove os lançamentos 'E' das colunas de Débito e Crédito
                # Isso garante que a soma horizontal (Ini + Deb - Cred = Fin) continue válida
                df_saldos_base["VL_DEB"] = (
                    df_saldos_base["VL_DEB"] - df_saldos_base["VL_D_E"]
                )
                df_saldos_base["VL_CRED"] = (
                    df_saldos_base["VL_CRED"] - df_saldos_base["VL_C_E"]
                )

                logging.info(
                    "Lançamentos de encerramento 'E' removidos de VL_DEB/VL_CRED e revertidos em VL_SLD_FIN_SIG."
                )
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        # NOVA INCLUSÃO: GARANTIR CONTINUIDADE HISTÓRICA (FORWARD ROLL)
        # ---------------------------------------------------------------------
        # Ordenamos por conta e data para garantir a sequência correta
        df_saldos_base = df_saldos_base.sort_values(["COD_CTA", "DT_FIN"])

        # Criamos uma coluna com o saldo final do mês anterior para cada conta
        df_saldos_base["VL_SLD_FIN_ANT"] = df_saldos_base.groupby("COD_CTA")[
            "VL_SLD_FIN_SIG"
        ].shift(1)

        # Aplicamos a regra: Se houver saldo anterior (mesma conta, mês anterior),
        # o saldo inicial DEVE ser o final do mês passado.
        # Isso resolve o encerramento trimestral e mensal.
        df_saldos_base["VL_SLD_INI_SIG"] = df_saldos_base.apply(
            lambda r: r["VL_SLD_FIN_ANT"]
            if pd.notna(r["VL_SLD_FIN_ANT"])
            else r["VL_SLD_INI_SIG"],
            axis=1,
        )

        logging.info(
            "Continuidade histórica aplicada: Saldos iniciais sincronizados com finais ajustados."
        )
        # ---------------------------------------------------------------------

        balancetes_lista = []
        for mes in df_saldos_base["DT_FIN"].unique():
            # Filtro do mês e colunas de valor
            df_mes = df_saldos_base[df_saldos_base["DT_FIN"] == mes][
                ["COD_CTA", "VL_SLD_INI_SIG", "VL_DEB", "VL_CRED", "VL_SLD_FIN_SIG"]
            ].copy()

            # Une com plano de contas para garantir todas as linhas contábeis
            tabela_balancete = pd.merge(df_plano, df_mes, on="COD_CTA", how="left")

            # Preenchimento de nulos com Decimal(0)
            cols_fin = ["VL_SLD_INI_SIG", "VL_DEB", "VL_CRED", "VL_SLD_FIN_SIG"]
            for col in cols_fin:
                tabela_balancete[col] = tabela_balancete[col].apply(
                    lambda x: x if isinstance(x, Decimal) else Decimal("0.00")
                )

            # --- Propagação Hierárquica (Subindo os valores para os pais) ---
            niveis = sorted(tabela_balancete["NIVEL"].unique(), reverse=True)
            for nivel in niveis:
                if nivel == 1:
                    continue
                # Agrega os analíticos para o nível superior
                # Nota: Usamos lambda x: sum(x) para garantir compatibilidade com Decimal
                agregados = (
                    tabela_balancete[tabela_balancete["NIVEL"] == nivel]
                    .groupby("COD_CTA_SUP")
                    .agg(
                        {
                            "VL_SLD_INI_SIG": lambda x: sum(x),
                            "VL_DEB": lambda x: sum(x),
                            "VL_CRED": lambda x: sum(x),
                            "VL_SLD_FIN_SIG": lambda x: sum(x),
                        }
                    )
                    .reset_index()
                )

                for _, row in agregados.iterrows():
                    idx_pai = tabela_balancete.index[
                        tabela_balancete["COD_CTA"] == row["COD_CTA_SUP"]
                    ]
                    if not idx_pai.empty:
                        tabela_balancete.loc[idx_pai, cols_fin] += row[cols_fin]

            tabela_balancete["MES"] = mes
            balancetes_lista.append(tabela_balancete)

        if not balancetes_lista:
            return pd.DataFrame()

        return pd.concat(balancetes_lista, ignore_index=True)

    def processar_demonstracoes(self) -> Dict[str, pd.DataFrame]:
        """
        Processa Balanço Patrimonial (J100) e DRE (J150).
        Retorna: Dicionário com 'BP' e 'DRE' em DataFrames.
        """
        df_j005 = self.blocos.get("dfECD_J005")
        df_j100 = self.blocos.get("dfECD_J100")
        df_j150 = self.blocos.get("dfECD_J150")

        resultados = {"BP": pd.DataFrame(), "DRE": pd.DataFrame()}

        if df_j005 is not None:
            # Demonstração do Balanço (J100)
            if df_j100 is not None:
                resultados["BP"] = pd.merge(
                    df_j005[["PK", "DT_INI", "DT_FIN"]],
                    df_j100,
                    left_on="PK",
                    right_on="FK_PAI",
                )
            # Demonstração de Resultado (J150)
            if df_j150 is not None:
                resultados["DRE"] = pd.merge(
                    df_j005[["PK", "DT_INI", "DT_FIN"]],
                    df_j150,
                    left_on="PK",
                    right_on="FK_PAI",
                )

        return resultados
