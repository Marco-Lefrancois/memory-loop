"""
Tests MLOOP-182-BE — Backfill retroactif des EvidencePacks EPIC-10→17 vers la
parite Phase 2 (CA-1 a CA-6 : injection, zero-invention, idempotence, legacy
intouche, granularite hybride D, richness_penalty recalcule).
"""
import hashlib
import json

import pytest

from src.pipelines.evidence_backfill import EvidenceBackfillEngine

DOSSIER = """---
story_id: MLOOP-160-BE
dossier_status: CURRENT
---
# Dossier — MLOOP-160-BE

## 🔬 2. Faits Extraits & Verbatims (Passage-Level Grounding)

| # | Source (fichier:lignes) | Verbatim | Fait établi |
| :---: | :--- | :--- | :--- |
| **F-01** | `directives/tech.md:15` | « Le document maître consolidé fait foi absolue. » | Le maître consolidé prime. |
| **F-02** | `directives/tech.md:16` | « L'amont n'est plus autoritaire. » | L'amont est subordonné. |

## 🏁 5. Évaluation de la Frontière Active

* **Arbitrages retenus (session Grill)** :
  * D2 — Fichier autonome court, refus d'enfouissement.
* **Frontière (ce que le récit NE fait PAS)** : aucun contrôle automatique.
* **Admission of Limits** : numérotation ADR reconfirmée au build du récit 161.
"""

PLAN = """# Plan MLOOP-160-BE

## Décisions d'implémentation
- **Déc. 1** : Extraire le protocole dans un fichier autonome de 40 lignes.

## Contrats Déclaratifs Cibles
- POST /api/v1/directives — soumission des directives projet.
"""

STORY = """---
id: MLOOP-160-BE
status: DONE
---
# MLOOP-160-BE : Protocole SSOT

## Règles d'affaires
- **RM-001** : Le document maître consolidé docs/03-models/ fait foi absolue.
"""

PACK_EMPTY = {
    "story_id": "MLOOP-160-BE",
    "timestamp": "2026-09-01T00:00:00+00:00",
    "verbatim_extracts": [],
    "implementation_decisions": [],
    "declarative_contracts": [],
    "conflict_matrix": [],
    "epistemic_audit": {
        "what_it_actually_proves": ["ancien"],
        "what_it_does_not_prove": ["ancien"],
        "richness_penalty": {"richness": 0, "multiplier": 0.7, "score": 0.5,
                             "reason": "no_citations"},
    },
}


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def capture_mloop_logs(caplog):
    """
    Capture des logs du moteur mLoop : get_logger force propagate=False et un
    niveau WARNING — on attache manuellement le handler caplog (documenté pytest)
    et on abaisse le niveau le temps du test.
    """
    import logging

    mloop_logger = logging.getLogger("mloop.pipelines.evidence_backfill")
    old_level = mloop_logger.level
    mloop_logger.setLevel(logging.DEBUG)
    mloop_logger.addHandler(caplog.handler)
    try:
        yield caplog
    finally:
        mloop_logger.removeHandler(caplog.handler)
        mloop_logger.setLevel(old_level)


