from __future__ import annotations
from typing import List
from .base import MappedNode, TaxonomyMapper

class EmptyFallbackMapper(TaxonomyMapper):
    model_version = "mapper-fallback-empty-0.1"

    def map(self, tenant_id: str, taxonomy_version: str, text: str) -> List[MappedNode]:
        # Devolve nada. Engine decide ANALISE_HUMANA ou indeferimento conservador.
        return []
