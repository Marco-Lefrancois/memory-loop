import json
from pathlib import Path
import pytest
from src.loop_mem.hybrid_search import TriStreamHybridSearch


@pytest.fixture(autouse=True)
def _stub_embeddings(monkeypatch):
    """Isole les tests du serveur Ollama réel (déterminisme + rapidité).

    Le flux vectoriel dense (MLOOP-102-BE) appelle un modèle d'embedding local via
    réseau. En test unitaire, on substitue un embedding lexical déterministe (sac de
    mots projeté sur un vecteur fixe) afin de valider la logique de fusion et de
    dépriorisation sans dépendance externe ni latence réseau.
    """
    import src.loop_mem.hybrid_search as hs

    def _fake_embed(text: str, *args, **kwargs):
        tokens = [t for t in text.lower().replace("\n", " ").split() if t]
        if not tokens:
            return []
        vec = [0.0] * 32
        for tok in tokens:
            vec[hash(tok) % 32] += 1.0
        return vec

    monkeypatch.setattr(hs, "get_embedding", _fake_embed)
    yield


def test_hybrid_search_nominal(tmp_path: Path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "adr_persistance.md").write_text(
        "# Persistance et SQLite\nArchitecture de base SQLite et FTS5.", encoding="utf-8"
    )

    mem_dir = tmp_path / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    graph_data = {"nodes": [{"id": "sqlite_node", "name": "SQLite"}]}
    (mem_dir / "knowledge_graph.json").write_text(json.dumps(graph_data), encoding="utf-8")

    engine = TriStreamHybridSearch(tmp_path)
    res = engine.search("SQLite", top_k=5)

    assert res["total"] >= 1
    assert res["latency_ms"] < 200.0
    titles = [r["title"].lower() for r in res["results"]]
    assert any("persistance" in t or "sqlite" in t for t in titles)
    assert res["results"][0]["confidence"] > 0.0


def test_hybrid_search_deprioritize_superseded(tmp_path: Path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Document obsolète / supplanté
    (docs_dir / "old_rule.md").write_text(
        "# Règle Ancienne\nCette règle est superseded par la nouvelle règle de sécurité.",
        encoding="utf-8",
    )
    # Document actif
    (docs_dir / "new_rule.md").write_text(
        "# Règle Active\nCette règle de sécurité est active et obligatoire.", encoding="utf-8"
    )

    engine = TriStreamHybridSearch(tmp_path)
    res = engine.search("règle sécurité", top_k=5)

    assert len(res["results"]) == 2
    # Le premier résultat doit être le document actif non-supplanté
    assert res["results"][0]["is_superseded"] is False
    assert res["results"][1]["is_superseded"] is True
    assert res["results"][0]["confidence"] > res["results"][1]["confidence"]


def test_hybrid_search_empty_query(tmp_path: Path):
    engine = TriStreamHybridSearch(tmp_path)
    res = engine.search("")
    assert res["results"] == []
    assert res["total"] == 0