@pytest.fixture
def project(tmp_path):
    """Mini-projet : cible avec sources + legacy + sans-source + dossier corrompu."""
    root = tmp_path / "ProjBF"
    ev = root / "memory" / "evidence"
    plan_dir = root / "memory" / "plan"
    stories = root / "backlog" / "stories"
    ev.mkdir(parents=True)
    plan_dir.mkdir(parents=True)
    stories.mkdir(parents=True)

    def write_pack(sid, data=None):
        payload = dict(data if data is not None else PACK_EMPTY)
        payload.setdefault("story_id", sid)
        target = ev / f"{sid}_evidence.json"
        target.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        return target

    write_pack("MLOOP-160-BE")
    (ev / "MLOOP-160-BE_fact_dossier.md").write_text(DOSSIER, encoding="utf-8")
    (plan_dir / "implementation_plan_MLOOP-160-BE.md").write_text(PLAN, encoding="utf-8")
    (stories / "MLOOP-160-BE.md").write_text(STORY, encoding="utf-8")

    # Legacy EPIC 1 (CA-4) — doit rester bit-à-bit intact
    write_pack("MLOOP-010-BE", {"story_id": "MLOOP-010-BE", "verbatim_extracts": [],
                                "implementation_decisions": []})

    # Sans source (Pilier 2)
    write_pack("MLOOP-110-BE")

    # Dossier corrompu (YAML invalide) + pack sain voisin (poursuite)
    write_pack("MLOOP-122-BE")
    (ev / "MLOOP-122-BE_fact_dossier.md").write_text(
        "---\nstory_id: [unclosed\n---\n# Corrompu\n", encoding="utf-8"
    )
    write_pack("MLOOP-123-BE")
    (ev / "MLOOP-123-BE_fact_dossier.md").write_text(
        DOSSIER.replace("story_id: MLOOP-160-BE", "story_id: MLOOP-123-BE"),
        encoding="utf-8",
    )

    # Génération native (>=180) — hors périmètre
    write_pack("MLOOP-181-BE", {"story_id": "MLOOP-181-BE",
                                "implementation_decisions": [{"decision_id": "DEC-x"}],
                                "verbatim_extracts": []})
    return root


def test_backfill_nominal_packs_populated(project):
    """CA-1/CA-2/CA-5/CA-6 : décisions, citations ancrées, contrats, Admission, penalty."""
    engine = EvidenceBackfillEngine(project_path=project)
    report = engine.run()

    assert "MLOOP-160-BE" in report["processed"]
    pack = json.loads(
        (project / "memory" / "evidence" / "MLOOP-160-BE_evidence.json").read_text(
            encoding="utf-8"
        )
    )

    # CA-1 : décisions = arbitrage D2 + Déc.1 (plan) + RM-001 (règles d'affaires)
    decisions = pack["implementation_decisions"]
    assert len(decisions) == 3
    cats = {d["category"] for d in decisions}
    assert "pattern" in cats  # RM-001 mappe vers pattern (documenté)
    assert all(d["timestamp"] for d in decisions)

    # CA-5 : granularité hybride D = 1/fichier source + 1/décision
    citations = pack["verbatim_extracts"]
    assert len(citations) >= 4
    dossier_cites = [c for c in citations
                     if c["source_file"].endswith("MLOOP-160-BE_fact_dossier.md")]
    assert dossier_cites, "verbatim_extracts doit référencer le fact_dossier (Déc. 3)"
    for c in citations:
        start, end = c["lines"]
        assert 1 <= start <= end
        assert c["quote"].strip()

    # Contrat POST détecté (défini, zéro invention)
    methods = {(c["method"], c["status"]) for c in pack["declarative_contracts"]}
    assert ("POST", "defined") in methods

    # Admission of Limits → what_it_does_not_prove
    proves = " ".join(pack["epistemic_audit"]["what_it_does_not_prove"])
    assert "numérotation ADR reconfirmée" in proves

    # CA-6 : richness_penalty recalculé (Déc.5 : 0.7 + 0.3*min(1, r/10), r=8 → 0.94)
    pen = pack["epistemic_audit"]["richness_penalty"]
    assert pen["richness"] == 8
    assert pen["multiplier"] == pytest.approx(0.94)
    assert pen["reason"] == "partial_richness (8/10)"

    # Pilier 4 : timestamp UTC + catégories du rapport
    assert "T" in report["timestamp_utc"]
    assert report["legacy_skipped"] == ["MLOOP-010-BE"]


