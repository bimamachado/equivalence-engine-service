from __future__ import annotations
from typing import List
import math
from app.api.schemas import HardRuleResult, PolicyInput, DisciplineInput

def apply_hard_rules(origem: DisciplineInput, destino: DisciplineInput, policy: PolicyInput) -> List[HardRuleResult]:
    results: List[HardRuleResult] = []

    # input mínimo
    if not origem.ementa or not destino.ementa:
        results.append(HardRuleResult(rule="input_minimo", ok=False, details="Ementa ausente"))
        return results
    results.append(HardRuleResult(rule="input_minimo", ok=True))

    # aprovação
    if origem.aprovado is False:
        results.append(HardRuleResult(rule="aprovacao", ok=False, details="Disciplina de origem não aprovada"))
    else:
        results.append(HardRuleResult(rule="aprovacao", ok=True))

    # carga horária
    min_required = int(math.ceil(destino.carga_horaria * policy.tolerancia_carga))
    if origem.carga_horaria < min_required:
        results.append(HardRuleResult(
            rule="carga_horaria",
            ok=False,
            details=f"Carga insuficiente: origem={origem.carga_horaria}h < mínimo={min_required}h (tol={policy.tolerancia_carga})"
        ))
    else:
        results.append(HardRuleResult(rule="carga_horaria", ok=True))

    # validade temporal (opcional)
    if policy.max_anos_validade is not None and origem.ano_conclusao is not None:
        from datetime import datetime
        age = datetime.now().year - origem.ano_conclusao
        if age > policy.max_anos_validade:
            results.append(HardRuleResult(
                rule="validade_temporal",
                ok=False,
                details=f"Disciplina antiga: {age} anos (máx={policy.max_anos_validade})"
            ))
        else:
            results.append(HardRuleResult(rule="validade_temporal", ok=True))
    else:
        results.append(HardRuleResult(rule="validade_temporal", ok=True, details="Não aplicável"))

    # nível (se você quiser endurecer depois; MVP só registra)
    results.append(HardRuleResult(rule="nivel", ok=True, details="Não aplicável no MVP"))

    return results

def hard_rules_block_decision(hard_rules: List[HardRuleResult]) -> bool:
    # se qualquer hard rule essencial falhar, bloqueia
    essential = {"input_minimo", "aprovacao", "carga_horaria", "validade_temporal"}
    for r in hard_rules:
        if r.rule in essential and not r.ok:
            return True
    return False
