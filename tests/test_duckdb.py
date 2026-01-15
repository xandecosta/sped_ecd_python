import duckdb
import glob

# 1. Busca automática por qualquer arquivo de Balancete na pasta output
# Isso evita que o erro de 'arquivo não encontrado' se você tiver uma data diferente
arquivos_encontrados = glob.glob(
    "data/output/**/20*_03_Balancetes_Mensais.parquet", recursive=True
)

if not arquivos_encontrados:
    print("[ERRO] Nenhum arquivo Parquet de Balancete foi encontrado em data/output.")
    print("Execute o 'python main.py' primeiro para gerar os dados de teste.")
else:
    # Vamos usar o primeiro arquivo que ele encontrar
    caminho_parquet = arquivos_encontrados[0]
    print(f"[OK] Arquivo localizado para o teste: {caminho_parquet}")

    print("\n--- Analisando com DuckDB (Performance Turbo) ---")

    # 2. O 'Pulo do Gato' do DuckDB:
    # Usamos o SQL direto no arquivo Parquet sem precisar de um banco de dados real
    query = f"""
        SELECT 
            count(*) as total_linhas,
            sum(VL_SLD_FIN_SIG) as soma_saldos_finais,
            sum(VL_DEB) as soma_debitos,
            sum(VL_CRED) as soma_creditos
        FROM read_parquet('{caminho_parquet}')
    """

    # Executa a query
    relatorio = duckdb.query(query).fetchone()

    if relatorio is not None:
        print(f"Total de contas no balancete: {relatorio[0]}")
        print(f"Soma total dos saldos finais: R$ {relatorio[1]:,.2f}")
        print(f"Soma total dos debitos: R$ {relatorio[2]:,.2f}")
        print(f"Soma total dos creditos: R$ {relatorio[3]:,.2f}")
    else:
        print("[ERRO] Não foi possível obter os dados do balancete.")

    print("\nDuckDB está operacional e pronto para a Fase 1!")
