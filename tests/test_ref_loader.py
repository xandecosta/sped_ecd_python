import json
import os
import pandas as pd


def utility_load_plan(cod_plan_ref, ano, tipo_demo="Balanço Patrimonial"):
    # Caminhos relativos a partir da raiz do projeto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index_path = os.path.join(base_dir, "schemas", "ref_plans", "ref_index.json")
    schemas_dir = os.path.join(base_dir, "schemas", "ref_plans")
    data_dir = os.path.join(base_dir, "data", "plano_contas_referencial")

    if not os.path.exists(index_path):
        print(f"Index não encontrado: {index_path}")
        return

    with open(index_path, "r", encoding="utf-8") as f:
        index = json.load(f)

    # Busca no index
    match = None
    for entry in index:
        if (
            entry["cod_plan_ref"] == str(cod_plan_ref)
            and entry["ano_min"] <= ano <= entry["ano_max"]
            and entry["tipo_demo"] == tipo_demo
        ):
            match = entry
            break

    if not match:
        print(
            f"Nenhum plano encontrado para COD={cod_plan_ref}, Ano={ano}, Tipo={tipo_demo}"
        )
        return

    print(f"Plano localizado: {match['arquivo']}")

    # Carrega o layout
    layout_path = os.path.join(schemas_dir, f"{match['layout']}.json")
    with open(layout_path, "r", encoding="utf-8") as f:
        layout = json.load(f)

    # Tenta carregar o arquivo real
    file_path = os.path.join(data_dir, f"{match['arquivo']}.txt")
    if not os.path.exists(file_path):
        print(f"Arquivo fisico nao encontrado: {file_path}")
        return

    try:
        df = pd.read_csv(
            file_path,
            sep=layout["separador"],
            encoding=layout["encoding"],
            names=layout["colunas"],
            header=0,
            dtype=str,
        )
        print(f"Sucesso! {len(df)} registros carregados.")
        print("Primeiras 3 linhas:")
        print(df.head(3))
    except Exception as e:
        print(f"Erro ao carregar: {e}")


if __name__ == "__main__":
    print("--- Teste 1: Plano Padrao (8 colunas) ---")
    utility_load_plan(1, 2013, "Balanço Patrimonial e Demonstração de Resultados")

    print("\n--- Teste 2: Plano Dinamico (9 colunas) ---")
    utility_load_plan(1, 2021, "Balanço Patrimonial")
