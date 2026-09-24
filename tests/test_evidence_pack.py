import json
import pytest
from pathlib import Path
from src.pipelines.evidence_pack import EvidencePackEngine


def test_evidence_pack_extraction(tmp_path):
    project_dir = tmp_path / "TestProject"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    story_file = stories_dir / "US-01.md"
    story_file.write_text(
        """---
id: US-01-TEST
status: IN_ANALYZE
---
# US-01 : Test Story

> [!NOTE]
> Trace Note

> [!CAUTION]
> Caution Alert

> [!WARNING]
> Warning Alert

- **Ref**: Q-001, QD-002
- **Source**: scan_test.md
""",
        encoding="utf-8",
    )

    # Création d'une source physique factice pour valider le calcul SHA-256
    ingested_dir = project_dir / "docs" / "00-ingested"
    ingested_dir.mkdir(parents=True)
    (ingested_dir / "scan_test.md").write_text(
        "Données source de référence fact-search", encoding="utf-8"
    )

    engine = EvidencePackEngine(project_dir)
    evidence = engine.extract_evidence(story_file)

    assert evidence["story_id"] == "US-01-TEST"
    assert len(evidence["alerts"]) == 3
    assert set(evidence["open_questions"]) == {"Q-001", "QD-002"}
    assert "scan_test.md" in evidence["sources_consulted"]
    assert "scan_test.md" in evidence.get("source_hashes_sha256", {})
    assert len(evidence["source_hashes_sha256"]["scan_test.md"]) == 64
    assert "epistemic_audit" in evidence
    assert "what_it_actually_proves" in evidence["epistemic_audit"]
    assert "claim_boundaries" in evidence["epistemic_audit"]

    saved_path = engine.save_evidence_pack(evidence)
    assert saved_path.exists()

    data = json.loads(saved_path.read_text(encoding="utf-8"))
    assert data["story_id"] == "US-01-TEST"
    assert (
        data["source_hashes_sha256"]["scan_test.md"]
        == evidence["source_hashes_sha256"]["scan_test.md"]
    )


def test_evidence_pack_visual_contract_from_ingested_mockup_frontmatter(tmp_path):
    """
    Phase 1 (AXE 1) : lorsqu'une story référence une maquette ingérée (docs/00-ingested/maquettes/*.md)
    portant un frontmatter is_vectorized/ocr_status (produit par svg_to_md.py), l'EvidencePack doit
    exposer un bloc `visual_contract` traçant si le Contrat Visuel a réellement été lu (OCR) ou non.
    """
    project_dir = tmp_path / "TestProjectVisual"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    maquettes_dir = project_dir / "docs" / "00-ingested" / "maquettes"
    maquettes_dir.mkdir(parents=True)
    mockup_md = maquettes_dir / "confirmation_ecran.md"
    mockup_md.write_text(
        """---
title: "Spécification UI : Confirmation Ecran"
document_type: "ui_specification"
source_svg: "confirmation_ecran.svg"
is_vectorized: true
ocr_status: "UNAVAILABLE"
---
# Spécification UI Extraite
""",
        encoding="utf-8",
    )

    story_file = stories_dir / "US-02.md"
    story_file.write_text(
        """---
id: US-02-TEST
status: IN_ANALYZE
---
# US-02 : Test Story Visuelle

- **Ref**: [confirmation_ecran.md](../../docs/00-ingested/maquettes/confirmation_ecran.md)
""",
        encoding="utf-8",
    )

    engine = EvidencePackEngine(project_dir)
    evidence = engine.extract_evidence(story_file)

    assert "visual_contract" in evidence
    contracts = evidence["visual_contract"]
    assert len(contracts) == 1
    assert contracts[0]["mockup_path"].endswith("confirmation_ecran.md")
    assert contracts[0]["is_vectorized"] is True
    assert contracts[0]["ocr_status"] == "UNAVAILABLE"


def test_evidence_pack_visual_contract_empty_when_no_mockup_referenced(tmp_path):
    """Aucune maquette référencée -> visual_contract est une liste vide (pas d'invention de contrat)."""
    project_dir = tmp_path / "TestProjectNoVisual"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    story_file = stories_dir / "US-03.md"
    story_file.write_text(
        """---
id: US-03-TEST
status: IN_ANALYZE
---
# US-03 : Story Sans Maquette
""",
        encoding="utf-8",
    )

    engine = EvidencePackEngine(project_dir)
    evidence = engine.extract_evidence(story_file)

    assert evidence["visual_contract"] == []


