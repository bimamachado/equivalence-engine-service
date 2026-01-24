from app.engine.decision import decide


class Policy:
    def __init__(self, exigir_criticos: bool, min_score_deferir: int, min_score_complemento: int):
        self.exigir_criticos = exigir_criticos
        self.min_score_deferir = min_score_deferir
        self.min_score_complemento = min_score_complemento


def test_decide_degraded_mode():
    p = Policy(exigir_criticos=False, min_score_deferir=50, min_score_complemento=30)
    decision, reason = decide(p, score=100, cov_crit=1.0, degraded_mode=True)
    assert decision == "ANALISE_HUMANA"
    assert "Modo degradado" in reason


def test_decide_missing_critical_coverage():
    p = Policy(exigir_criticos=True, min_score_deferir=50, min_score_complemento=30)
    decision, _ = decide(p, score=100, cov_crit=0.5, degraded_mode=False)
    assert decision == "INDEFERIDO"


def test_decide_deferido_by_score():
    p = Policy(exigir_criticos=False, min_score_deferir=80, min_score_complemento=60)
    decision, _ = decide(p, score=85, cov_crit=1.0, degraded_mode=False)
    assert decision == "DEFERIDO"


def test_decide_complemento_by_score():
    p = Policy(exigir_criticos=False, min_score_deferir=90, min_score_complemento=70)
    decision, _ = decide(p, score=75, cov_crit=1.0, degraded_mode=False)
    assert decision == "ANALISE_HUMANA"


def test_decide_indeferido_low_score():
    p = Policy(exigir_criticos=False, min_score_deferir=80, min_score_complemento=60)
    decision, _ = decide(p, score=50, cov_crit=1.0, degraded_mode=False)
    assert decision == "INDEFERIDO"
