from __future__ import annotations
from typing import Dict, List
from .models import TaxonomyNode

class TaxonomyStore:
    """
    MVP: store em memória.
    Produção: carregar do DB por tenant + taxonomy_version, com cache.
    """

    def __init__(self):
        self._by_version: Dict[str, Dict[int, TaxonomyNode]] = {}

    def load_version(self, taxonomy_version: str, nodes: List[TaxonomyNode]) -> None:
        self._by_version[taxonomy_version] = {n.id: n for n in nodes}

    def get_nodes(self, taxonomy_version: str) -> Dict[int, TaxonomyNode]:
        if taxonomy_version not in self._by_version:
            raise ValueError(f"Taxonomia não carregada para version={taxonomy_version}")
        return self._by_version[taxonomy_version]

    def critical_ids(self, taxonomy_version: str) -> List[int]:
        nodes = self.get_nodes(taxonomy_version)
        return [nid for nid, n in nodes.items() if n.critico]
