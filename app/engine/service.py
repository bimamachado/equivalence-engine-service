from __future__ import annotations
from typing import Optional
from app.api.schemas import EvaluateRequest, EvaluateResponse, EvidenceBlock, ConceptEvidence, TimingsMs, ScoreBreakdown
from app.engine.hard_rules import apply_hard_rules, hard_rules_block_decision
from app.engine.scoring import build_vector, coverage, critical_coverage, level_penalty, final_score
from app.engine.decision import decide
from app.engine.justification import build_justification
from app.engine.utils import sha256_text, timer_ms
from app.taxonomy.store import TaxonomyStore
from app.mapper.base import TaxonomyMapper
from app.cache.cache import SimpleTTLCache
from app.audit.repository import AuditRepository

class EquivalenceEngine:
    def __init__(
        self,
        taxonomy_store: TaxonomyStore,
        mapper: TaxonomyMapper,
        fallback_mapper: Optional[TaxonomyMapper],
        cache: SimpleTTLCache,
        audit_repo: AuditRepository,
    ):
        self.taxonomy_store = taxonomy_store
        self.mapper = mapper
        self.fallback_mapper = fallback_mapper
        self.cache = cache
        self.audit = audit_repo

    def evaluate(self, req: EvaluateRequest, tenant_id: str) -> EvaluateResponse:
        timings = TimingsMs()

        with timer_ms() as t_total:
            # 1) validação básica (Pydantic já fez, mas aqui você poderia impor regras extra)
            with timer_ms() as t:
                nodes = self.taxonomy_store.get_nodes(req.taxonomy_version)
            timings.validate = t()

            # 2) hard rules
            with timer_ms() as t:
                hard = apply_hard_rules(req.origem, req.destino, req.policy)
                blocked = hard_rules_block_decision(hard)
            timings.hard_rules = t()

            if blocked:
                # indeferimento determinístico, sem IA
                score = 0
                breakdown = ScoreBreakdown(cobertura=0.0, cobertura_critica=0.0, penalidade_nivel=0.0)
                decisao = "INDEFERIDO"
                motivo = "Falha em regra  (aprovação/carga/validade/entrada)."
                curta, detalhada = build_justification(
                    decisao, motivo, score,
                    breakdown=breakdown,
                    faltantes=[], criticos_faltantes=[],
                    carga_origem=req.origem.carga_horaria,
                    carga_destino=req.destino.carga_horaria
                )
                timings.total = t_total()
                return EvaluateResponse(
                    request_id=req.request_id,
                    decisao=decisao,
                    score=score,
                    breakdown=breakdown,  # Pydantic aceita dict compatível
                    hard_rules=hard,
                    faltantes=[],
                    criticos_faltantes=[],
                    justificativa_curta=curta,
                    justificativa_detalhada=detalhada,
                    evidence=None,
                    degraded_mode=False,
                    model_version=self.mapper.model_version,
                    policy_version=req.policy_version,
                    taxonomy_version=req.taxonomy_version,
                    timings_ms=timings,
                    meta={"blocked_by_hard_rules": True},
                )

            # 3) mapeamento (cacheado)
            degraded = False
            with timer_ms() as t:
                key_o = sha256_text(tenant_id, req.taxonomy_version, "origem", req.origem.ementa)
                key_d = sha256_text(tenant_id, req.taxonomy_version, "destino", req.destino.ementa)

                mapped_o = self.cache.get(key_o)
                mapped_d = self.cache.get(key_d)

                if mapped_o is None:
                    mapped_o = self.mapper.map(tenant_id, req.taxonomy_version, req.origem.ementa)
                    self.cache.set(key_o, mapped_o)

                if mapped_d is None:
                    mapped_d = self.mapper.map(tenant_id, req.taxonomy_version, req.destino.ementa)
                    self.cache.set(key_d, mapped_d)

                # se mapper não retornou nada útil, tenta fallback (se permitido)
                if req.options.allow_degraded_fallback and (not mapped_o or not mapped_d):
                    degraded = True
                    if self.fallback_mapper is not None:
                        mapped_o = self.fallback_mapper.map(tenant_id, req.taxonomy_version, req.origem.ementa)
                        mapped_d = self.fallback_mapper.map(tenant_id, req.taxonomy_version, req.destino.ementa)
            timings.map = t()

            # 4) scoring
            with timer_ms() as t:
                vec_o = build_vector(mapped_o, req.policy.confidence_cutoff)
                vec_d = build_vector(mapped_d, req.policy.confidence_cutoff)

                cov, missing = coverage(vec_o, vec_d)
                cov_crit, missing_crit = critical_coverage(vec_o, vec_d, nodes)
                pen = level_penalty(vec_o, vec_d, nodes)

                score, breakdown = final_score(req.policy, cov, cov_crit, pen)
            timings.score = t()

            # 5) decisão
            with timer_ms() as t:
                decisao, motivo = decide(req.policy, score, cov_crit, degraded_mode=degraded)
            timings.decide = t()

            # 6) justificativa
            with timer_ms() as t:
                curta, detalhada = build_justification(
                    decisao, motivo, score, breakdown, missing, missing_crit,
                    carga_origem=req.origem.carga_horaria,
                    carga_destino=req.destino.carga_horaria
                )
            timings.justify = t()

            # 7) evidências (opcional)
            evidence = None
            if req.options.return_evidence:
                covered = [
                    ConceptEvidence(node_id=m.node_id, weight=float(m.weight), confidence=float(m.confidence), evidence=m.evidence)
                    for m in mapped_o
                    if m.node_id in vec_d and m.confidence >= req.policy.confidence_cutoff
                ]
                evidence = EvidenceBlock(
                    covered_concepts=covered[:50],
                    missing_concepts=missing[:200],
                    missing_critical_concepts=missing_crit[:200],
                )

            timings.total = t_total()

            # 8) audit (MVP: no-op)
            self.audit.save({
                "request_id": req.request_id,
                "tenant_id": tenant_id,
                "policy_version": req.policy_version,
                "taxonomy_version": req.taxonomy_version,
                "model_version": (self.fallback_mapper.model_version if degraded and self.fallback_mapper else self.mapper.model_version),
                "degraded_mode": degraded,
                "score": score,
                "decision": decisao,
                "timings_ms": timings.model_dump(),
                "hash_origem": sha256_text(req.origem.ementa),
                "hash_destino": sha256_text(req.destino.ementa),
            })

            return EvaluateResponse(
                request_id=req.request_id,
                decisao=decisao,
                score=score,
                breakdown=breakdown,
                hard_rules=hard,
                faltantes=missing,
                criticos_faltantes=missing_crit,
                justificativa_curta=curta,
                justificativa_detalhada=detalhada,
                evidence=evidence,
                degraded_mode=degraded,
                model_version=(self.fallback_mapper.model_version if degraded and self.fallback_mapper else self.mapper.model_version),
                policy_version=req.policy_version,
                taxonomy_version=req.taxonomy_version,
                timings_ms=timings,
                meta={
                    "origin_vec_size": len(vec_o),
                    "dest_vec_size": len(vec_d),
                    "mapper_used": "fallback" if degraded else "primary"
                }
            )
