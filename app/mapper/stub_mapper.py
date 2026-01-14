from __future__ import annotations
from typing import List, Dict
import re
import unicodedata
from .base import MappedNode, TaxonomyMapper
from app.taxonomy.store import TaxonomyStore


def _normalize_text(s: str) -> str:
    """Normaliza o texto: NFD, remove acentos, lowercase."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.lower()


class StubKeywordMapper(TaxonomyMapper):
    """
    MVP: matching por palavras-chave da taxonomia.
    Produção: substituir por embeddings/LLM.
    Melhorias: usa normalização e regex com fronteiras de palavra para reduzir falsos positivos.
    """
    model_version = "mapper-stub-keywords-0.1"

    def __init__(self, store: TaxonomyStore):
        self.store = store

    def map(self, tenant_id: str, taxonomy_version: str, text: str) -> List[MappedNode]:
        if not text:
            return []

        nodes = self.store.get_nodes(taxonomy_version)
        t_norm = _normalize_text(text)
        mapped: List[MappedNode] = []

        for node_id, node in nodes.items():
            hits = 0
            evid: List[str] = []
            for kw in node.palavras_chave:
                kw_norm = _normalize_text(kw)
                # usa regex com fronteiras de palavra para evitar substrings indesejadas
                try:
                    if re.search(rf"\b{re.escape(kw_norm)}\b", t_norm):
                        hits += 1
                        if len(evid) < 3:
                            evid.append(kw)
                except re.error:
                    # se keyword produzir regex inválida (muito raro), fallback para in
                    if kw_norm in t_norm:
                        hits += 1
                        if len(evid) < 3:
                            evid.append(kw)

            if hits > 0:
                # peso simples: saturação por hits
                weight = min(1.0, 0.3 + 0.2 * hits)
                conf = min(1.0, 0.6 + 0.1 * hits)
                mapped.append(MappedNode(node_id=node_id, weight=weight, confidence=conf, evidence=evid))

        # mantém top-N por peso
        mapped.sort(key=lambda x: (x.weight, x.confidence), reverse=True)
        return mapped[:60]
