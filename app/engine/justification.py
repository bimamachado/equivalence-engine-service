from __future__ import annotations
from typing import List, Tuple
from app.api.schemas import DecisionType, ScoreBreakdown

def build_justification(
    decisao: DecisionType,
    motivo: str,
    score: int,
    breakdown: ScoreBreakdown,
    faltantes: List[int],
    criticos_faltantes: List[int],
    carga_origem: int,
    carga_destino: int
) -> Tuple[str, str]:
    curta = f"{decisao}: {motivo}"

    detalhes = [
        f"Decisão: {decisao}",
        f"Motivo: {motivo}",
        f"Score final: {score}/100",
        f"Cobertura: {breakdown.cobertura:.2f}",
        f"Cobertura crítica: {breakdown.cobertura_critica:.2f}",
        f"Penalidade de nível: {breakdown.penalidade_nivel:.2f}",
        f"Carga horária: origem={carga_origem}h, destino={carga_destino}h",
    ]
    if criticos_faltantes:
        detalhes.append(f"Conceitos críticos faltantes (ids): {criticos_faltantes}")
    if faltantes and len(faltantes) <= 30:
        detalhes.append(f"Conceitos faltantes (ids): {faltantes}")
    elif faltantes:
        detalhes.append(f"Conceitos faltantes (ids): {faltantes[:30]} ... (+{len(faltantes)-30})")

    return curta, "\n".join(detalhes)
