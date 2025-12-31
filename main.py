import os
import glob
import logging
from core.reader_ecd import ECDReader
from core.processor import ECDProcessor
from utils.exporter import ECDExporter

# Configuração de Logs para acompanhar o progresso no terminal
logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")


def executar_pipeline_ecd():
    # 1. Configuração de Caminhos
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "data", "input")
    output_dir = os.path.join(base_dir, "data", "output")

    # 2. Localizar o arquivo ECD (Pega o primeiro .txt da pasta input)
    arquivos = glob.glob(os.path.join(input_dir, "*.txt"))
    if not arquivos:
        logging.error("Nenhum arquivo .txt encontrado em data/input. Abortando.")
        return

    caminho_arquivo = arquivos[0]
    nome_projeto = os.path.basename(caminho_arquivo).replace(".txt", "")
    logging.info(f"Iniciando processamento: {caminho_arquivo}")

    # --- PASSO 1: LEITURA ---
    reader = ECDReader(caminho_arquivo)
    # Convertemos o gerador em lista para o processor (necessário para múltiplos passos)
    registros = list(reader.processar_arquivo())
    logging.info(f"Leitura concluída. {len(registros)} registros carregados.")

    # --- PASSO 2: PROCESSAMENTO ---
    processor = ECDProcessor(registros)

    # Gerar Bases Principais (Joins e Limpeza)
    df_plano = processor.processar_plano_contas()
    df_lancamentos = processor.processar_lancamentos(df_plano)
    df_saldos = processor.processar_saldos_mensais()

    # Gerar Demonstrações (J100/J150)
    demos = processor.processar_demonstracoes()

    # Executar o Motor de Propagação (A inteligência contábil)
    df_balancete = processor.gerar_balancetes()
    logging.info("Processamento contábil e propagação de saldos concluídos.")

    # --- PASSO 3: EXPORTAÇÃO ---
    exporter = ECDExporter(output_dir)

    tabelas_para_exportar = {
        "01_Plano_Contas": df_plano,
        "02_Lancamentos_Contabeis": df_lancamentos,
        "03_Saldos_Mensais": df_saldos,
        "04_Balancetes_Mensais": df_balancete,
        "05_BP": demos["BP"],
        "06_DRE": demos["DRE"],
    }

    exporter.exportar_lote(tabelas_para_exportar, nome_projeto)
    logging.info("=== PROCESSO FINALIZADO COM SUCESSO ===")


if __name__ == "__main__":
    executar_pipeline_ecd()
