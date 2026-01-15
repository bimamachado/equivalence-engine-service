from __future__ import annotations
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from app.mapper.base import MappedNode, TaxonomyMapper
from app.mapper.clients import EmbeddingClient, LLMJsonClient
from app.mapper.taxonomy_index import TaxonomyEmbeddingIndex, top_k_concepts, build_taxonomy_text
from app.taxonomy.models import TaxonomyNode


@dataclass
class EmbeddingLLMMapperConfig:
    top_k: int = 30
    min_similarity: float = 0.30  # corte inicial
    use_llm_refine: bool = True
    max_evidence_per_node: int = 3


class EmbeddingLLMMapper(TaxonomyMapper):
    """
    Estratégia:
    1) Embedding da ementa
    2) Top-K nós da taxonomia por cosine
    3) Converter similaridade em (weight/confidence) base
    4) Opcional: pedir ao LLM para ajustar pesos e listar evidências (trechos)
    """
    model_version = "mapper-embed+llm-0.1"

    def __init__(
        self,
        embedder: EmbeddingClient,
        index: TaxonomyEmbeddingIndex,
        cfg: EmbeddingLLMMapperConfig,
        llm: Optional[LLMJsonClient] = None,
    ):
        self.embedder = embedder
        self.index = index
        self.cfg = cfg
        self.llm = llm

    def map(self, tenant_id: str, taxonomy_version: str, text: str) -> List[MappedNode]:
        if taxonomy_version != self.index.taxonomy_version:
            raise ValueError("Index não corresponde à taxonomy_version solicitada.")

        # 1) embedding da ementa
        qvec = self.embedder.embed([text])[0]

        # 2) top-k candidatos
        candidates = top_k_concepts(self.index, qvec, k=self.cfg.top_k)
        candidates = [(nid, sim) for nid, sim in candidates if sim >= self.cfg.min_similarity]
        if not candidates:
            return []

        # 3) score base -> weight/confidence
        base = []
        for nid, sim in candidates:
            # mapeamento simples: sim em [min_similarity..1] -> peso/conf
            # (não precisa ser perfeito, precisa ser estável)
            w = min(1.0, max(0.1, (sim - self.cfg.min_similarity) / (1.0 - self.cfg.min_similarity)))
            conf = min(1.0, max(0.4, sim))
            base.append(MappedNode(node_id=nid, weight=float(w), confidence=float(conf), evidence=[]))

        # 4) opcional: refinamento por LLM para evidência e ajuste fino
        if self.cfg.use_llm_refine and self.llm is not None:
            try:
                return self._refine_with_llm(text, base)
            except Exception:
                # Se LLM falhar, devolve base. O engine continua, sem drama.
                return base

        return base

    def _refine_with_llm(self, ementa: str, base: List[MappedNode]) -> List[MappedNode]:
        # Monta contexto compacto: só candidatos + descrições.
        nodes: Dict[int, TaxonomyNode] = self.index.nodes
        concepts_compact = []
        for m in base[: self.cfg.top_k]:
            n = nodes.get(m.node_id)
            if not n:
                continue
            concepts_compact.append({
                "node_id": m.node_id,
                "conceito": n.conceito,
                "descricao": n.descricao[:240],
                "nivel": n.nivel,
                "critico": n.critico,
                "keywords": n.palavras_chave[:10],
                "base_weight": m.weight,
                "base_confidence": m.confidence,
            })

        json_schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "mapped": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "node_id": {"type": "integer"},
                            "weight": {"type": "number"},
                            "confidence": {"type": "number"},
                            "evidence": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["node_id", "weight", "confidence", "evidence"]
                    }
                }
            },
            "required": ["mapped"]
        }

        system = (
            "Você é um avaliador técnico. "
            "Mapeie a ementa a conceitos da taxonomia. "
            "Não invente conceitos fora da lista. "
            "Use pesos (0..1), confiança (0..1) e evidências como trechos curtos da ementa."
        )

        user = (
            "EMENTA:\n"
            f"{ementa}\n\n"
            "CANDIDATOS (use apenas estes node_id):\n"
            f"{concepts_compact}\n\n"
            "Regras:\n"
            "- Retorne somente JSON no schema.\n"
            "- weight alto se o conceito é claramente coberto.\n"
            "- confidence alta se há evidência explícita.\n"
            "- evidence: no máximo 3 trechos curtos.\n"
        )

        out = self.llm.complete_json(system=system, user=user, json_schema=json_schema)

        mapped_out: List[MappedNode] = []
        allowed = {m.node_id for m in base}
        for item in out.get("mapped", []):
            nid = int(item["node_id"])
            if nid not in allowed:
                continue
            w = float(item["weight"])
            c = float(item["confidence"])
            ev = item.get("evidence", [])[: self.cfg.max_evidence_per_node]
            mapped_out.append(MappedNode(node_id=nid, weight=max(0.0, min(1.0, w)), confidence=max(0.0, min(1.0, c)), evidence=ev))

        mapped_out.sort(key=lambda x: (x.weight, x.confidence), reverse=True)
        return mapped_out[:60]