def test_evidence_pack_socle_factuel_defaults_to_unvalidated(tmp_path):
    """
    Phase 2.2 : par défaut (aucune mention explicite dans le récit), le socle factuel
    n'est PAS considéré comme validé par l'humain. Champ traçable pour élévation future
    en BLOCKING (cf. plan Phase 2.2 — non bloquant à ce stade).
    """
    project_dir = tmp_path / "TestProjectSocle"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    story_file = stories_dir / "US-04.md"
    story_file.write_text(
        """---
id: US-04-TEST
status: READY_FOR_DEV
---
# US-04 : Story Sans Validation Explicite
""",
        encoding="utf-8",
    )

    engine = EvidencePackEngine(project_dir)
    evidence = engine.extract_evidence(story_file)

    assert evidence["socle_factuel_validated_by_human"] is False
    assert evidence["socle_factuel_validated_at"] is None


def test_evidence_pack_preserves_human_validation_on_regeneration(tmp_path):
    """
    BUG-WIKIFIX-03 (anti-régression) : lors d'une régénération (WikiFix/sync), les champs
    scellés par l'humain sur l'EvidencePack existant NE doivent PAS être écrasés par les
    valeurs par défaut. Merge non-destructif de socle_factuel_validated_by_human / _at.
    """
    project_dir = tmp_path / "TestProjectPreserve"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)

    story_file = stories_dir / "US-05.md"
    story_file.write_text(
        """---
id: US-05-TEST
status: READY_FOR_GROOMING
---
# US-05 : Story avec socle validé humainement
""",
        encoding="utf-8",
    )

    engine = EvidencePackEngine(project_dir)

    # 1er passage : génère et sauvegarde le pack (socle non validé par défaut)
    pack1 = engine.extract_evidence(story_file)
    engine.save_evidence_pack(pack1)

    # L'humain scelle manuellement le socle dans le pack existant sur disque
    pack_path = project_dir / "memory" / "evidence" / "US-05-TEST_evidence.json"
    sealed = json.loads(pack_path.read_text(encoding="utf-8"))
    sealed["socle_factuel_validated_by_human"] = True
    sealed["socle_factuel_validated_at"] = "2026-09-10T10:52:00+00:00"
    pack_path.write_text(json.dumps(sealed, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2e passage (régénération WikiFix) : DOIT préserver le scellé humain
    pack2 = engine.extract_evidence(story_file)

    assert pack2["socle_factuel_validated_by_human"] is True, (
        "La régénération ne doit pas écraser la validation humaine existante."
    )
    assert pack2["socle_factuel_validated_at"] == "2026-09-10T10:52:00+00:00"


def test_evidence_pack_projection_from_fact_dossier(tmp_path):
    """
    Vérifie la projection du Dossier de Preuves Documentaires dans l'EvidencePack :
    - Extraction des faits F-01..F-NN sans duplication de prose
    - Rehaussement en ssot_dossier_grounded avec confidence HIGH/1.0
    - Hachage cryptographique du dossier et des sources canoniques déclarées
    """
    project_dir = tmp_path / "TestProjectDossier"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)
    evidence_dir = project_dir / "memory" / "evidence"
    evidence_dir.mkdir(parents=True)
    models_dir = project_dir / "docs" / "03-models"
    models_dir.mkdir(parents=True)

    # 1. Source canonique SSOT physique
    (models_dir / "modele-incubation.md").write_text(
        "Table boire_ref_incubator { id uuid, code varchar(50) }", encoding="utf-8"
    )

    # 2. Dossier de Preuves Documentaires
    dossier_file = evidence_dir / "INC-003-BE_fact_dossier.md"
    dossier_file.write_text(
        """---
story_id: INC-003-BE
jira_key: COUVBOIRE-1064
dossier_status: CURRENT
sources_hashes:
  modele-incubation.md: dummyhash123
---
# Dossier de Preuves — INC-003-BE

## 🔬 2. Faits Extraits & Verbatims

| # | Table / Source | Définition DBML Exacte | Rôle dans le Payload API |
| :---: | :--- | :--- | :--- |
| **F-01** | `boire_ref_incubator` | `Table boire_ref_incubator { id uuid }` | Machine d'incubation : code et type. |
| **F-02** | `IncubationAssignment` | `Table IncubationAssignment { id uuid }` | Affectation physique rattachée au coup. |

## 🗄️ 3. Schéma Relationnel SSOT
```mermaid
erDiagram
    boire_ref_incubator ||--o{ IncubationAssignment : heberge
```

## 🎯 4. Contrats Déclaratifs Cibles
`GET /api/v1/incubation/assignments`
""",
        encoding="utf-8",
    )

    # 3. User Story Gherkin pure (sans section technique)
    story_file = stories_dir / "INC-003-BE.md"
    story_file.write_text(
        """---
id: INC-003-BE
jira_key: COUVBOIRE-1064
status: READY_FOR_DEV
---
# INC-003-BE : Consultation des assignations

## Critères d'acceptation
- Critère 1 : Consultation par date

## Scénarios de test
### Pilier 1 : Nominal
- Scénario : Consultation avec succès
""",
        encoding="utf-8",
    )

    engine = EvidencePackEngine(project_dir)
    evidence = engine.extract_evidence(story_file)

    # Validations du contrat d'architecture
    assert evidence["story_id"] == "INC-003-BE"
    # MLOOP-180-BE (Déc.5) : richesse=0 (aucun verbatim/décision/contrat) →
    # multiplier=0.7 → confidence dégradée HIGH→MEDIUM, score=1.0×0.7=0.7
    assert evidence["confidence"] == "MEDIUM"
    assert evidence["confidence_score"] == pytest.approx(0.7, abs=1e-4)
    assert evidence["status"] == "VALIDATED"

    # Vérification des faits projetés
    assert len(evidence["facts_verified"]) == 2
    f1 = evidence["facts_verified"][0]
    assert f1["fact_id"] == "F-01"
    assert f1["source_ref"] == "boire_ref_incubator"
    assert f1["rule_summary"] == "Machine d'incubation : code et type."
    assert f1["status"] == "VERIFIED"

    f2 = evidence["facts_verified"][1]
    assert f2["fact_id"] == "F-02"
    assert f2["source_ref"] == "IncubationAssignment"

    # Vérification des empreintes
    assert "INC-003-BE_fact_dossier.md" in evidence["source_hashes_sha256"]
    assert "modele-incubation.md" in evidence["source_hashes_sha256"]
    assert len(evidence["source_hashes_sha256"]["modele-incubation.md"]) == 64

    # Preuve rehaussée en ssot_dossier_grounded
    dossier_proofs = [
        p for p in evidence["fact_search_proofs"] if p["source_file"] == "modele-incubation.md"
    ]
    assert len(dossier_proofs) == 1
    assert dossier_proofs[0]["verification_method"] == "ssot_dossier_grounded"
    assert dossier_proofs[0]["confidence"] == "HIGH"
    assert dossier_proofs[0]["confidence_score"] == 1.0


# ══════════════════════════════════════════════════════════════════════════════
# MLOOP-180-BE — Tests de parité Phase 2 (CA-1 à CA-6 / ADR-0369)
# ══════════════════════════════════════════════════════════════════════════════


def _make_minimal_story(tmp_path: Path, story_id: str, content_extra: str = "") -> tuple:
    """Fixture helper : projet minimal + fichier story, retourne (engine, story_file)."""
    project_dir = tmp_path / f"Proj_{story_id}"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)
    story_file = stories_dir / f"{story_id}.md"
    story_file.write_text(
        f"---\nid: {story_id}\nstatus: READY_FOR_DEV\n---\n# {story_id}\n{content_extra}",
        encoding="utf-8",
    )
    engine = EvidencePackEngine(project_dir)
    return engine, story_file


