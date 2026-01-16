from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, conint, confloat

DecisionType = Literal["DEFERIDO", "INDEFERIDO", "COMPLEMENTO", "ANALISE_HUMANA"]
RuleName = Literal["aprovacao", "carga_horaria", "nivel", "validade_temporal", "input_minimo"]

class DisciplineInput(BaseModel):
    nome: str = Field(..., min_length=1, max_length=200)
    carga_horaria: conint(gt=0, le=2000)
    ementa: str = Field(..., min_length=10, max_length=20000)
    aprovado: Optional[bool] = None  # origem geralmente tem; destino não precisa
    nivel: Optional[Literal["basico", "intermediario", "avancado"]] = None
    ano_conclusao: Optional[conint(ge=1950, le=2100)] = None
    disciplina_id: Optional[int] = None  # útil no destino

class Weights(BaseModel):
    cobertura: confloat(ge=0, le=1) = 0.6
    critica: confloat(ge=0, le=1) = 0.4
    nivel: confloat(ge=0, le=1) = 0.1  # penalidade (subtrai)

class PolicyInput(BaseModel):
    min_score_deferir: conint(ge=0, le=100) = 85
    min_score_complemento: conint(ge=0, le=100) = 70
    tolerancia_carga: confloat(gt=0, le=1) = 1.0  # 1.0 = exige igual/maior; 0.8 = aceita 80%
    exigir_criticos: bool = True
    max_anos_validade: Optional[conint(ge=1, le=50)] = None  # se quiser recusar disciplinas antigas
    weights: Weights = Weights()
    confidence_cutoff: confloat(ge=0, le=1) = 0.5  # corta conceitos com confiança baixa

class EvaluateOptions(BaseModel):
    return_evidence: bool = True
    allow_degraded_fallback: bool = True

class EvaluateRequest(BaseModel):
    request_id: str = Field(..., min_length=8, max_length=80)
    origem: DisciplineInput
    destino: DisciplineInput
    policy: PolicyInput = PolicyInput()
    taxonomy_version: str = Field(..., min_length=3, max_length=30)
    policy_version: str = Field(..., min_length=1, max_length=30)
    options: EvaluateOptions = EvaluateOptions()
    course_id: Optional[str] = None
    request_id: Optional[str] = None


class HardRuleResult(BaseModel):
    rule: RuleName
    ok: bool
    details: Optional[str] = None

class ScoreBreakdown(BaseModel):
    cobertura: confloat(ge=0, le=1)
    cobertura_critica: confloat(ge=0, le=1)
    penalidade_nivel: confloat(ge=0, le=1)

class ConceptEvidence(BaseModel):
    node_id: int
    weight: confloat(ge=0, le=1)
    confidence: confloat(ge=0, le=1) = 1.0
    evidence: List[str] = Field(default_factory=list)

class EvidenceBlock(BaseModel):
    covered_concepts: List[ConceptEvidence] = Field(default_factory=list)
    missing_concepts: List[int] = Field(default_factory=list)
    missing_critical_concepts: List[int] = Field(default_factory=list)

class TimingsMs(BaseModel):
    validation: int = 0
    hard_rules: int = 0
    map: int = 0
    score: int = 0
    decide: int = 0
    justify: int = 0
    total: int = 0

class EvaluateResponse(BaseModel):
    request_id: str
    decisao: DecisionType
    score: conint(ge=0, le=100)
    breakdown: ScoreBreakdown
    hard_rules: List[HardRuleResult]
    faltantes: List[int]
    criticos_faltantes: List[int]
    justificativa_curta: str
    justificativa_detalhada: str
    evidence: Optional[EvidenceBlock] = None
    degraded_mode: bool = False
    model_version: str = "mapper-stub"
    policy_version: str
    taxonomy_version: str
    timings_ms: TimingsMs
    meta: Dict[str, Any] = Field(default_factory=dict)
