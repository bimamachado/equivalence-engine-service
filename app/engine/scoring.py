from __future__ import annotations
from typing import Dict, List, Tuple
from app.mapper.base import MappedNode
from app.taxonomy.models import TaxonomyNode
from app.api.schemas import ScoreBreakdown, PolicyInput

def build_vector(mapped: List[MappedNode], confidence_cutoff: float) -> Dict[int, float]:
    vec: Dict[int, float] = {}
    for m in mapped:
        if m.confidence < confidence_cutoff:
            continue
        vec[m.node_id] = max(vec.get(m.node_id, 0.0), float(m.weight))
    return vec

def coverage(origin_vec: Dict[int, float], dest_vec: Dict[int, float]) -> Tuple[float, List[int]]:
    """
    Cobertura = soma dos pesos do destino que foram cobertos pela origem / soma dos pesos do destino
    Dest pesa por weight do mapper.
    """
    if not dest_vec:
        return 0.0, list(dest_vec.keys())

    total = sum(dest_vec.values())
    if total <= 0:
        return 0.0, list(dest_vec.keys())

    covered_sum = 0.0
    missing: List[int] = []
    for nid, w_dest in dest_vec.items():
        w_org = origin_vec.get(nid, 0.0)
        if w_org > 0:
            covered_sum += w_dest
        else:
            missing.append(nid)

    return min(1.0, covered_sum / total), missing

def critical_coverage(origin_vec: Dict[int, float], dest_vec: Dict[int, float], nodes: Dict[int, TaxonomyNode]) -> Tuple[float, List[int]]:
    critical_ids = [nid for nid in dest_vec.keys() if nodes.get(nid) and nodes[nid].critico]
    if not critical_ids:
        return 1.0, []  # sem críticos no destino
    missing_crit = [nid for nid in critical_ids if origin_vec.get(nid, 0.0) <= 0]
    cov = 1.0 - (len(missing_crit) / len(critical_ids))
    return max(0.0, min(1.0, cov)), missing_crit

def level_penalty(origin_vec: Dict[int, float], dest_vec: Dict[int, float], nodes: Dict[int, TaxonomyNode]) -> float:
    """
    MVP simples: se destino tem muitos conceitos avançados e origem não cobre nenhum, penaliza.
    Produção: comparar níveis por conceito.
    """
    dest_adv = [nid for nid in dest_vec.keys() if nodes.get(nid) and nodes[nid].nivel == "avancado"]
    if not dest_adv:
        return 0.0
    covered_adv = sum(1 for nid in dest_adv if origin_vec.get(nid, 0.0) > 0)
    ratio = covered_adv / len(dest_adv)
    return float(max(0.0, 1.0 - ratio))  # 1.0 se cobre zero, 0.0 se cobre tudo

def final_score(policy: PolicyInput, cov: float, cov_crit: float, pen_level: float) -> Tuple[int, ScoreBreakdown]:
    w = policy.weights
    raw = (w.cobertura * cov) + (w.critica * cov_crit) - (w.nivel * pen_level)
    raw = max(0.0, min(1.0, raw))
    score = int(round(raw * 100))
    return score, ScoreBreakdown(cobertura=cov, cobertura_critica=cov_crit, penalidade_nivel=pen_level)
