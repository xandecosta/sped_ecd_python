import os
import glob
import logging
import traceback
from core.reader_ecd import ECDReader
from core.processor import ECDProcessor
from utils.exporter import ECDExporter

# Configuração de Logs
# Usamos ERROR para o console para manter o terminal limpo
# Mas mantemos informações críticas via print ou logging manual
logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")


def processar_um_arquivo(caminho_arquivo: str, output_base: str):
    """
    Executa o ciclo completo de processamento para um único arquivo.
    """
    nome_arquivo = os.path.basename(caminho_arquivo)
    nome_projeto = nome_arquivo.replace(".txt", "")

    print(f"\n>>> PROCESSANDO: {nome_arquivo}")

    try:
        # --- PASSO 1: LEITURA ---
        reader = ECDReader(caminho_arquivo)
        registros = list(reader.processar_arquivo())
        if not registros:
            print(f"      [AVISO] Arquivo vazio ou sem registros válidos.")
            return

        # Captura o Período (YYYYMMDD) gerado pelo reader durante o processamento do reg 0000
        # Se não encontrado (arquivo inválido), usa o nome do projeto como fallback
        id_folder = reader.periodo_ecd if reader.periodo_ecd else nome_projeto

        # Define pasta de saída específica para este arquivo (Estrutura Flat)
        pasta_saida_arquivo = os.path.join(output_base, id_folder)

        # --- PASSO 2: PROCESSAMENTO ---
        processor = ECDProcessor(registros)

        # Gerar Bases
        df_plano = processor.processar_plano_contas()
        df_lancamentos = processor.processar_lancamentos(df_plano)
        df_saldos = processor.processar_saldos_mensais()
        df_balancete = processor.gerar_balancetes()
        demos = processor.processar_demonstracoes()

        # --- PASSO 3: EXPORTAÇÃO ---
        exporter = ECDExporter(pasta_saida_arquivo)

        tabelas = {
            "01_Plano_Contas": df_plano,
            "02_Lancamentos_Contabeis": df_lancamentos,
            "03_Saldos_Mensais": df_saldos,
            "04_Balancetes_Mensais": df_balancete,
            "05_BP": demos["BP"],
            "06_DRE": demos["DRE"],
        }

        exporter.exportar_lote(tabelas, nome_projeto)
        print(f"      [OK] Finalizado com sucesso: {pasta_saida_arquivo}")

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

    # 1. Localizar todos os arquivos .txt
    arquivos = glob.glob(os.path.join(input_dir, "*.txt"))

    if not arquivos:
        print("Nenhum arquivo .txt encontrado em data/input.")
        return

    print(f"=== INICIANDO LOTE: {len(arquivos)} ARQUIVOS ENCONTRADOS ===")

    # 2. Processar cada arquivo individualmente
    for caminho in arquivos:
        processar_um_arquivo(caminho, output_dir)

    print("\n=== LOTE FINALIZADO ===")


if __name__ == "__main__":
    executar_pipeline_batch()
