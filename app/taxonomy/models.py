from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Literal

Level = Literal["basico", "intermediario", "avancado"]

@dataclass(frozen=True)
class TaxonomyNode:
    id: int
    area: str
    subarea: str
    conceito: str
    descricao: str
    palavras_chave: List[str]
    nivel: Level
    critico: bool
