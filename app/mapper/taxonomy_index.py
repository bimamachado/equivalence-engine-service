from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple
import math

from app.taxonomy.models import TaxonomyNode
from app.mapper.clients import EmbeddingClient


def cosine(a: List[float], b: List[float]) -> float:
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


@dataclass
class TaxonomyEmbeddingIndex:
    taxonomy_version: str
    # node_id -> vector
    vectors: Dict[int, List[float]]
    # node_id -> node
    nodes: Dict[int, TaxonomyNode]


def build_taxonomy_text(node: TaxonomyNode) -> str:
    kws = ", ".join(node.palavras_chave[:12])
    return f"{node.area} / {node.subarea} | {node.conceito}. {node.descricao}. Palavras-chave: {kws}."


def build_index(
    taxonomy_version: str,
    nodes: Dict[int, TaxonomyNode],
    embedder: EmbeddingClient,
) -> TaxonomyEmbeddingIndex:
    # cria textos por nó
    items: List[Tuple[int, str]] = [(nid, build_taxonomy_text(n)) for nid, n in nodes.items()]
    texts = [t for _, t in items]
    vecs = embedder.embed(texts)

    vectors = {items[i][0]: vecs[i] for i in range(len(items))}
    return TaxonomyEmbeddingIndex(taxonomy_version=taxonomy_version, vectors=vectors, nodes=nodes)


def top_k_concepts(
    index: TaxonomyEmbeddingIndex,
    query_vec: List[float],
    k: int = 30,
) -> List[Tuple[int, float]]:
    scored = []
    for nid, v in index.vectors.items():
        s = cosine(query_vec, v)
        scored.append((nid, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]
