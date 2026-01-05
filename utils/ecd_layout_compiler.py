import pandas as pd
import json
import os
import logging
from typing import cast, Dict, Any

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

INPUT_CAMPOS = r"data/reference/campos_por_registros.csv"
INPUT_REGISTROS = r"data/reference/registros_por_leiaute.csv"
OUTPUT_DIR = r"schemas/ecd_layouts"


def compile_ecd_layouts():
    """
    Lê os CSVs de parâmetros e gera arquivos JSON por versão de layout,
    incluindo a hierarquia (Nível) e validando se o registro pertence ao layout.
    """

    if not os.path.exists(INPUT_CAMPOS) or not os.path.exists(INPUT_REGISTROS):
        logging.error("Arquivos de entrada não encontrados.")
        return

    try:
        # --- 1. Leitura e Preparação dos Dados ---

        # Leitura dos Campos
        df_campos = pd.read_csv(INPUT_CAMPOS, sep=";", encoding="utf-8-sig", dtype=str)
        # Limpar colunas e dados
        df_campos.columns = pd.Index([str(c).strip() for c in df_campos.columns])
        df_campos = df_campos.apply(
            lambda x: cast(pd.Series, x).str.strip() if x.dtype == "object" else x
        )

        # Tratamento de Tipos nos Campos
        df_campos["Decimal"] = (
            cast(
                pd.Series,
                cast(pd.Series, df_campos["Decimal"]).replace({"-": "0", "": "0"}),
            )
            .fillna("0")
            .astype(int)
        )
        df_campos["Ordem"] = (
            cast(
                pd.Series,
                pd.to_numeric(cast(pd.Series, df_campos["Ordem"]), errors="coerce"),
            )
            .fillna(0)
            .astype(int)
        )
        df_campos["Tamanho"] = (
            cast(
                pd.Series,
                pd.to_numeric(cast(pd.Series, df_campos["Tamanho"]), errors="coerce"),
            )
            .fillna(0)
            .astype(int)
        )

        # Leitura dos Registros (Hierarquia)
        df_registros = pd.read_csv(
            INPUT_REGISTROS, sep=";", encoding="utf-8-sig", dtype=str
        )
        df_registros.columns = pd.Index([str(c).strip() for c in df_registros.columns])
        df_registros = df_registros.apply(
            lambda x: cast(pd.Series, x).str.strip() if x.dtype == "object" else x
        )

        # Converter Nivel para int
        df_registros["Nivel"] = (
            cast(
                pd.Series,
                pd.to_numeric(cast(pd.Series, df_registros["Nivel"]), errors="coerce"),
            )
            .fillna(0)
            .astype(int)
        )

        # --- 2. Geração de Schemas ---
        versoes = cast(pd.Series, df_campos["Versao"]).unique()
        logging.info(f"Versões encontradas em Campos: {versoes}")

        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        for versao in versoes:
            if not versao or pd.isna(versao):
                continue

            # Extrair número da versão para mapear com a coluna Leiaute_X do csv de registros
            # Ex: 9.00 -> 9
            versao_num = int(float(str(versao)))
            coluna_leiaute = f"Leiaute_{versao_num}"

            if coluna_leiaute not in df_registros.columns:
                logging.warning(
                    f"Versão {versao} (Coluna {coluna_leiaute}) não encontrada no arquivo de registros. Pulando validação cruzada rigorosa."
                )
                # Fallback: assume que todos os registros da versão são válidos se a coluna não existir
                # Usando .loc para garantir que o resultado da filtragem seja tratado como DataFrame
                df_filtro_ver = df_campos.loc[df_campos["Versao"] == versao]
                registros_validos_map: Dict[str, Any] = {
                    str(r): 0 for r in cast(pd.Series, df_filtro_ver["REG"]).unique()
                }
            else:
                # Filtra apenas registros marcados com 'S' para este layout
                df_reg_versao = df_registros.loc[df_registros[coluna_leiaute] == "S"]
                # Mapa de Registro -> Nivel
                registros_validos_map = dict(
                    zip(df_reg_versao["Registro"], df_reg_versao["Nivel"])
                )

            # Inicia estrutura do Schema
            schema_json = {}

            # Filtra campos desta versão
            df_ver = df_campos.loc[df_campos["Versao"] == versao]
            registros_da_versao = cast(pd.Series, df_ver["REG"]).unique()

            for reg in registros_da_versao:
                # Cruzamento: Verifica se o registro é válido para este layout e pega o nível
                if reg not in registros_validos_map:
                    # Se não estiver no mapa de registros válidos, ignoramos (não deve estar no JSON)
                    # Exceção: Talvez o CSV de campos tenha registros que o de layout diz 'N'. Respeitamos o de Layout.
                    continue

                nivel = registros_validos_map[reg]

                # Monta lista de campos
                campos_df = df_ver.loc[df_ver["REG"] == reg].sort_values(by="Ordem")
                lista_campos = []
                for _, row in campos_df.iterrows():
                    campo = {
                        "nome": row["CampoUnico"],
                        "tipo": row["Tipo"],
                        "tamanho": int(row["Tamanho"]),
                        "decimal": int(row["Decimal"]),
                    }
                    lista_campos.append(campo)

                # Nova Estrutura com 'nivel'
                schema_json[str(reg)] = {"nivel": int(nivel), "campos": lista_campos}

            # Salvar JSON
            nome_arquivo = f"layout_{versao}.json"
            caminho_arquivo = os.path.join(OUTPUT_DIR, nome_arquivo)

            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                json.dump(schema_json, f, indent=2, ensure_ascii=False)

            logging.info(
                f"Schema gerado: {nome_arquivo} ({len(schema_json)} registros)"
            )

        logging.info("Processo de geração concluído com sucesso.")

    except Exception as e:
        logging.error(f"Erro no processamento: {e}")
        raise


if __name__ == "__main__":
    compile_ecd_layouts()
