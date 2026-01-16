import pandas as pd
from typing import Dict, Any, Optional
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class HistoricalMapper:
    """
    Gerencia o aprendizado e a inferência bidirecional de mapeamentos referenciais (I051).
    Foca na consistência temporal: se uma conta foi mapeada em qualquer ano da série
    histórica, esse conhecimento pode ser usado para preencher lacunas em outros anos.
    """

    def __init__(self):
        # Estrutura: { cnpj: { cod_cta: { ano: cod_cta_ref } } }
        self._knowledge: Dict[str, Dict[str, Dict[str, str]]] = {}
        # Estrutura: { cnpj: { cod_cta: cod_cta_ref_canonico } }
        self._consensus: Dict[str, Dict[str, str]] = {}

        # Estrutura: { cnpj: { ano: set(cod_cta) } }
        self._account_structures: Dict[str, Dict[str, set]] = {}

        # Estrutura: { cnpj: { ano: { cod_sup: Counter(cod_cta_ref) } } }
        self._group_knowledge: Dict[str, Dict[str, Dict[str, Counter]]] = {}

        # Novo: Rastreio de Instituição (COD_PLAN_REF)
        # { cnpj: { ano: cod_plan_ref } }
        self._plan_knowledge: Dict[str, Dict[str, str]] = {}
        # { cnpj: cod_plan_ref_canonico }
        self._plan_consensus: Dict[str, str] = {}

    def learn(
        self,
        cnpj: str,
        ano: str,
        df_mapping: pd.DataFrame,
        cod_plan_ref: Optional[str] = None,
        accounting_ctas: Optional[set] = None,
    ) -> None:
        """
        Coleta mapeamentos, identificação de plano e estrutura contábil.
        """
        if cnpj not in self._knowledge:
            self._knowledge[cnpj] = {}
        if cnpj not in self._plan_knowledge:
            self._plan_knowledge[cnpj] = {}
        if cnpj not in self._account_structures:
            self._account_structures[cnpj] = {}
        if cnpj not in self._group_knowledge:
            self._group_knowledge[cnpj] = {}

        # 1. Aprende a Estrutura Contábil (I050) para cálculo de similaridade posterior
        if accounting_ctas:
            self._account_structures[cnpj][str(ano)] = accounting_ctas

        # 2. Aprende a Instituição (COD_PLAN_REF) se fornecido
        if cod_plan_ref:
            self._plan_knowledge[cnpj][str(ano)] = str(cod_plan_ref)

        # 3. Aprende o Mapeamento de Contas
        if (
            df_mapping.empty
            or "COD_CTA" not in df_mapping.columns
            or "COD_CTA_REF" not in df_mapping.columns
        ):
            return

        # Filtra apenas registros com mapeamento preenchido
        df_valid = df_mapping.dropna(subset=["COD_CTA", "COD_CTA_REF"])

        for _, row in df_valid.iterrows():
            cta = str(row["COD_CTA"]).strip()
            ref = str(row["COD_CTA_REF"]).strip()

            if not cta or not ref:
                continue

            if cta not in self._knowledge[cnpj]:
                self._knowledge[cnpj][cta] = {}

            self._knowledge[cnpj][cta][str(ano)] = ref

            # 4. Aprende o mapeamento do Grupo (COD_SUP) se disponível
            sup_val = row.get("COD_SUP")
            # Usamos uma Series temporária para garantir um booleano simples (.empty) e tratar duplicatas
            sup_series = pd.Series(sup_val).dropna()
            if not sup_series.empty:
                sup = str(sup_series.iloc[0]).strip()
                if str(ano) not in self._group_knowledge[cnpj]:
                    self._group_knowledge[cnpj][str(ano)] = {}
                if sup not in self._group_knowledge[cnpj][str(ano)]:
                    self._group_knowledge[cnpj][str(ano)][sup] = Counter()
                self._group_knowledge[cnpj][str(ano)][sup][ref] += 1

    def find_best_neighbor(self, cnpj: str, target_year: str) -> Optional[str]:
        """
        Identifica qual ano tem o plano contábil (I050) mais parecido com o ano alvo.
        Útil para saber se devemos usar 2013 ou 2015 para completar 2014.
        """
        target_struct = self._account_structures.get(cnpj, {}).get(str(target_year))
        if not target_struct:
            return None

        best_year = None
        highest_similarity = -1.0

        for ano, struct in self._account_structures.get(cnpj, {}).items():
            if ano == str(target_year):
                continue

            # Verifica se esse ano candidato tem algum mapeamento para oferecer
            # (Não adianta ser parecido se não tiver I051)
            has_mappings = any(
                ano in year_maps for year_maps in self._knowledge.get(cnpj, {}).values()
            )
            if not has_mappings:
                continue

            # Cálculo de similaridade baseado em COBERTURA (Intersection / Size of Target)
            # Como sugerido: Se o ano alvo pode ser explicado pelo vizinho, isso é o que importa.
            intersection = len(target_struct.intersection(struct))
            score = (intersection / len(target_struct)) if target_struct else 0

            if score > highest_similarity:
                highest_similarity = score
                best_year = ano

        # Threshold de 50% de cobertura para considerar um vizinho confiável
        if highest_similarity >= 0.5:
            return best_year
        return None

    def build_consensus(self) -> None:
        """
        Analisa o histórico e define o mapeamento mais provável para cada conta.
        """
        self._consensus = {}
        for cnpj, accounts in self._knowledge.items():
            self._consensus[cnpj] = {}
            for cta, year_mappings in accounts.items():
                if not year_mappings:
                    continue
                counts = Counter(year_mappings.values())
                most_common_ref = counts.most_common(1)[0][0]
                self._consensus[cnpj][cta] = most_common_ref

        # 2. Consenso de Instituição (COD_PLAN_REF)
        self._plan_consensus = {}
        for cnpj, years in self._plan_knowledge.items():
            if not years:
                continue
            counts = Counter(years.values())
            self._plan_consensus[cnpj] = counts.most_common(1)[0][0]

    def get_mapping(
        self, cnpj: str, cod_cta: str, ano_atual: str, cod_sup: Optional[str] = None
    ) -> Dict[str, Optional[str]]:
        """
        Retorna o mapeamento seguindo a hierarquia:
        1. Declarado (I051) do próprio ano
        2. Ponte Virtual (Rodada 1): Vizinho + COD_CTA
        3. Ponte Virtual (Rodada 2): Vizinho + COD_SUP (Mais relevante do grupo)
        4. Consenso Global
        """
        # 1. Tenta o dado do próprio ano
        declared_ref = (
            self._knowledge.get(cnpj, {}).get(cod_cta, {}).get(str(ano_atual))
        )
        if declared_ref:
            return {"COD_CTA_REF": declared_ref, "ORIGEM_MAP": "I051"}

        # Identifica o Vizinho mais Próximo (Passado ou Futuro)
        best_neighbor = self.find_best_neighbor(cnpj, ano_atual)

        if best_neighbor:
            # 2. Ponte Virtual (Rodada 1): Vizinho + COD_CTA
            neighbor_ref = (
                self._knowledge.get(cnpj, {}).get(cod_cta, {}).get(best_neighbor)
            )
            if neighbor_ref:
                return {
                    "COD_CTA_REF": neighbor_ref,
                    "ORIGEM_MAP": f"{best_neighbor}_COD_CTA",
                }

            # 3. Ponte Virtual (Rodada 2): Vizinho + COD_SUP (Grupo)
            if cod_sup:
                sup_literal = str(cod_sup).strip()
                group_data = self._group_knowledge.get(cnpj, {}).get(best_neighbor, {})
                if sup_literal in group_data:
                    # Pega a conta referencial mais frequente no grupo do vizinho
                    most_relevant_ref = group_data[sup_literal].most_common(1)[0][0]
                    return {
                        "COD_CTA_REF": most_relevant_ref,
                        "ORIGEM_MAP": f"{best_neighbor}_COD_SUP",
                    }

        # 4. Tenta o Consenso Histórico Global (Ultimo recurso)
        historical_ref = self._consensus.get(cnpj, {}).get(cod_cta)
        if historical_ref:
            return {"COD_CTA_REF": historical_ref, "ORIGEM_MAP": "CONSENSO_HISTORICO"}

        return {"COD_CTA_REF": None, "ORIGEM_MAP": "SEM_MAPEAMENTO"}

    def get_summary(self) -> Dict[str, Any]:
        """Retorna estatísticas do aprendizado."""
        total_cnpjs = len(self._knowledge)
        total_ctas = sum(len(ctas) for ctas in self._knowledge.values())
        return {
            "cnpjs_processados": total_cnpjs,
            "contas_mapeadas_na_historia": total_ctas,
            "anos_com_estrutura_i050": sum(
                len(yrs) for yrs in self._account_structures.values()
            ),
        }

    def get_inferred_plan(
        self, cnpj: str, ano_alvo: Optional[str] = None
    ) -> Optional[str]:
        """
        Retorna o COD_PLAN_REF. Se ano_alvo for fornecido, tenta buscar
        o código do vizinho mais similar.
        """
        inferred = None
        if ano_alvo:
            best_neighbor = self.find_best_neighbor(cnpj, ano_alvo)
            if best_neighbor:
                inferred = self._plan_knowledge.get(cnpj, {}).get(best_neighbor)

        if not inferred:
            inferred = self._plan_consensus.get(cnpj)

        # --- LÓGICA DE EQUIVALÊNCIA HISTÓRICA (Regra 2014+) ---
        # Em 2011-2013, código '10' significava 'PJ em Geral'.
        # Em 2014+, código '1' passou a ser 'Lucro Real' e '10' 'Lucro Presumido'.
        # Se inferirmos '10' de um ano antigo para um ano moderno, e o alvo moderno
        # estiver apontando para '1' (videntificável no SPED), mantemos o '1'.
        # Aqui, apenas garantimos que '10' antigo não seja tratado como '10' moderno
        # sem critério, mas para fins de busca, eles são compatíveis.

        # Se extrairmos '10' de 2011-2013 e estivermos em 2015+,
        # e o sistema já detectou que o arquivo usa '1', o processor prioriza o '1'.
        # Esta função serve apenas como fallback.

        return inferred
