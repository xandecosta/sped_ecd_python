import pytest
from datetime import date
from decimal import Decimal
from core.reader_ecd import ECDReader


@pytest.fixture
def fake_ecd_file(tmp_path):
    """
    Cria um arquivo ECD fake para testes controlados e independentes.
    """
    d = tmp_path / "sub"
    d.mkdir()
    f = d / "fake_ecd.txt"

    # Conteúdo mínimo para um ECD válido no nosso parser
    conteúdo = [
        "|0000|LECD|01012020|31122020|EMPRESA TESTE|12345678000199|UF||00001|9.00|",
        "|I010|G|9.00|",
        "|I150|01012020|31012020|",
        "|I155|01.1.1.01.001||150,55|D|0,00|C|",
        "|9999|",
    ]
    f.write_text("\n".join(conteúdo), encoding="latin-1")
    return str(f)


def test_detectar_layout_fake(fake_ecd_file):
    """Garante que o layout é detectado corretamente em um arquivo controlado."""
    reader = ECDReader(fake_ecd_file)
    reader._detectar_layout()
    assert reader.layout_versao == "9.00"
    assert reader.schema is not None


def test_arquivo_inexistente():
    """Garante que o sistema lança FileNotFoundError se o arquivo não existir."""
    with pytest.raises(FileNotFoundError):
        reader = ECDReader("caminho/fantasma.txt")
        reader._detectar_layout()


def test_captura_periodo_ecd(fake_ecd_file):
    """Validação do 0000: Garante que periodo_ecd é preenchido corretamente."""
    reader = ECDReader(fake_ecd_file)
    # Roda o gerador para processar o primeiro registro
    next(reader.processar_arquivo())

    # O 0000_DT_FIN no fake é 31122020 -> YYYYMMDD = 20201231
    assert reader.periodo_ecd == "20201231"


def test_conversao_tipos_direta():
    """Teste de Tipagem: Valida o método individualmente sem depender de arquivo."""
    reader = ECDReader("dummy.txt")

    # Data com zero suprimido
    assert reader._converter_valor("1012020", "N", 0, "DT_INI") == date(2020, 1, 1)

    # Decimal financeiro
    res_decimal = reader._converter_valor("100,50", "N", 2, "VALOR")
    assert isinstance(res_decimal, Decimal)
    assert res_decimal == Decimal("100.50")

    # Identificador String
    assert reader._converter_valor("000123", "N", 0, "COD_CTA") == "000123"


def test_hierarquia_com_fake(fake_ecd_file):
    """Teste de Hierarquia: Valida PK e FK_PAI em fluxo controlado."""
    reader = ECDReader(fake_ecd_file)
    registros = list(reader.processar_arquivo())

    reg_i150 = next(r for r in registros if r["REG"] == "I150")
    reg_i155 = next(r for r in registros if r["REG"] == "I155")

    # No schema 9.00: I150 (nivel 3), I155 (nivel 4)
    if reader.schema and "I155" in reader.schema and "I150" in reader.schema:
        if reader.schema["I155"]["nivel"] > reader.schema["I150"]["nivel"]:
            # Se I155 é filho direto ou descendente, deve ter herdado o pai no contexto
            assert reg_i155["FK_PAI"] == reg_i150["PK"]
