import pytest
import pandas as pd
from utils.historical_mapper import HistoricalMapper


def test_historical_mapper_bidirectional_learning():
    mapper = HistoricalMapper()
    cnpj = "12345678000100"

    # 1. Simula aprendizado de 2019 (Ano com dados)
    df_2019 = pd.DataFrame(
        {"COD_CTA": ["1.01", "1.02"], "COD_CTA_REF": ["REF_CAIXA", "REF_BANCO"]}
    )
    mapper.learn(cnpj, "2019", df_2019)

    # 2. Simula aprendizado de 2021 (Futuro ensinando)
    df_2021 = pd.DataFrame({"COD_CTA": ["1.03"], "COD_CTA_REF": ["REF_CLIENTES"]})
    mapper.learn(cnpj, "2021", df_2021)

    # Constrói consenso
    mapper.build_consensus()

    # 3. Teste: Conta declarada no próprio ano
    res_2019_cta1 = mapper.get_mapping(cnpj, "1.01", "2019")
    assert res_2019_cta1["COD_CTA_REF"] == "REF_CAIXA"
    assert res_2019_cta1["ORIGEM_MAP"] == "DECLARADO"

    # 4. Teste: Lacuna em 2020 preenchida pelo PASSADO (2019)
    res_2020_cta2 = mapper.get_mapping(cnpj, "1.02", "2020")
    assert res_2020_cta2["COD_CTA_REF"] == "REF_BANCO"
    assert res_2020_cta2["ORIGEM_MAP"] == "HISTORICO_2019"

    # 5. Teste: Lacuna em 2020 preenchida pelo FUTURO (2021)
    res_2020_cta3 = mapper.get_mapping(cnpj, "1.03", "2020")
    assert res_2020_cta3["COD_CTA_REF"] == "REF_CLIENTES"
    assert res_2020_cta3["ORIGEM_MAP"] == "HISTORICO_2021"


def test_historical_mapper_consensus_frequency():
    mapper = HistoricalMapper()
    cnpj = "999"
    cta = "CONTA_CONFLITO"

    # Aprende mapeamentos divergentes
    mapper.learn(
        cnpj, "2018", pd.DataFrame({"COD_CTA": [cta], "COD_CTA_REF": ["REF_A"]})
    )
    mapper.learn(
        cnpj, "2019", pd.DataFrame({"COD_CTA": [cta], "COD_CTA_REF": ["REF_B"]})
    )
    mapper.learn(
        cnpj, "2020", pd.DataFrame({"COD_CTA": [cta], "COD_CTA_REF": ["REF_B"]})
    )

    mapper.build_consensus()

    # Deve escolher REF_B pois aparece 2 vezes contra 1 de REF_A
    res = mapper.get_mapping(cnpj, cta, "2021")
    assert res["COD_CTA_REF"] == "REF_B"


def test_historical_mapper_no_data():
    mapper = HistoricalMapper()
    res = mapper.get_mapping("000", "XXX", "2020")
    assert res["COD_CTA_REF"] is None
    assert res["ORIGEM_MAP"] == "SEM_MAPEAMENTO"