def test_backfill_idempotent_second_run_unchanged(project):
    """CA-3 : re-exécution = hash SHA-256 du pack inchangé (delta nul → zéro écriture)."""
    engine = EvidenceBackfillEngine(project_path=project)
    engine.run()
    pack_path = project / "memory" / "evidence" / "MLOOP-160-BE_evidence.json"
    first = _sha(pack_path)

    report2 = engine.run()
    assert _sha(pack_path) == first, "re-exécution doit laisser le pack bit-à-bit identique"
    assert "MLOOP-160-BE" in report2["processed"] or "MLOOP-160-BE" in report2["unchanged"]


def test_backfill_legacy_pack_never_written(project, capture_mloop_logs):
    """CA-4 + Pilier 2 : MLOOP-010-BE (EPIC 1) jamais ouvert en écriture, log legacy_skipped."""
    legacy_path = project / "memory" / "evidence" / "MLOOP-010-BE_evidence.json"
    before = _sha(legacy_path)

    report = EvidenceBackfillEngine(project_path=project).run()

    assert _sha(legacy_path) == before, "pack legacy modifié (CA-4 violée)"
    assert "MLOOP-010-BE" in report["legacy_skipped"]
    assert any("legacy_skipped" in r.message for r in capture_mloop_logs.records), (
        "log INFO 'legacy_skipped' manquant"
    )


def test_backfill_no_source_documented_and_stable(project):
    """Pilier 2 : source absente → NO_SOURCE_AVAILABLE, puis idempotence stricte."""
    engine = EvidenceBackfillEngine(project_path=project)
    engine.run()
    pack_path = project / "memory" / "evidence" / "MLOOP-110-BE_evidence.json"

    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    audit = " ".join(pack["epistemic_audit"]["what_it_does_not_prove"])
    assert "NO_SOURCE_AVAILABLE" in audit
    assert pack["implementation_decisions"] == []
    assert pack["verbatim_extracts"] == []
    assert "MLOOP-110-BE" in engine.last_report["no_source"]

    after_first = _sha(pack_path)
    engine.run()
    assert _sha(pack_path) == after_first, "hash modifié lors de la re-exécution sans source"


def test_backfill_corrupted_dossier_intact_target_and_continues(project, capture_mloop_logs):
    """Pilier 3 : dossier corrompu → pack cible intact, erreur loggée, autres packs traités."""
    bad_pack = project / "memory" / "evidence" / "MLOOP-122-BE_evidence.json"
    before = _sha(bad_pack)

    report = EvidenceBackfillEngine(project_path=project).run()

    assert _sha(bad_pack) == before, "pack cible modifié malgré source corrompue"
    assert any("MLOOP-122-BE" in e.get("story_id", "") for e in report["errors"])
    assert any(
        r.exc_info for r in capture_mloop_logs.records
    ), "erreur non loggée avec exc_info (ADR-0369)"
    assert "MLOOP-123-BE" in report["processed"], "poursuite sur les autres packs requise"


def test_backfill_dry_run_writes_nothing(project):
    """Mode --dry-run : rapport complet, zéro écriture sur les packs."""
    engine = EvidenceBackfillEngine(project_path=project)
    pack_path = project / "memory" / "evidence" / "MLOOP-160-BE_evidence.json"
    before = _sha(pack_path)

    report = engine.run(dry_run=True)
    assert _sha(pack_path) == before
    assert "MLOOP-160-BE" in report["processed"]
    assert not (project / "memory" / "evidence" / "backfill_report.json").exists()


def test_backfill_report_written_with_pillar4_fields(project):
    """Pilier 4 : rapport persisté — traités, legacy, sans source, delta, timestamp UTC."""
    EvidenceBackfillEngine(project_path=project).run()
    report_path = project / "memory" / "evidence" / "backfill_report.json"
    assert report_path.exists()
    data = json.loads(report_path.read_text(encoding="utf-8"))
    for key in ("timestamp_utc", "processed", "legacy_skipped", "no_source",
                "errors", "avg_delta_citations"):
        assert key in data, f"clé Pilier 4 manquante : {key}"
    assert data["avg_delta_citations"] >= 0.0
    assert "T" in data["timestamp_utc"]
