"""
Tests MLOOP-181-BE — Préservation des captures du harnais Phase 3 lors de la
régénération de l'EvidencePack (CA-1/CA-2 : les décisions, citations et le
sceau tdd_cycle doivent survivre à chaque `sync` / `extract_evidence`).
"""
import json

from src.pipelines.evidence_pack import EvidencePackEngine
from src.pipelines.pack_preserver import (
    PRESERVED_LIST_FIELDS,
    load_preserved_fields,
)


def _make_project(tmp_path):
    project_dir = tmp_path / "ProjPres"
    stories = project_dir / "backlog" / "stories"
    stories.mkdir(parents=True)
    story_file = stories / "US-PRES.md"
    story_file.write_text(
        "---\nid: US-PRES-TEST\nstatus: IN_QA\n---\n# US-PRES : Story de préservation\n\nCorps.\n",
        encoding="utf-8",
    )
    return project_dir, story_file


def _existing_pack(project_dir, story_id="US-PRES-TEST"):
    ev_dir = project_dir / "memory" / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)
    existing = {
        "story_id": story_id,
        "verbatim_extracts": [
            {"source_file": "src/x.py", "lines": [1, 2], "quote": "x = 1",
             "established_fact": "fait"}
        ],
        "implementation_decisions": [
            {"decision_id": "DEC-abc123", "category": "testing",
             "rationale": "cycle scellé", "alternatives_considered": [], "timestamp": "t"}
        ],
        "declarative_contracts": [],
        "conflict_matrix": [],
        "tdd_cycle": {
            "red": {"story_id": story_id, "exit_code": 1},
            "green": {"story_id": story_id, "exit_code": 0},
        },
    }
    (ev_dir / f"{story_id}_evidence.json").write_text(
        json.dumps(existing), encoding="utf-8"
    )
    return existing


def test_extract_evidence_preserves_captured_fields(tmp_path):
    """CA-1/CA-2 : extract_evidence ne doit PAS écraser les captures du harnais."""
    project_dir, story_file = _make_project(tmp_path)
    _existing_pack(project_dir)

    engine = EvidencePackEngine(project_dir)
    pack = engine.extract_evidence(story_file)

    assert pack["implementation_decisions"], (
        "implementation_decisions écrasées par extract_evidence (CA-1/CA-2 violés)"
    )
    assert pack["verbatim_extracts"], "verbatim_extracts écrasées (CA-4 violé)"
    assert pack.get("tdd_cycle"), "tdd_cycle écrasé — sceau Red/Green perdu (Gate 3 violée)"


def test_load_preserved_fields_defaults_when_absent(tmp_path):
    """Pack absent -> structures vides (rétrocompat MLOOP-180-BE CA-5)."""
    preserved = load_preserved_fields(tmp_path / "UNKNOWN_evidence.json")
    for field in PRESERVED_LIST_FIELDS:
        assert preserved[field] == []
    assert preserved["tdd_cycle"] is None


def test_load_preserved_fields_ignores_corrupted_pack(tmp_path):
    """Pack corrompu -> préservation neutralisée, zéro crash (résilience)."""
    bad = tmp_path / "BAD_evidence.json"
    bad.write_text("{not-json", encoding="utf-8")
    preserved = load_preserved_fields(bad)
    for field in PRESERVED_LIST_FIELDS:
        assert preserved[field] == []