# ── Test 1 : CA-1 — 5 champs présents par défaut ─────────────────────────────


def test_extract_evidence_includes_5_parity_fields_by_default(tmp_path):
    """CA-1 : un pack neuf sans données source doit exposer les 5 clés de parité."""
    engine, story_file = _make_minimal_story(tmp_path, "MLOOP-180-T1")
    evidence = engine.extract_evidence(story_file)

    for field in (
        "verbatim_extracts",
        "implementation_decisions",
        "declarative_contracts",
        "conflict_matrix",
    ):
        assert field in evidence, f"Champ manquant : {field!r}"
        assert isinstance(evidence[field], list), f"{field!r} doit être une liste"

    # richness_penalty dans epistemic_audit
    assert "richness_penalty" in evidence["epistemic_audit"], (
        "richness_penalty manquant dans epistemic_audit"
    )


# ── Test 2 : CA-2 — validation VerbatimExtract (parametrize) ─────────────────


@pytest.mark.parametrize(
    "extract, expected_fragment",
    [
        # quote vide → rejet
        (
            {"source_file": "foo.md", "lines": [1, 5], "quote": "", "established_fact": "fait"},
            "quote",
        ),
        # lines=None → rejet
        (
            {"source_file": "foo.md", "lines": None, "quote": "texte", "established_fact": "fait"},
            "ancrage ligne obligatoire",
        ),
        # lines mal ordonnées (start > end) → rejet
        (
            {
                "source_file": "foo.md",
                "lines": [10, 2],
                "quote": "texte",
                "established_fact": "fait",
            },
            "start doit être ≤ end",
        ),
        # lines non liste → rejet (les crochets sont échappés car match est un pattern regex)
        (
            {"source_file": "foo.md", "lines": 5, "quote": "texte", "established_fact": "fait"},
            r"doit être \[start, end\]",
        ),
    ],
)
def test_verbatim_extracts_requires_nonempty_quote_and_lines(extract, expected_fragment):
    """CA-2 : VerbatimExtract invalide → ValueError contextuelle (ADR-0369)."""
    with pytest.raises(ValueError, match=expected_fragment):
        EvidencePackEngine._validate_verbatim_extract(extract)  # type: ignore[arg-type]


