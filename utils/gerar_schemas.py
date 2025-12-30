import pandas as pd
import json
import os
import logging

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

INPUT_FILE = r"data_raw/campos_por_registros.csv"
OUTPUT_DIR = r"schemas"


def gerar_schemas():
    """Lê o CSV de parâmetros e gera arquivos JSON por versão de layout."""

    if not os.path.exists(INPUT_FILE):
        logging.error(f"Arquivo de entrada não encontrado: {INPUT_FILE}")
        return

    try:
        # 1. Leitura Segura
        df = pd.read_csv(
            INPUT_FILE,
            sep=";",
            encoding="utf-8-sig",
            # quoting=3, # REMOVIDO: Causava erro em campos com ; entre aspas
            dtype=str,  # Ler tudo como string inicialmente para tratamento seguro
        )

        # 2. Limpeza de Nomes (Strip)
        df.columns = [c.strip() for c in df.columns]
        # Aplica strip em todas as células de string
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

        # 3. Tratamento de Tipos
        # Converte Decimal para int, tratando vazios e hífens como 0
        df["Decimal"] = (
            df["Decimal"].replace({"-": "0", "": "0"}).fillna("0").astype(int)
        )

        # Converte Ordem para int
        df["Ordem"] = pd.to_numeric(df["Ordem"], errors="coerce").fillna(0).astype(int)

        # Converte Tamanho para int (se possível)
        df["Tamanho"] = (
            pd.to_numeric(df["Tamanho"], errors="coerce").fillna(0).astype(int)
        )

        # 4. Geração de Schemas
        versoes = df["Versao"].unique()
        logging.info(f"Versões encontradas: {versoes}")

        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        for versao in versoes:
            if not versao:
                continue  # Pula versões vazias se houver

            df_ver = df[df["Versao"] == versao]
            schema_json = {}

            registros = df_ver["REG"].unique()

            for reg in registros:
                campos_df = df_ver[df_ver["REG"] == reg].sort_values("Ordem")

                lista_campos = []
                for _, row in campos_df.iterrows():
                    campo = {
                        "nome": row["CampoUnico"],
                        "tipo": row["Tipo"],
                        "tamanho": int(row["Tamanho"]),
                        "decimal": int(row["Decimal"]),
                    }
                    lista_campos.append(campo)

                schema_json[reg] = lista_campos

            # Salvar JSON
            nome_arquivo = f"layout_{versao}.json"
            caminho_arquivo = os.path.join(OUTPUT_DIR, nome_arquivo)

            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                json.dump(schema_json, f, indent=2, ensure_ascii=False)

            logging.info(f"Schema gerado: {nome_arquivo} ({len(registros)} registros)")

        logging.info("Processo de geração concluído com sucesso.")

    except Exception as e:
        logging.error(f"Erro no processamento: {e}")
        raise


if __name__ == "__main__":
    gerar_schemas()
