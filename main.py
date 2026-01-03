import os
import glob
import logging
import traceback
import warnings
from core.reader_ecd import ECDReader
from core.processor import ECDProcessor
from utils.exporter import ECDExporter

# 1. Silenciar Avisos de Bibliotecas (Pandas, etc)
warnings.filterwarnings("ignore")

# 2. Silenciar Logs de Sistema e Módulos (Apenas Erros Críticos)
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")
logging.getLogger("core.reader_ecd").setLevel(logging.ERROR)


def processar_um_arquivo(caminho_arquivo: str, output_base: str):
    """
    Executa o ciclo completo de processamento para um único arquivo ECD.
    """
    nome_arquivo = os.path.basename(caminho_arquivo)
    nome_projeto = nome_arquivo.replace(".txt", "")

    print(f"\n>>> PROCESSANDO: {nome_arquivo}")

    try:
        # --- PASSO 1: LEITURA ---
        reader = ECDReader(caminho_arquivo)
        registros = list(reader.processar_arquivo())

        if not registros:
            print("      [AVISO] Arquivo vazio ou sem registros válidos.")
            return

        # Captura metadados críticos do Reader para o processamento de auditoria
        id_folder = reader.periodo_ecd if reader.periodo_ecd else nome_projeto
        cnpj_contribuinte = getattr(reader, "cnpj", "")

        # --- PASSO 2: PROCESSAMENTO ---
        # Instancia o processador com os metadados para injeção e mapeamento RFB
        processor = ECDProcessor(
            registros, cnpj=cnpj_contribuinte, layout_versao=reader.layout_versao or ""
        )

        df_plano = processor.processar_plano_contas()
        df_lancamentos = processor.processar_lancamentos(df_plano)

        # O método gerar_balancetes agora retorna um dicionário (Empresa e baseRFB)
        dict_balancetes = processor.gerar_balancetes()

        # O método processar_demonstracoes retorna um dicionário (BP e DRE)
        dict_demos = processor.processar_demonstracoes()

        # --- PASSO 3: EXPORTAÇÃO ---
        pasta_saida_arquivo = os.path.join(output_base, id_folder)
        exporter = ECDExporter(pasta_saida_arquivo)

        # Consolidamos todas as tabelas seguindo a hierarquia de prioridade de auditoria
        # Reorganizado para manter as demonstrações no topo (01 e 02)
        tabelas = {
            "01_BP": dict_demos.get("BP"),
            "02_DRE": dict_demos.get("DRE"),
            "03_Balancetes_Mensais": dict_balancetes.get("04_Balancetes_Mensais"),
            "04_Balancete_baseRFB": dict_balancetes.get("04_Balancetes_RFB"),
            "05_Plano_Contas": df_plano,
            "06_Lancamentos_Contabeis": df_lancamentos,
        }

        # Exporta com o prefixo da data para permitir abertura simultânea no Excel
        exporter.exportar_lote(tabelas, nome_projeto, prefixo=id_folder)

        print(f"      [OK] Finalizado com sucesso: {id_folder}")

    except Exception as e:
        print(f"      [ERRO] Falha ao processar {nome_arquivo}: {str(e)}")
        logging.error(traceback.format_exc())


def executar_pipeline_batch():
    """
    Localiza todos os arquivos ECD e gerencia o processamento em lote.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "data", "input")
    output_dir = os.path.join(base_dir, "data", "output")

    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        print(f"Pasta de entrada criada: {input_dir}. Adicione os arquivos .txt nela.")
        return

    arquivos = glob.glob(os.path.join(input_dir, "*.txt"))

    if not arquivos:
        print("Nenhum arquivo .txt encontrado na pasta data/input.")
        return

    print(f"Iniciando processamento de {len(arquivos)} arquivo(s)...")

    for arquivo in arquivos:
        processar_um_arquivo(arquivo, output_dir)


if __name__ == "__main__":
    executar_pipeline_batch()
