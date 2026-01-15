from app.mapper.stub_mapper import StubKeywordMapper
from app.taxonomy.models import TaxonomyNode
from app.taxonomy.store import TaxonomyStore


def _build_store():
    store = TaxonomyStore()
    nodes = [
        TaxonomyNode(
            id=101,
            area="Admin",
            subarea="Gestao",
            conceito="Planejamento",
            descricao="descr",
            palavras_chave=["Administração", "planejamento"],
            nivel="intermediario",
            critico=False,
        ),
        TaxonomyNode(
            id=102,
            area="Arte",
            subarea="Artes",
            conceito="Artes",
            descricao="descr",
            palavras_chave=["arte", "pintura"],
            nivel="basico",
            critico=False,
        ),
        TaxonomyNode(
            id=103,
            area="Teste",
            subarea="Sub",
            conceito="Substring",
            descricao="descr",
            palavras_chave=["art"],
            nivel="basico",
            critico=False,
        ),
    ]
    store.load_version("v1", nodes)
    return store


def test_normalization_and_accent_match():
    store = _build_store()
    mapper = StubKeywordMapper(store)
    mapped = mapper.map("t", "v1", "conhecimentos em administracao e pintura")
    ids = {m.node_id for m in mapped}
    assert 101 in ids  # administração matched administracao
    assert 102 in ids  # pintura matched pintura


def test_word_boundary_prevents_substring():
    store = _build_store()
    mapper = StubKeywordMapper(store)
    mapped = mapper.map("t", "v1", "estudo em arte")
    ids = {m.node_id for m in mapped}
    assert 102 in ids
    assert 103 not in ids  # 'art' should not match inside 'arte'


def test_empty_text_returns_empty():
    store = _build_store()
    mapper = StubKeywordMapper(store)
    mapped = mapper.map("t", "v1", "")
    assert mapped == []
