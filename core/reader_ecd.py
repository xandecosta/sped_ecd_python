import json
import logging
import os
import glob
from datetime import datetime, date
from typing import Generator, Dict, Any, Optional

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class ECDReader:
    def __init__(self, caminho_arquivo: str):
        self.caminho_arquivo = caminho_arquivo
        self.layout_versao: Optional[str] = None
        self.schema: Optional[Dict[str, Any]] = None
        self.periodo_ecd: Optional[str] = None  # YYYYMMDD do registro 0000
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

    def _converter_valor(
        self, valor: str, tipo: str, decimal: int, nome_campo: str
    ) -> Any:
        """Converte o valor string para o tipo apropriado."""
        if not valor:
            return None

        if tipo == "N":
            try:
                # Substitui vírgula por ponto para conversão
                valor_fmt = valor.replace(",", ".")
                if decimal > 0:
                    return float(valor_fmt)
                else:
                    return int(float(valor_fmt))
            except ValueError:
                logging.warning(
                    f"Erro de conversão Numérica no campo {nome_campo}: '{valor}'"
                )
                return None

        # Tentativa de detecção de data pelo nome do campo
        if "DT_" in nome_campo or "DATA" in nome_campo:
            # Formato esperado: DDMMYYYY
            if len(valor) == 8 and valor.isdigit():
                try:
                    return datetime.strptime(valor, "%d%m%Y").date()
                except ValueError:
                    # Pode não ser uma data válida, retorna string
                    pass

        return valor

    def processar_arquivo(self) -> Generator[Dict[str, Any], None, None]:
        """
        Lê o arquivo linha a linha, gera PK/FK e converte dados.
        """
        if not self.schema:
            self._detectar_layout()

        logging.info(f"Iniciando processamento do arquivo: {self.caminho_arquivo}")

        # Contexto de Pais: {nivel: pk_do_registro}
        contexto_pais: Dict[int, str] = {}

        with open(self.caminho_arquivo, "r", encoding="latin-1", errors="replace") as f:
            for numero_linha, linha in enumerate(f, 1):
                linha = linha.strip()
                if not linha or not linha.startswith("|"):
                    continue

                partes = linha.split("|")
                if len(partes) < 2:
                    continue

                registro = partes[1]

                # Ignorar Bloco C (conforme especificação original)
                if registro.startswith("C"):
                    continue

                if registro not in self.schema:
                    # logging.debug(f"Linha {numero_linha}: Registro {registro} não mapeado.")
                    continue

                # Obter definição do schema
                def_registro = self.schema[registro]
                nivel = def_registro.get("nivel", 0)
                campos_layout = def_registro.get("campos", [])

                dados_registro = {"REG": registro, "LINHA_ORIGEM": numero_linha}

                # --- Extração de Campos ---
                for i, def_campo in enumerate(campos_layout):
                    idx_valor = i + 1  # offset do pipe inicial
                    valor_bruto = partes[idx_valor] if idx_valor < len(partes) else ""

                    valor_final = self._converter_valor(
                        valor_bruto,
                        def_campo["tipo"],
                        def_campo["decimal"],
                        def_campo["nome"],
                    )
                    dados_registro[def_campo["nome"]] = valor_final

                # --- Captura de Período (Registro 0000) ---
                if registro == "0000":
                    dt_fin = dados_registro.get("0000_DT_FIN")
                    if isinstance(dt_fin, date):
                        self.periodo_ecd = dt_fin.strftime("%Y%m%d")
                    elif isinstance(
                        dt_fin, (int, float)
                    ):  # Fallback se conversão falhar ou for numérico estranho
                        self.periodo_ecd = str(dt_fin)
                    else:
                        # Tenta pegar bruto se a conversão de data falhou mas tem 8 digitos
                        if partes[4] and len(partes[4]) == 8:
                            # 0000_DT_FIN é o 4º campo (indice 4 no array partes [0, REG, LECD, DT_INI, DT_FIN])
                            # Ops, partes[0]='', [1]='0000', [2]=LECD, [3]=DT_INI, [4]=DT_FIN
                            # Confirmando schema:
                            # 1: REG, 2: LECD, 3: DT_INI, 4: DT_FIN
                            # Então partes[4] é o valor.
                            # Correção: partes[4] seria DT_INI se seguir a ordem, vamos confiar no dicionário
                            pass

                    if not self.periodo_ecd:
                        logging.warning(
                            "Não foi possível detectar DT_FIN no registro 0000. PKs podem ficar inconsistentes."
                        )
                        self.periodo_ecd = "UNKNOWN"

                # --- Geração de PK ---
                # PK = {PERIODO}_{LINHA:08d}
                # Se periodo for unknown, usa apenas linha
                pk_prefix = self.periodo_ecd if self.periodo_ecd else "00000000"
                pk_atual = f"{pk_prefix}_{numero_linha:08d}"
                dados_registro["PK"] = pk_atual

                # --- Geração de FK (Pai) ---
                # A FK é a PK do último registro de nível imediatamente superior (nivel - 1)
                if nivel > 0:
                    fk_pai = contexto_pais.get(nivel - 1)
                    dados_registro["FK_PAI"] = fk_pai
                else:
                    dados_registro["FK_PAI"] = None

                # Atualizar o contexto de pais para o nível atual
                contexto_pais[nivel] = pk_atual

                # Limpar níveis inferiores do contexto (opcional, mas bom pra evitar lixo)
                # Se estou no nível 2, tudo que era nível 3+ do passado não é mais meu filho direto
                # Mas como é um dicionário e sobrescrevemos, não é estritamente necessário se a lógica for nivel-1

                yield dados_registro


if __name__ == "__main__":
    # Bloco de Teste
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(base_dir, "data", "input")

    arquivos_txt = glob.glob(os.path.join(input_dir, "*.txt"))

    if arquivos_txt:
        arquivo_teste = arquivos_txt[-1]
        print(f"--- TESTANDO ECDReader v2.0 com: {os.path.basename(arquivo_teste)} ---")

        try:
            reader = ECDReader(arquivo_teste)
            gerador = reader.processar_arquivo()

            print("\n[Primeiros 10 Registros Processados]")
            for i, reg in enumerate(gerador):
                print(
                    f"#{i + 1} [Nível: {reader.schema[reg['REG']].get('nivel')}] PK: {reg.get('PK')} | Pai: {reg.get('FK_PAI')} | {reg.get('REG')}"
                )
                # Imprimir alguns campos chaves para conferência
                # print(reg)
                if i >= 15:  # Aumentei um pouco para pegar filhos
                    break
            print("\nTeste concluído.")

        except Exception as e:
            logging.error(f"FALHA NO TESTE: {e}", exc_info=True)
    else:
        print(f"Nenhum arquivo .txt encontrado em: {input_dir}")
