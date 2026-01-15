from __future__ import annotations
from dataclasses import dataclass
from typing import List, Protocol

@dataclass
class MappedNode:
    node_id: int
    weight: float        # 0..1
    confidence: float    # 0..1
    evidence: List[str]

class TaxonomyMapper(Protocol):
    model_version: str
    def map(self, tenant_id: str, taxonomy_version: str, text: str) -> List[MappedNode]:
        ...
