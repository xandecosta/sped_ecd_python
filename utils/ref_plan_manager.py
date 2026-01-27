import pandas as pd
import os
import shutil
import io
import json
from typing import cast, Dict, List, Any


class RefPlanManager:
    def __init__(self):
        # Determine paths dynamically
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(self.current_dir)

        # Define key directories/files
        self.reference_dir = os.path.join(self.base_dir, "data", "reference")
        self.raw_data_dir = os.path.join(self.base_dir, "data", "raw_ref_plans")
        self.schemas_dir = os.path.join(self.base_dir, "schemas", "ref_plans", "data")
        self.analysis_dir = os.path.join(self.base_dir, "data", "analysis")
        self.catalog_path = os.path.join(
            self.base_dir, "schemas", "ref_plans", "ref_catalog.json"
        )

        # Files
        self.full_meta_path = os.path.join(self.reference_dir, "ref_plan_full.csv")
        self.filtered_meta_path = os.path.join(
            self.reference_dir, "ref_plan_filtered.csv"
        )
        self.discovery_report_path = os.path.join(
            self.reference_dir, "ref_plan_layout.xlsx"
        )
        self.conflicts_report_path = os.path.join(
            self.analysis_dir, "structural_conflicts_report.csv"
        )

        # State for auditing
        self.conflicts: List[Dict[str, Any]] = []

    def filter_metadata(self) -> pd.DataFrame:
        """
        Reads the full metadata CSV, filters for the latest version of each plan/year,
        saves the result to disk, and returns the DataFrame.
        """
        print(f"Reading metadata from: {self.full_meta_path}")

        if not os.path.exists(self.full_meta_path):
            raise FileNotFoundError(f"Source file not found: {self.full_meta_path}")

        df = cast(
            pd.DataFrame,
            pd.read_csv(self.full_meta_path, sep=";", encoding="utf-8-sig"),
        )

        required_cols = ["CodigoTabDinamica", "Ano", "VersaoTabDinamica"]
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing columns in metadata. Expected {required_cols}")

        print(f"Original row count: {len(df)}")

        # Sort: Ascending keys, Descending Version
        df_sorted = df.sort_values(
            by=["CodigoTabDinamica", "Ano", "VersaoTabDinamica"],
            ascending=[True, True, False],
        )

        # Keep only the first (highest version) for each group
        df_filtered = df_sorted.drop_duplicates(
            subset=["CodigoTabDinamica", "Ano"], keep="first"
        ).copy()

        df_filtered.sort_values(by=["CodigoTabDinamica", "Ano"], inplace=True)

        print(f"Filtered row count: {len(df_filtered)}")

        # Save filtered file
        os.makedirs(self.reference_dir, exist_ok=True)
        df_filtered.to_csv(
            self.filtered_meta_path, sep=";", index=False, encoding="utf-8-sig"
        )
        print(f"Saved filtered metadata: {self.filtered_meta_path}")

        return df_filtered

    def parse_ano_range(self, ano_str: str):
        """Converts year strings to numeric ranges."""
        ano_str = str(ano_str).strip()
        if ano_str == "<2014":
            return 0, 2013
        if ano_str == ">=2021":
            return 2021, 9999
        try:
            # Handle cases like ">=2014" or "<2020" if they appear elsewhere or generic cleaning
            if ano_str.startswith(">="):
                val = int(ano_str.replace(">=", ""))
                return val, 9999
            if ano_str.startswith("<"):
                val = int(ano_str.replace("<", ""))
                return 0, val - 1

            ano = int(ano_str)
            return ano, ano
        except Exception:
            return 0, 9999

    def parse_year_safe(self, year_val: Any) -> int:
        """Helper to safely extract integer year from metadata string."""
        try:
            year_str = str(year_val).strip()
            if year_str.startswith(">="):
                return int(year_str.replace(">=", ""))
            elif year_str.startswith("<"):
                return int(year_str.replace("<", ""))
            else:
                return int(year_str)
        except ValueError:
            return 0

    def standardize_plans(self):
        """
        Lê os metadados filtrados, agrupa por COD_PLAN_REF + Ano,
        concatena os arquivos TXT correspondentes (Balanço, DRE, etc)
        e gera um CSV unificado por Instituição/Ano.
        """
        # Ensure latest metadata is active
        df_meta = self.filter_metadata()

        print("\n>>> INICIANDO PADRONIZAÇÃO UNIFICADA...")

        # 1. Limpeza da pasta de schemas/data
        if os.path.exists(self.schemas_dir):
            print(f"Limpando pasta de schemas: {self.schemas_dir}")
            shutil.rmtree(self.schemas_dir)
        os.makedirs(self.schemas_dir, exist_ok=True)

        catalog: Dict[str, Any] = {}

        # Agrupamos por Instituição e Ano para criar arquivos únicos
        grouped = df_meta.groupby(["COD_PLAN_REF", "Ano"])

        for keys, group in grouped:
            cod_ref_raw, ano_str_raw = cast(tuple, keys)
            cod_ref = str(cod_ref_raw)
            ano_str = str(ano_str_raw)

            print(f"Unificando Planos: Instituição {cod_ref} | Ano {ano_str}")

            dfs_unificados = []
            info_versao = ""
            layout_type = "ref_standard"

            for _, row in group.iterrows():
                file_name = str(row["TabelaDinamica"])
                versao = str(row["VersaoTabDinamica"])
                estrutura = str(row["ESTRUTURA_COLUNAS"])

                # Snapshot da última versão/layout encontrada no grupo
                info_versao = versao
                if "ORDEM" in estrutura:
                    layout_type = "ref_dynamic"

                # Define colunas
                if "ORDEM" in estrutura:
                    cols = [
                        "CODIGO",
                        "DESCRICAO",
                        "DT_INI",
                        "DT_FIM",
                        "ORDEM",
                        "TIPO",
                        "COD_SUP",
                        "NIVEL",
                        "NATUREZA",
                    ]
                else:
                    cols = [
                        "CODIGO",
                        "DESCRICAO",
                        "DT_INI",
                        "DT_FIM",
                        "TIPO",
                        "COD_SUP",
                        "NIVEL",
                        "NATUREZA",
                        "UTILIZACAO",
                    ]

                file_path = os.path.join(self.raw_data_dir, file_name)
                if not os.path.exists(file_path) and os.path.exists(file_path + ".txt"):
                    file_path += ".txt"

                if not os.path.exists(file_path):
                    continue

                try:
                    with open(file_path, "r", encoding="latin1") as f:
                        lines = f.readlines()
                        if not lines:
                            continue
                        content = "".join(lines[1:])

                    df_part = pd.read_csv(
                        io.StringIO(content),
                        sep="|",
                        names=cols,
                        header=None,
                        dtype=str,
                        engine="python",
                        quoting=3,
                        index_col=False,
                    ).fillna("")

                    dfs_unificados.append(df_part)
                except Exception as e:
                    print(f"      Erro ao ler {file_name}: {e}")

            if dfs_unificados:
                df_final = pd.concat(dfs_unificados, ignore_index=True)
                # Remove duplicidade de códigos que possam existir entre planos
                df_final.drop_duplicates(subset=["CODIGO"], keep="first", inplace=True)

                # Limpeza Padrão
                if "NATUREZA" in df_final.columns:
                    df_final["NATUREZA"] = df_final["NATUREZA"].apply(
                        lambda x: str(x).zfill(2) if x and str(x).strip() else ""
                    )
                if "DESCRICAO" in df_final.columns:
                    df_final["DESCRICAO"] = df_final["DESCRICAO"].str.strip()

                # Nome unificado: REF_{Instituicao}_{Ano}.csv
                output_filename = f"REF_{cod_ref}_{ano_str}.csv".replace(
                    ">=", "GE"
                ).replace("<", "LT")
                output_path = os.path.join(self.schemas_dir, output_filename)

                df_final.to_csv(output_path, sep="|", index=False, encoding="utf-8")

                # Atualiza Catálogo
                ano_min, ano_max = self.parse_ano_range(ano_str)

                if cod_ref not in catalog:
                    catalog[cod_ref] = {}

                catalog[cod_ref][ano_str] = {
                    "range": [ano_min, ano_max],
                    "plans": {
                        "REF": {
                            info_versao: {
                                "file": output_filename,
                                "tipo_demo": "Unificado (Balanço + Resultado)",
                                "layout": layout_type,
                            }
                        }
                    },
                }

        # Save Catalog JSON
        with open(self.catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)

        print(f"\nStandardization complete. Catalog saved to {self.catalog_path}")

    def audit_plans(self):
        """
        Consolidated Audit:
        1. Generates Evolution Matrix (History of accounts across years).
        2. Checks Structural Integrity (Conflicts in Parent, Nature, Type).
        """
        print("\n--- Starting Consolidated Audit (Evolution + Integrity) ---")
        os.makedirs(self.analysis_dir, exist_ok=True)
        self.conflicts = []

        # Load Metadata directly (assuming it exists or standardized first)
        if not os.path.exists(self.filtered_meta_path):
            print("Filtered metadata not found. Running filter...")
            df_meta = self.filter_metadata()
        else:
            df_meta = cast(
                pd.DataFrame,
                pd.read_csv(
                    self.filtered_meta_path, sep=";", encoding="utf-8-sig", dtype=str
                ),
            )

        # Filter only for Plan 1 (Lucro Real) and 2 (Lucro Presumido)
        unique_refs = [
            r
            for r in cast(pd.Series, df_meta["COD_PLAN_REF"]).unique()
            if str(r).strip() in ["1", "2"]
        ]
        print(f"Processing restricted to COD_PLAN_REF types: {unique_refs}")

        for cod_ref in unique_refs:
            print(f"\nProcessing Plan: {cod_ref}")
            df_plan = df_meta[df_meta["COD_PLAN_REF"] == cod_ref].copy()

            # Prepare containers
            yearly_data: Dict[str, pd.DataFrame] = {}
            knowledge_base: Dict[str, Dict[str, Any]] = {}

            # Sort groups by year
            grouped = df_plan.groupby("Ano")
            group_keys = cast(Dict[Any, Any], grouped.groups).keys()
            years_list: List[tuple[int, Any]] = []
            for y_key in group_keys:
                years_list.append((self.parse_year_safe(y_key), y_key))

            years_list.sort(key=lambda x: x[0])

            for y_val, year_key in years_list:
                # Skip ancient history if desired, matching logic from previous scripts
                if y_val < 2014:
                    continue

                ano_str = str(year_key)
                # Reconstrói o nome do arquivo unificado conforme lógica do standardize_plans
                unified_filename = f"REF_{cod_ref}_{ano_str}.csv".replace(
                    ">=", "GE"
                ).replace("<", "LT")
                file_path = os.path.join(self.schemas_dir, unified_filename)

                if not os.path.exists(file_path):
                    continue

                print(f"  Lendo plano para auditoria: {unified_filename}")
                try:
                    # Read CSV - Use pipe separator as generated by standardize_plans
                    df_full_year = cast(
                        pd.DataFrame,
                        pd.read_csv(file_path, sep="|", dtype=str, encoding="utf-8"),
                    )

                    cols_to_keep = [
                        "CODIGO",
                        "DESCRICAO",
                        "NATUREZA",
                        "NIVEL",
                        "COD_SUP",
                        "TIPO",
                    ]
                    # Keep available columns
                    existing_cols = [
                        c for c in cols_to_keep if c in df_full_year.columns
                    ]
                    df_full_year = cast(pd.DataFrame, df_full_year[existing_cols])
                    df_full_year.drop_duplicates(subset=["CODIGO"], inplace=True)

                    # 1. Integrity Check (On-the-fly)
                    self._check_integrity_row(
                        cod_ref, year_key, df_full_year, knowledge_base
                    )

                    # 2. Store for Evolution Report
                    yearly_data[str(year_key)] = df_full_year.set_index("CODIGO")

                except Exception as e:
                    print(f"  Error reading {file_path}: {e}")

            # After processing all years for this Plan Ref, generate the Evolution Report
            self._generate_evolution_report(cod_ref, yearly_data)

        # After processing all Plans, save the global Conflict Report
        self._save_conflict_report()

    def _check_integrity_row(
        self,
        cod_ref: str,
        year: str,
        df: pd.DataFrame,
        knowledge_base: Dict[str, Dict[str, Any]],
    ):
        """Compares current year's accounts against the knowledge base."""
        for _, account in df.iterrows():
            code = str(account.get("CODIGO", ""))
            if not code:
                continue

            # Normalize fields
            cod_sup = (
                str(account.get("COD_SUP", ""))
                if pd.notna(cast(Any, account.get("COD_SUP")))
                else ""
            )
            natureza = (
                str(account.get("NATUREZA", ""))
                if pd.notna(cast(Any, account.get("NATUREZA")))
                else ""
            )
            tipo = (
                str(account.get("TIPO", ""))
                if pd.notna(cast(Any, account.get("TIPO")))
                else ""
            )

            if code in knowledge_base:
                prev = knowledge_base[code]

                # Check Parent
                if prev["COD_SUP"] != cod_sup:
                    self.conflicts.append(
                        {
                            "COD_PLAN_REF": cod_ref,
                            "CODIGO": code,
                            "TIPO_CONFLITO": "MUDANCA_PAI",
                            "VALOR_ANTIGO": prev["COD_SUP"],
                            "ANO_ANTIGO": prev["LAST_SEEN_YEAR"],
                            "VALOR_NOVO": cod_sup,
                            "ANO_NOVO": year,
                        }
                    )

                # Check Nature
                if prev["NATUREZA"] != natureza:
                    self.conflicts.append(
                        {
                            "COD_PLAN_REF": cod_ref,
                            "CODIGO": code,
                            "TIPO_CONFLITO": "MUDANCA_NATUREZA",
                            "VALOR_ANTIGO": prev["NATUREZA"],
                            "ANO_ANTIGO": prev["LAST_SEEN_YEAR"],
                            "VALOR_NOVO": natureza,
                            "ANO_NOVO": year,
                        }
                    )

                # Check Type
                if prev["TIPO"] != tipo:
                    self.conflicts.append(
                        {
                            "COD_PLAN_REF": cod_ref,
                            "CODIGO": code,
                            "TIPO_CONFLITO": "MUDANCA_TIPO",
                            "VALOR_ANTIGO": prev["TIPO"],
                            "ANO_ANTIGO": prev["LAST_SEEN_YEAR"],
                            "VALOR_NOVO": tipo,
                            "ANO_NOVO": year,
                        }
                    )

                # Update KB
                knowledge_base[code]["COD_SUP"] = cod_sup
                knowledge_base[code]["NATUREZA"] = natureza
                knowledge_base[code]["TIPO"] = tipo
                knowledge_base[code]["LAST_SEEN_YEAR"] = year
            else:
                # New Entry
                knowledge_base[code] = {
                    "COD_SUP": cod_sup,
                    "NATUREZA": natureza,
                    "TIPO": tipo,
                    "FIRST_SEEN_YEAR": year,
                    "LAST_SEEN_YEAR": year,
                }

    def _generate_evolution_report(
        self, cod_ref: str, yearly_data: Dict[str, pd.DataFrame]
    ):
        """Generates the wide-format CSV matrix for account evolution."""
        all_codes = set()
        for year in yearly_data:
            all_codes.update(cast(pd.Series, yearly_data[year].index).tolist())

        if not all_codes:
            print("  No data found for evolution report.")
            return

        print(f"  Generating evolution report for {len(all_codes)} accounts...")

        comparison_rows: List[Dict[str, Any]] = []

        # Sort years numerically for columns
        years_sorted = sorted(yearly_data.keys(), key=self.parse_year_safe)

        for code in sorted(list(all_codes)):
            row: Dict[str, Any] = {"CODIGO": code}
            canonical_info: Dict[str, Any] = {}

            # Find most recent info (traverse backwards)
            for year in reversed(years_sorted):
                if code in yearly_data[year].index:
                    data = cast(pd.Series, yearly_data[year].loc[code])
                    canonical_info = {
                        "DESCRICAO": data.get("DESCRICAO", ""),
                        "NIVEL": data.get("NIVEL", ""),
                        "NATUREZA": data.get("NATUREZA", ""),
                        "TIPO": data.get("TIPO", ""),
                        "COD_SUP": data.get("COD_SUP", ""),
                    }
                    break
            row.update(canonical_info)

            # Fill year columns
            for year in years_sorted:
                if code in yearly_data[year].index:
                    desc = cast(pd.Series, yearly_data[year].loc[code]).get(
                        "DESCRICAO", "SIM"
                    )
                    row[f"ANO_{year}"] = desc
                else:
                    row[f"ANO_{year}"] = None

            comparison_rows.append(row)

        df_comparison = cast(pd.DataFrame, pd.DataFrame(comparison_rows))

        # Enforce Column Order requested by User
        base_cols = [
            "CODIGO",
            "DESCRICAO",
            "TIPO",
            "COD_SUP",
            "NIVEL",
            "NATUREZA",
        ]
        year_cols = [f"ANO_{y}" for y in years_sorted]
        final_cols = base_cols + year_cols

        # Select only existing columns to be safe
        existing_cols = [c for c in final_cols if c in df_comparison.columns]
        df_comparison = df_comparison[existing_cols]

        safe_cod = str(cod_ref).strip()
        output_path = os.path.join(
            self.analysis_dir, f"ref_plan_evolution_{safe_cod}.csv"
        )

        # Using pipe separator as requested
        df_comparison.to_csv(output_path, sep="|", index=False, encoding="utf-8-sig")
        print(f"  Evolution Report saved: {output_path}")

    def _save_conflict_report(self):
        """Saves the cumulative conflict list to CSV."""
        if not self.conflicts:
            print("\nSUCCESS: No structural conflicts found!")
        else:
            print(f"\nWARNING: Found {len(self.conflicts)} structural conflicts.")
            df_conflicts = pd.DataFrame(self.conflicts)
            # Using pipe separator for consistency
            df_conflicts.to_csv(
                self.conflicts_report_path, sep="|", index=False, encoding="utf-8-sig"
            )
            print(f"Conflict report saved to: {self.conflicts_report_path}")

    def discover_layouts(self):
        """
        Scans the raw data directory and creates an Excel report of the file headers.
        Useful for debugging layout changes.
        """
        print(f"Scanning raw files in {self.raw_data_dir}...")

        if not os.path.exists(self.raw_data_dir):
            print(f"Error: Directory {self.raw_data_dir} not found.")
            return

        arquivos = [f for f in os.listdir(self.raw_data_dir) if f.endswith(".txt")]
        dados = []

        for nome_arq in arquivos:
            caminho = os.path.join(self.raw_data_dir, nome_arq)
            try:
                with open(caminho, "r", encoding="latin1") as f:
                    primeira_linha = f.readline().strip()
                    dados.append({"Arquivo": nome_arq, "Cabecalho": primeira_linha})
            except Exception as e:
                dados.append({"Arquivo": nome_arq, "Cabecalho": f"ERRO: {e}"})

        df = cast(pd.DataFrame, pd.DataFrame(dados))
        os.makedirs(os.path.dirname(self.discovery_report_path), exist_ok=True)
        df.to_excel(self.discovery_report_path, index=False, engine="openpyxl")
        print(f"Discovery report generated: {self.discovery_report_path}")


if __name__ == "__main__":
    manager = RefPlanManager()

    # 1. Standardize (Generate CSVs)
    manager.standardize_plans()

    # 2. Audit (Evolution + Integrity)
    manager.audit_plans()