def test_verbatim_extract_valid_does_not_raise():
    """CA-2 (nominal) : un VerbatimExtract correct ne lève pas d'exception."""
    EvidencePackEngine._validate_verbatim_extract(
        {
            "source_file": "foo.md",
            "lines": [3, 7],
            "quote": "un texte valide",
            "established_fact": "fait établi",
        }
    )  # ne doit pas lever


# ── Test 3 : CA-3 — liste fermée des catégories de décision (parametrize) ────


@pytest.mark.parametrize(
    "category",
    ["architecture", "pattern", "refactoring", "performance", "security", "tooling", "testing"],
)
def test_implementation_decision_category_valid_does_not_raise(category):
    """CA-3 : les 7 catégories autorisées ne lèvent pas d'exception."""
    EvidencePackEngine._validate_decision_category(category)  # ne doit pas lever


def test_implementation_decision_category_closed_list_raises_for_invalid():
    """CA-3 : catégorie hors liste fermée → ValueError contextualisée."""
    with pytest.raises(ValueError, match="hors liste fermée"):
        EvidencePackEngine._validate_decision_category("random_choice")


@pytest.mark.parametrize("bad_cat", ["ARCHITECTURE", "infra", "ops", ""])
def test_implementation_decision_category_rejects_variants(bad_cat):
    """CA-3 : variantes (casse, alias, vide) → ValueError."""
    with pytest.raises(ValueError):
        EvidencePackEngine._validate_decision_category(bad_cat)


# ── Test 4 : richness_penalty présent dans epistemic_audit ───────────────────


def test_epistemic_audit_has_richness_penalty_key(tmp_path):
    """CA-1 (UX) : richness_penalty exposé dans epistemic_audit avec les clés attendues."""
    engine, story_file = _make_minimal_story(tmp_path, "MLOOP-180-T4")
    evidence = engine.extract_evidence(story_file)

    penalty = evidence["epistemic_audit"]["richness_penalty"]
    for key in ("richness", "multiplier", "score", "reason"):
        assert key in penalty, f"Clé manquante dans richness_penalty : {key!r}"

    assert isinstance(penalty["richness"], int)
    assert isinstance(penalty["multiplier"], float)
    assert isinstance(penalty["score"], float)
    assert isinstance(penalty["reason"], str)


# ── Test 5 : bornes du multiplicateur de richesse (Déc.5) ────────────────────


def test_richness_multiplier_bounds(tmp_path):
    """Déc.5 : richesse=0 → mult=0.7 ; richesse≥10 → mult=1.0 (formule verrouillée)."""
    engine, story_file = _make_minimal_story(tmp_path, "MLOOP-180-T5")
    evidence = engine.extract_evidence(story_file)

    penalty = evidence["epistemic_audit"]["richness_penalty"]
    richness = penalty["richness"]
    multiplier = penalty["multiplier"]

    if richness == 0:
        assert multiplier == pytest.approx(0.7), (
            f"richesse=0 → multiplicateur attendu 0.7, obtenu {multiplier}"
        )
    elif richness >= 10:
        assert multiplier == pytest.approx(1.0), (
            f"richesse≥10 → multiplicateur attendu 1.0, obtenu {multiplier}"
        )
    else:
        expected = round(0.7 + 0.3 * min(1.0, richness / 10), 4)
        assert multiplier == pytest.approx(expected, abs=1e-4), (
            f"richesse={richness} → mult attendu {expected}, obtenu {multiplier}"
        )

    # La story minimale n'a aucun extract/decision/contract → richesse=0 → mult=0.7
    assert richness == 0
    assert multiplier == pytest.approx(0.7)


# ── Test 6 : CA-5 — rétrocompatibilité pack legacy sans les 5 champs ─────────


