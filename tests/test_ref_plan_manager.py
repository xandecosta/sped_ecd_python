import os
import json
import pandas as pd
from intelligence.ref_plan_manager import RefPlanManager


def test_manager_integration():
    print("Iniciando Validação do RefPlanManager...")
    manager = RefPlanManager()

    # 1. Verificar catálogo
    if not os.path.exists(manager.catalog_path):
        print(f"ERRO: Catálogo não encontrado em {manager.catalog_path}")
        return False

    with open(manager.catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    print(f"Catálogo carregado: {len(catalog)} instituições mapeadas.")

    # 2. Testar busca lógica (Plan 1 - Lucro Real)
    plan_id = "1"
    if plan_id in catalog:
        years = catalog[plan_id].keys()
        print(f"Plan 1 possui dados para os anos: {list(years)}")

        # Testar um ano específico (ex: 2021)
        ano_teste = "2021"
        if ano_teste in catalog[plan_id]:
            entry = catalog[plan_id][ano_teste]
            # Pega a primeira versão disponível dinamicamente (ex: '1' ou '4')
            versions = list(entry["plans"]["REF"].keys())
            first_ver = versions[0]
            filename = entry["plans"]["REF"][first_ver]["file"]
            filepath = os.path.join(manager.schemas_dir, filename)

            print(f"Verificando arquivo unificado: {filename}")
            if os.path.exists(filepath):
                df = pd.read_csv(filepath, sep="|", nrows=5, dtype=str)
                print(f"Sucesso! Arquivo lido. Amostra de colunas: {list(df.columns)}")
                return True
            else:
                print(f"ERRO: Arquivo físico não encontrado: {filepath}")
        else:
            print(f"AVISO: Ano {ano_teste} não encontrado para o Plano 1 no catálogo.")
    else:
        print("ERRO: Plano 1 (Lucro Real) não encontrado no catálogo.")

    return False


if __name__ == "__main__":
    success = test_manager_integration()
    if success:
        print("\n>>> VALIDAÇÃO CONCLUÍDA: O Gerenciador de Planos está operacional!")
    else:
        print("\n>>> FALHA NA VALIDAÇÃO: Verifique os logs acima.")
