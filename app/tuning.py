import itertools
from sqlalchemy.orm import Session
from sqlalchemy import select
from app import models
import uuid
import math

def tune_for_course(db: Session, tenant_id: str, course_id: str):
    # pega resultados + labels
    rows = db.execute(
        select(models.EquivalenceResult, models.Label).join(models.Label, models.Label.result_id == models.EquivalenceResult.id)
        .where(models.EquivalenceResult.tenant_id == tenant_id, models.EquivalenceResult.course_id == course_id)
    ).all()

    data = []
    for r, lab in rows:
        data.append((r.score, lab.label))

    if len(data) < 50:
        raise RuntimeError("Poucos dados rotulados. Comece com >= 50 (ideal >= 200).")

    # grid thresholds
    defer_grid = range(75, 96, 1)
    comp_grid = range(55, 86, 1)

    def eval_policy(t_defer, t_comp):
        # simples: se score>=defer => DEFERIDO
        # elif score>=comp => COMPLEMENTO
        # else INDEFERIDO
        # Medida: acurácia (pode trocar por F1 por classe)
        correct = 0
        for score, y in data:
            yhat = "INDEFERIDO"
            if score >= t_defer:
                yhat = "DEFERIDO"
            elif score >= t_comp:
                yhat = "ANALISE_HUMANA"
            if yhat == y:
                correct += 1
        return correct / len(data)

    best = (-1, None, None)
    for t_defer, t_comp in itertools.product(defer_grid, comp_grid):
        if t_comp >= t_defer:
            continue
        acc = eval_policy(t_defer, t_comp)
        if acc > best[0]:
            best = (acc, t_defer, t_comp)

    acc, t_defer, t_comp = best
    return {"accuracy": acc, "min_score_deferir": t_defer, "min_score_complemento": t_comp}

def create_policy_version(db: Session, tenant_id: str, base_version: str, new_version: str, config: dict):
    pid = str(uuid.uuid4())
    pv = models.PolicyVersion(id=pid, tenant_id=tenant_id, version=new_version, config=config)
    db.add(pv)
    db.commit()
    return pv