def test_legacy_pack_without_5_fields_still_parses(tmp_path):
    """CA-5 : un pack existant sans les 5 champs est rechargeable sans KeyError."""
    project_dir = tmp_path / "ProjLegacy"
    project_dir.mkdir()
    stories_dir = project_dir / "backlog" / "stories"
    stories_dir.mkdir(parents=True)
    evidence_dir = project_dir / "memory" / "evidence"
    evidence_dir.mkdir(parents=True)

    story_file = stories_dir / "LEGACY-001.md"
    story_file.write_text(
        "---\nid: LEGACY-001\nstatus: READY_FOR_DEV\n---\n# Legacy story\n",
        encoding="utf-8",
    )

    # Simule un pack legacy sans les 5 champs (71 packs existants avant MLOOP-180-BE)
    legacy_pack = {
        "story_id": "LEGACY-001",
        "jira_key": None,
        "timestamp": "2026-01-01T00:00:00+00:00",
        "fact_search_status": "VERIFIED",
        "fact_search_proofs": [],
        "source_hashes_sha256": {},
        "epistemic_audit": {
            "what_it_actually_proves": ["Spécification basée sur modèle déclaratif"],
            "what_it_does_not_prove": ["Aucune question ouverte non résolue"],
            "claim_boundaries": "Périmètre fonctionnel restreint aux 4 Piliers Gherkin du récit",
        },
        "facts_verified": [],
        "sources_consulted": [],
        "external_references": [],
        "alerts": [],
        "open_questions": [],
        "visual_contract": [],
        "socle_factuel_validated_by_human": False,
        "socle_factuel_validated_at": None,
        "verification_harness": [],
        "next_actions": [],
        "confidence": "MEDIUM",
        "confidence_score": 0.75,
        "status": "VALIDATED",
        # NB : PAS de verbatim_extracts, implementation_decisions,
        #      declarative_contracts, conflict_matrix — c'est l'état legacy.
    }
    pack_path = evidence_dir / "LEGACY-001_evidence.json"
    pack_path.write_text(json.dumps(legacy_pack, indent=2), encoding="utf-8")

    # Régénération via extract_evidence → ne doit pas lever de KeyError
    engine = EvidencePackEngine(project_dir)
    evidence = engine.extract_evidence(story_file)

    # Les 5 champs doivent être présents (initialisés à []) même si le pack legacy ne les avait pas
    assert "verbatim_extracts" in evidence
    assert "implementation_decisions" in evidence
    assert "declarative_contracts" in evidence
    assert "conflict_matrix" in evidence
    assert isinstance(evidence["verbatim_extracts"], list)
    assert isinstance(evidence["implementation_decisions"], list)
    assert isinstance(evidence["declarative_contracts"], list)
    assert isinstance(evidence["conflict_matrix"], list)

    # Le socle humain ne doit pas être perdu (merge non-destructif)
    # legacy n'a pas de socle validé → False par défaut
    assert evidence["socle_factuel_validated_by_human"] is False


# ── Test 7 : conflict_matrix et declarative_contracts — backcompat .get() ─────


def test_conflict_matrix_declarative_contracts_optional_backcompat(tmp_path):
    """CA-5 : accès .get() sur un pack sans les champs ne lève aucune KeyError."""
    engine, story_file = _make_minimal_story(tmp_path, "MLOOP-180-T7")
    evidence = engine.extract_evidence(story_file)

    # Simule un appelant legacy lisant le pack avec .get() (Zéro KeyError garanti)
    conflict_matrix = evidence.get("conflict_matrix", [])
    declarative_contracts = evidence.get("declarative_contracts", [])
    verbatim_extracts = evidence.get("verbatim_extracts", [])
    implementation_decisions = evidence.get("implementation_decisions", [])

    assert isinstance(conflict_matrix, list)
    assert isinstance(declarative_contracts, list)
    assert isinstance(verbatim_extracts, list)
    assert isinstance(implementation_decisions, list)

    # Les listes sont vides (aucune source dans la story minimale)
    assert conflict_matrix == []
    assert declarative_contracts == []
    assert verbatim_extracts == []
    assert implementation_decisions == []

    # Vérification que le pack sérialisé (JSON round-trip) est stable sans KeyError
    saved_path = engine.save_evidence_pack(evidence)
    reloaded = json.loads(saved_path.read_text(encoding="utf-8"))

    for field in (
        "verbatim_extracts",
        "implementation_decisions",
        "declarative_contracts",
        "conflict_matrix",
    ):
        assert field in reloaded, f"Champ {field!r} absent après sérialisation JSON"
        assert isinstance(reloaded[field], list)
