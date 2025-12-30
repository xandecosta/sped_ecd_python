import json
import logging
import os
import glob
from typing import Generator, Dict, Any, Optional

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class ECDReader:
    def __init__(self, caminho_arquivo: str):
        self.caminho_arquivo = caminho_arquivo
        self.layout_versao: Optional[str] = None
        self.schema: Optional[Dict[str, Any]] = None
        # Assume que schemas está no diretório pai de core/
        self.schemas_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schemas"
        )

    def _detectar_layout(self) -> None:
        """
        Detecta a versão do layout lendo o registro I010.
        Carrega o schema JSON correspondente.
        """
        logging.info(f"Detectando layout do arquivo: {self.caminho_arquivo}")

        if not os.path.exists(self.caminho_arquivo):
            raise FileNotFoundError(f"Arquivo não encontrado: {self.caminho_arquivo}")

        with open(self.caminho_arquivo, "r", encoding="latin-1", errors="replace") as f:
            for linha in f:
                if linha.startswith("|I010|"):
                    partes = linha.split("|")
                    # Ex: |I010|G|9.00| -> ['', 'I010', 'G', '9.00', '...']
                    if len(partes) > 3:
                        self.layout_versao = partes[3]
                        logging.info(f"Layout detectado: {self.layout_versao}")
                        self._carregar_schema()
                        return

        if not self.layout_versao:
            raise ValueError(
                "Não foi possível detectar a versão do layout (Registro I010 não encontrado)."
            )

    def _carregar_schema(self) -> None:
        """Carrega o arquivo JSON do schema correspondente à versão detectada."""
        nome_arquivo = f"layout_{self.layout_versao}.json"
        caminho_schema = os.path.join(self.schemas_dir, nome_arquivo)

        logging.info(f"Carregando schema: {caminho_schema}")

        if not os.path.exists(caminho_schema):
            raise ValueError(
                f"Schema não encontrado para a versão {self.layout_versao}: {caminho_schema}"
            )

        with open(caminho_schema, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

    def processar_arquivo(self) -> Generator[Dict[str, Any], None, None]:
        """
        Lê o arquivo linha a linha e converte para dicionários usando o schema.
        Ignora o Bloco C por enquanto.
        """
        if not self.schema:
            self._detectar_layout()

        logging.info(f"Iniciando processamento do arquivo: {self.caminho_arquivo}")

        with open(self.caminho_arquivo, "r", encoding="latin-1", errors="replace") as f:
            for numero_linha, linha in enumerate(f, 1):
                linha = linha.strip()
                if not linha or not linha.startswith("|"):
                    continue

                partes = linha.split("|")
                # O split de "|REG|..." gera um elemento vazio no início.
                # partes[0] é '', partes[1] é o REG
                if len(partes) < 2:
                    continue

                registro = partes[1]

                # Ignorar Bloco C
                if registro.startswith("C"):
                    continue

                if registro not in self.schema:
                    # Opcional: Logar apenas a primeira ocorrência ou usar nível DEBUG para não poluir
                    logging.debug(
                        f"Linha {numero_linha}: Registro {registro} não mapeado no schema."
                    )
                    continue

                campos_layout = self.schema[registro]
                dados_registro = {}

                for i, def_campo in enumerate(campos_layout):
                    # O indice no 'partes' é i + 1 (pois partes[0] é '')
                    idx_valor = i + 1

                    valor_processado = None

                    if idx_valor < len(partes):
                        valor_bruto = partes[idx_valor]
                        # Tratamento simples de tipos
                        tipo = def_campo.get("tipo", "C")
                        decimal = def_campo.get("decimal", 0)

                        valor_processado = valor_bruto

                        if tipo == "N" and valor_bruto:
                            try:
                                # SPED usa vírgula como separador decimal
                                valor_fmt = valor_bruto.replace(",", ".")
                                if decimal > 0:
                                    valor_processado = float(valor_fmt)
                                else:
                                    valor_processado = int(
                                        float(valor_fmt)
                                    )  # float primeiro para garantir caso venha 1.00
                            except ValueError:
                                # Fallback para string em caso de erro de conversão
                                logging.warning(
                                    f"Erro de conversão (N) na linha {numero_linha}, campo {def_campo['nome']}: {valor_bruto}"
                                )
                                valor_processado = valor_bruto
                        elif tipo == "N" and not valor_bruto:
                            valor_processado = 0.0 if decimal > 0 else 0

                    dados_registro[def_campo["nome"]] = valor_processado

                yield dados_registro


if __name__ == "__main__":
    # Bloco de Teste
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(base_dir, "data", "input")

    arquivos_txt = glob.glob(os.path.join(input_dir, "*.txt"))

    if arquivos_txt:
        # Pega o último arquivo da lista (simulando seleção)
        arquivo_teste = arquivos_txt[-1]
        print(f"--- TESTANDO ECDReader com: {os.path.basename(arquivo_teste)} ---")

        try:
            reader = ECDReader(arquivo_teste)
            gerador = reader.processar_arquivo()

            print("\n[Primeiros 10 Registros Processados]")
            for i, reg in enumerate(gerador):
                print(f"#{i + 1}: {reg}")
                if i >= 9:
                    break
            print("\nTeste concluído.")

        except Exception as e:
            logging.error(f"FALHA NO TESTE: {e}", exc_info=True)
    else:
        print(f"Nenhum arquivo .txt encontrado em: {input_dir}")
