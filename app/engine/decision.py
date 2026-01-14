from __future__ import annotations
from typing import Tuple
from app.api.schemas import PolicyInput, DecisionType

def decide(policy: PolicyInput, score: int, cov_crit: float, degraded_mode: bool) -> Tuple[DecisionType, str]:
    if degraded_mode:
        # conservador: não “aprova” sem IA
        return "ANALISE_HUMANA", "Modo degradado: serviço de IA indisponível ou sem mapeamento confiável."

    if policy.exigir_criticos and cov_crit < 1.0:
        return "INDEFERIDO", "Conceitos críticos do destino não foram totalmente contemplados."

    if score >= policy.min_score_deferir:
        return "DEFERIDO", "Score e critérios atendidos para deferimento automático."

    if score >= policy.min_score_complemento:
        return "COMPLEMENTO", "Similaridade suficiente, mas recomenda-se complemento para fechar lacunas."

    return "INDEFERIDO", "Score insuficiente para equivalência."
