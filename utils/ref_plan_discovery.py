import os
import pandas as pd


def discover_ref_plan_layouts():
    dir_planos = r"g:\Drives compartilhados\10_Arquivo\002_Programacao_Desenvolvimento\python_ecd\data\plano_contas_referencial"
    out_file = r"g:\Drives compartilhados\10_Arquivo\002_Programacao_Desenvolvimento\python_ecd\data\reference\leiaute_plano_contas_referencial.xlsx"

    if not os.path.exists(dir_planos):
        print(f"Erro: Diretorio {dir_planos} nao encontrado.")
        return

    arquivos = [f for f in os.listdir(dir_planos) if f.endswith(".txt")]
    dados = []

    for nome_arq in arquivos:
        caminho = os.path.join(dir_planos, nome_arq)
        try:
            with open(caminho, "r", encoding="latin1") as f:
                primeira_linha = f.readline().strip()
                dados.append({"Arquivo": nome_arq, "Cabecalho": primeira_linha})
        except Exception as e:
            print(f"Erro ao ler {nome_arq}: {e}")
            dados.append({"Arquivo": nome_arq, "Cabecalho": f"ERRO: {e}"})

    df = pd.DataFrame(dados)

    # Garante que a pasta reference existe
    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    df.to_excel(out_file, index=False, engine="openpyxl")
    print(f"Arquivo gerado com sucesso em: {out_file}")


if __name__ == "__main__":
    discover_ref_plan_layouts()
