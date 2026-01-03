import pandas as pd
import json
import os
import io


def parse_ano_range(ano_str):
    """Converte strings de ano em faixas numericas."""
    if ano_str == "<2014":
        return 0, 2013
    if ano_str == ">=2021":
        return 2021, 9999
    try:
        ano = int(ano_str)
        return ano, ano
    except Exception:
        return 0, 9999


def standardize_ref_plans():
    base_dir = r"g:\Drives compartilhados\10_Arquivo\002_Programacao_Desenvolvimento\python_ecd"
    csv_path = os.path.join(
        base_dir, "data", "reference", "plano_contas_referencial.csv"
    )
    raw_data_dir = os.path.join(base_dir, "data", "plano_contas_referencial")
    output_data_dir = os.path.join(base_dir, "schemas", "ref_plans", "data")
    catalog_path = os.path.join(base_dir, "schemas", "ref_plans", "ref_catalog.json")

    # Garante diretorio de saida
    os.makedirs(output_data_dir, exist_ok=True)

    if not os.path.exists(csv_path):
        print("Erro: CSV de referencia (meta) nao encontrado.")
        return

    df_meta = pd.read_csv(csv_path, sep=";", encoding="utf-8")
    catalog = {}

    for _, row in df_meta.iterrows():
        file_name = row["TabelaDinamica"]
        alias = row["CodigoTabDinamica"]
        versao = str(row["VersaoTabDinamica"])
        ano_str = str(row["Ano"])
        cod_plan_ref = str(row["COD_PLAN_REF"])
        tipo_demo = row["TipoDemonstracao"]
        estrutura = str(row["ESTRUTURA_COLUNAS"])

        # Define colunas baseado na estrutura
        has_ordem = "ORDEM" in estrutura

        if has_ordem:
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

        file_path = os.path.join(raw_data_dir, file_name)

        if not os.path.exists(file_path):
            file_path_txt = file_path + ".txt"
            if os.path.exists(file_path_txt):
                file_path = file_path_txt
            else:
                print(f"Aviso: Arquivo {file_name} nao encontrado.")
                continue

        try:
            # Lendo o TXT bruto (ANSI/Latin1) pulando a 1a linha
            with open(file_path, "r", encoding="latin1") as f:
                lines = f.readlines()
                if not lines:
                    continue
                content = "".join(lines[1:])

            # Parse CSV do conteudo bruto
            df_plan = pd.read_csv(
                io.StringIO(content),
                sep="|",
                names=cols,
                header=None,
                dtype=str,
                engine="python",
                quoting=3,
                index_col=False,
            ).fillna("")

            # Salva Plano em CSV PADRONIZADO (UTF-8, com Cabecalho, Pipe)
            csv_output_name = f"{file_name}.csv"
            csv_output_path = os.path.join(output_data_dir, csv_output_name)

            df_plan.to_csv(csv_output_path, sep="|", index=False, encoding="utf-8")

            # Build Catalog Hierarquico
            ano_min, ano_max = parse_ano_range(ano_str)

            if cod_plan_ref not in catalog:
                catalog[cod_plan_ref] = {}
            if ano_str not in catalog[cod_plan_ref]:
                catalog[cod_plan_ref][ano_str] = {
                    "range": [ano_min, ano_max],
                    "plans": {},
                }
            if alias not in catalog[cod_plan_ref][ano_str]["plans"]:
                catalog[cod_plan_ref][ano_str]["plans"][alias] = {}

            catalog[cod_plan_ref][ano_str]["plans"][alias][versao] = {
                "file": csv_output_name,
                "tipo_demo": tipo_demo,
                "layout": "ref_dynamic" if has_ordem else "ref_standard",
            }

        except Exception as e:
            print(f"Erro ao processar {file_name}: {e}")

    # Salva Catalogo em JSON
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"Padronizacao concluida. {len(df_meta)} registros processados.")
    print(f"Catalog atualizado e arquivos CSV salvos em: {output_data_dir}")


if __name__ == "__main__":
    standardize_ref_plans()
