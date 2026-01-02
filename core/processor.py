import pandas as pd
import logging

from typing import Dict, List, Any, Optional
from decimal import Decimal

# Logger local para uso interno do módulo (não configura nível globalmente)
logger = logging.getLogger(__name__)


class ECDProcessor:
    """
    Motor de Processamento de Dados ECD (SPED-Contábil) com Auditoria Integrada.
    """

    def __init__(self, registros: List[Dict[str, Any]], cnpj: str = ""):
        self.df_bruto = pd.DataFrame(registros) if registros else pd.DataFrame()
        self.cnpj = cnpj
        self.blocos: Dict[str, pd.DataFrame] = {}

        if not self.df_bruto.empty:
            self._separar_blocos()

    def _separar_blocos(self) -> None:
        """Divide os registros por REG e limpa prefixos redundantes."""
        for reg in self.df_bruto["REG"].unique():
            df_reg = (
                self.df_bruto[self.df_bruto["REG"] == reg]
                .dropna(axis=1, how="all")
                .copy()
            )
            if "REG" in df_reg.columns:
                df_reg = df_reg.drop(columns=["REG"])

            prefixo = f"{reg}_"
            df_reg.columns = [
                str(c).replace(prefixo, "") if str(c).startswith(prefixo) else c
                for c in df_reg.columns
            ]

            # Remove duplicatas de colunas que possam surgir na renomeação
            self.blocos[f"dfECD_{reg}"] = df_reg.loc[
                :, ~pd.Index(df_reg.columns).duplicated()
            ].copy()

    def _converter_decimal(self, valor) -> Decimal:
        """Garante precisão absoluta para cálculos financeiros."""
        if pd.isna(valor) or valor == "":
            return Decimal("0.00")
        try:
            return Decimal(str(valor))
        except:
            return Decimal("0.00")

    def processar_plano_contas(self) -> pd.DataFrame:
        """Processa o Plano de Contas da Empresa (I050)."""
        df = self.blocos.get("dfECD_I050")
        if df is None:
            return pd.DataFrame()

        colunas = ["COD_NAT", "IND_CTA", "NIVEL", "COD_CTA", "COD_CTA_SUP", "CTA"]
        df_res = df[[c for c in colunas if c in df.columns]].copy()
        df_res["CNPJ"] = self.cnpj

        if "CTA" in df_res.columns:
            df_res["CONTA"] = (
                df_res["COD_CTA"].astype(str)
                + " - "
                + df_res["CTA"].str.strip().str.upper()
            )
        return df_res

    def processar_lancamentos(self, df_plano: pd.DataFrame) -> pd.DataFrame:
        """Processa Lançamentos Contábeis (I200/I250)."""
        df_i200 = self.blocos.get("dfECD_I200")
        df_i250 = self.blocos.get("dfECD_I250")
        if df_i200 is None or df_i250 is None:
            return pd.DataFrame()

        df_lctos = pd.merge(
            df_i200[["PK", "NUM_LCTO", "DT_LCTO", "IND_LCTO"]],
            df_i250,
            left_on="PK",
            right_on="FK_PAI",
        )

        df_lctos["CNPJ"] = self.cnpj
        df_lctos["VL_D"] = df_lctos.apply(
            lambda r: self._converter_decimal(r["VL_DC"])
            if r["IND_DC"] == "D"
            else Decimal("0.00"),
            axis=1,
        )
        df_lctos["VL_C"] = df_lctos.apply(
            lambda r: self._converter_decimal(r["VL_DC"])
            if r["IND_DC"] == "C"
            else Decimal("0.00"),
            axis=1,
        )
        df_lctos["VL_SINAL"] = df_lctos.apply(lambda r: r["VL_D"] - r["VL_C"], axis=1)

        if not df_plano.empty:
            df_lctos = pd.merge(
                df_lctos, df_plano[["COD_CTA", "CONTA"]], on="COD_CTA", how="left"
            )

        return df_lctos

    def gerar_balancetes(self) -> Dict[str, pd.DataFrame]:
        """
        Gera balancetes com Forward Roll, Reversão de Encerramento.
        """
        df_plano = self.processar_plano_contas()
        df_i150 = self.blocos.get("dfECD_I150")
        df_i155 = self.blocos.get("dfECD_I155")
        df_i157 = self.blocos.get("dfECD_I157")  # Transferência de Plano de Contas

        if df_plano.empty or df_i150 is None or df_i155 is None:
            return {}

        # 1. Base Unificada de Saldos
        df_base = pd.merge(
            df_i150[["PK", "DT_FIN"]], df_i155, left_on="PK", right_on="FK_PAI"
        )
        df_base["CNPJ"] = self.cnpj

        # 2. Sinais e Tipagem
        df_base["VL_SLD_INI_SIG"] = df_base.apply(
            lambda r: self._converter_decimal(r["VL_SLD_INI"])
            if r["IND_DC_INI"] == "D"
            else -self._converter_decimal(r["VL_SLD_INI"]),
            axis=1,
        )
        df_base["VL_SLD_FIN_SIG"] = df_base.apply(
            lambda r: self._converter_decimal(r["VL_SLD_FIN"])
            if r["IND_DC_FIN"] == "D"
            else -self._converter_decimal(r["VL_SLD_FIN"]),
            axis=1,
        )
        df_base["VL_DEB"] = df_base["VL_DEB"].apply(self._converter_decimal)
        df_base["VL_CRED"] = df_base["VL_CRED"].apply(self._converter_decimal)

        # 3. Reversão de Encerramento (Indicator 'E')
        df_lctos = self.processar_lancamentos(df_plano)
        if not df_lctos.empty and "IND_LCTO" in df_lctos.columns:
            df_e = df_lctos[df_lctos["IND_LCTO"] == "E"].copy()
            if not df_e.empty:
                ajustes = (
                    df_e.groupby(["COD_CTA", "DT_LCTO"])
                    .agg({"VL_SINAL": "sum", "VL_D": "sum", "VL_C": "sum"})
                    .reset_index()
                )
                ajustes.rename(
                    columns={
                        "VL_SINAL": "VL_AJ_SINAL",
                        "VL_D": "VL_AJ_D",
                        "VL_C": "VL_AJ_C",
                        "DT_LCTO": "DT_FIN",
                    },
                    inplace=True,
                )

                df_base = pd.merge(
                    df_base, ajustes, on=["COD_CTA", "DT_FIN"], how="left"
                ).fillna(Decimal("0.00"))
                df_base["VL_SLD_FIN_SIG"] = (
                    df_base["VL_SLD_FIN_SIG"] - df_base["VL_AJ_SINAL"]
                )
                df_base["VL_DEB"] = df_base["VL_DEB"] - df_base["VL_AJ_D"]
                df_base["VL_CRED"] = df_base["VL_CRED"] - df_base["VL_AJ_C"]

        # 4. Forward Roll (Continuidade Histórica) & I157
        df_base = df_base.sort_values(["COD_CTA", "DT_FIN"])
        df_base["VL_SLD_FIN_ANT"] = df_base.groupby("COD_CTA")["VL_SLD_FIN_SIG"].shift(
            1
        )

        # Se houver I157, aplica o mapeamento de saldos iniciais transferidos
        if df_i157 is not None:
            df_base = pd.merge(
                df_base,
                df_i157[["COD_CTA", "VL_SLD_INI", "IND_DC_INI"]],
                on="COD_CTA",
                how="left",
                suffixes=("", "_I157"),
            )
            df_base["VL_I157_SIG"] = df_base.apply(
                lambda r: self._converter_decimal(r["VL_SLD_INI_I157"])
                if r["IND_DC_INI_I157"] == "D"
                else -self._converter_decimal(r["VL_SLD_INI_I157"]),
                axis=1,
            )
            # Aplica o saldo do I157 apenas se não houver saldo anterior detectado (início da conta no novo plano)
            mask_primeiro_mes = df_base["VL_SLD_FIN_ANT"].isna()
            df_base.loc[
                mask_primeiro_mes & df_base["VL_I157_SIG"].notna(), "VL_SLD_INI_SIG"
            ] = df_base["VL_I157_SIG"]

        df_base["VL_SLD_INI_SIG"] = df_base.apply(
            lambda r: r["VL_SLD_FIN_ANT"]
            if pd.notna(r["VL_SLD_FIN_ANT"])
            else r["VL_SLD_INI_SIG"],
            axis=1,
        )

        # 5. Propagação Hierárquica (Plano da Empresa)
        balancete_empresa = self._propagar_hierarquia(df_base, df_plano)

        return {
            "04_Balancetes_Mensais": balancete_empresa,
        }

    def _propagar_hierarquia(self, df_saldos, df_plano) -> pd.DataFrame:
        """Algoritmo Bottom-Up para consolidação de níveis sintéticos."""
        balancetes = []
        cols_valores = ["VL_SLD_INI_SIG", "VL_DEB", "VL_CRED", "VL_SLD_FIN_SIG"]

        for data in df_saldos["DT_FIN"].unique():
            df_mes = df_saldos[df_saldos["DT_FIN"] == data].copy()
            tab = pd.merge(
                df_plano, df_mes[cols_valores + ["COD_CTA"]], on="COD_CTA", how="left"
            )
            for col in cols_valores:
                tab[col] = tab[col].apply(self._converter_decimal)

            niveis = sorted(tab["NIVEL"].unique(), reverse=True)
            for nivel in niveis:
                if nivel == 1:
                    continue
                agregados = (
                    tab[tab["NIVEL"] == nivel]
                    .groupby("COD_CTA_SUP")[cols_valores]
                    .sum()
                    .reset_index()
                )
                for _, row in agregados.iterrows():
                    idx_pai = tab.index[tab["COD_CTA"] == row["COD_CTA_SUP"]]
                    if not idx_pai.empty:
                        tab.loc[idx_pai, cols_valores] += row[cols_valores]

            tab["DT_FIN"] = data
            balancetes.append(tab)

        return (
            pd.concat(balancetes, ignore_index=True) if balancetes else pd.DataFrame()
        )

    def processar_demonstracoes(self) -> Dict[str, pd.DataFrame]:
        """Processa Balanço (J100) e DRE (J150)."""
        df_j100 = self.blocos.get("dfECD_J100")
        df_j150 = self.blocos.get("dfECD_J150")
        df_j005 = self.blocos.get("dfECD_J005")

        res = {"BP": pd.DataFrame(), "DRE": pd.DataFrame()}
        if df_j005 is not None:
            # Garante que temos a data final para o join
            base = (
                df_j005[["PK", "DT_FIN", "CNPJ"]]
                if "CNPJ" in df_j005.columns
                else df_j005[["PK", "DT_FIN"]]
            )
            if df_j100 is not None:
                res["BP"] = pd.merge(base, df_j100, left_on="PK", right_on="FK_PAI")
            if df_j150 is not None:
                res["DRE"] = pd.merge(base, df_j150, left_on="PK", right_on="FK_PAI")
        return res
