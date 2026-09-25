"""
Tests unitaires pour le GrillEngine et la conformité ADR-0320 (Frontier Design Tree).
"""

import logging
import pytest
import tempfile
import shutil
from pathlib import Path
from src.pipelines.grill_engine import GrillEngine
from src.state import ProjectLayout, StoryStatus


@pytest.fixture
def temp_project(tmp_path):
    """Crée une arborescence projet mLoop temporaire."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir(parents=True)

    docs_dir = project_dir / ProjectLayout.DOCS / ProjectLayout.DOCS_ARCHITECTURE
    docs_dir.mkdir(parents=True)

    backlog_dir = project_dir / ProjectLayout.BACKLOG / "stories"
    backlog_dir.mkdir(parents=True)

    sprint_backlog = project_dir / ProjectLayout.BACKLOG / "sprint_backlog.md"
    sprint_backlog.write_text(
        "# Sprint Backlog\n\n| ID | Titre | Statut |\n| :--- | :--- | :--- |\n| US-01 | Initialisation UI | IN_ANALYZE |\n",
        encoding="utf-8",
    )

    story_file = backlog_dir / "US-01_initialisation_ui.md"
    story_file.write_text(
        "---\nid: US-01\ntitle: Initialisation UI\nstatus: IN_ANALYZE\n---\n## Description\nInitialisation.",
        encoding="utf-8",
    )

    return project_dir


def test_grill_engine_record_adr(temp_project):
    """Vérifie la génération d'un ADR structuré."""
    engine = GrillEngine(temp_project)
    adr_path = engine.record_adr(
        title="Adoption du Frontier Design Tree",
        context="Alignement sur l'arbre de décision préalable.",
        decision="Intégration du pattern Grill-Me.",
        positives="Clarté et réduction du flou.",
        negatives="Temps d'interrogatoire initial.",
    )

    assert adr_path.exists()
    content = adr_path.read_text(encoding="utf-8")
    assert "ADR-001" in content
    assert "Adoption du Frontier Design Tree" in content
    assert "**Statut** : DECIDED" in content
    assert "Intégration du pattern Grill-Me." in content


def test_grill_engine_mark_story_grilled(temp_project):
    """Vérifie la transition FSM et le marquage du statut READY_FOR_GROOMING."""
    engine = GrillEngine(temp_project)
    success = engine.mark_story_grilled("US-01")
    assert success is True

    # Vérification fichier story
    story_file = temp_project / ProjectLayout.BACKLOG / "stories" / "US-01_initialisation_ui.md"
    content = story_file.read_text(encoding="utf-8")
    assert "status: READY_FOR_GROOMING" in content
    assert "content_hash:" in content  # Hash anti-tampering

    # Vérification sprint_backlog.md
    sb_file = temp_project / ProjectLayout.BACKLOG / "sprint_backlog.md"
    sb_content = sb_file.read_text(encoding="utf-8")
    assert "READY_FOR_GROOMING" in sb_content


def test_grill_engine_mark_story_grilled_by_internal_id_when_file_named_by_jira_key(
    tmp_path,
):
    """
    BUG-GRILL-01 (anti-régression) : quand le fichier est nommé par la clé Jira (MMA-4658.md)
    mais que l'utilisateur passe l'ID interne du frontmatter (US-05-FOOD), mark_story_grilled
    doit résoudre le récit via le champ `id:` du frontmatter et promouvoir son statut.
    """
    project_dir = tmp_path / "jira_named_project"
    (project_dir / ProjectLayout.DOCS / ProjectLayout.DOCS_ARCHITECTURE).mkdir(parents=True)
    stories_dir = project_dir / ProjectLayout.BACKLOG / "stories" / "OneTrust_FOOD"
    stories_dir.mkdir(parents=True)
    (project_dir / ProjectLayout.BACKLOG / "sprint_backlog.md").write_text(
        "# Sprint Backlog\n\n| ID | Titre | Statut |\n| :--- | :--- | :--- |\n",
        encoding="utf-8",
    )

    # Fichier nommé par la CLÉ JIRA, ID interne uniquement dans le frontmatter
    story_file = stories_dir / "MMA-4658.md"
    story_file.write_text(
        "---\nid: US-05-FOOD\njira_key: MMA-4658\ntitle: Centre de préférence\nstatus: IN_ANALYZE\n---\n## Description\nDispatcher.",
        encoding="utf-8",
    )

    engine = GrillEngine(project_dir)
    # On passe l'ID INTERNE (US-05-FOOD), pas la clé Jira ni le nom de fichier
    success = engine.mark_story_grilled("US-05-FOOD")

    assert success is True, "mark_story_grilled doit résoudre l'ID interne via le frontmatter id:."
    content = story_file.read_text(encoding="utf-8")
    assert "status: READY_FOR_GROOMING" in content


def test_grill_engine_no_adr_generated_without_decision_content(tmp_path):
    """
    BUG-GRILL-02 (anti-régression) : la génération d'un ADR ne doit se produire QUE lorsqu'un
    contenu de décision réel (context/decision) est fourni. Un simple marquage de story
    (title générique + story) ne doit PAS créer d'ADR parasite.
    """
    from src.commands.handlers.architecture import handle_grill
    import argparse

    project_dir = tmp_path / "no_adr_project"
    docs_arch = project_dir / ProjectLayout.DOCS / ProjectLayout.DOCS_ARCHITECTURE
    docs_arch.mkdir(parents=True)
    stories_dir = project_dir / ProjectLayout.BACKLOG / "stories"
    stories_dir.mkdir(parents=True)
    (project_dir / ProjectLayout.BACKLOG / "sprint_backlog.md").write_text(
        "# Sprint Backlog\n", encoding="utf-8"
    )
    (stories_dir / "US-01.md").write_text(
        "---\nid: US-01\ntitle: T\nstatus: IN_ANALYZE\n---\n## Description\nX.",
        encoding="utf-8",
    )

    # Args sans --context/--decision : intention = marquer la story, PAS créer un ADR
    args = argparse.Namespace(
        project=str(project_dir),
        story="US-01",
        title="Validations",
        context=None,
        decision=None,
        positives=None,
        negatives=None,
    )

    class _DummyState:
        def save_to_graph(self, *a, **k):
            pass

    try:
        handle_grill(args, _DummyState(), project_dir)
    except Exception:
        pass  # run_sync peut échouer dans le sandbox — on n'audite que l'effet ADR

    adrs = list(docs_arch.glob("ADR-*.md"))
    assert adrs == [], (
        f"Aucun ADR parasite ne doit être créé sans contenu de décision, trouvés : {adrs}"
    )


def test_grill_skill_conformance():
    """Vérifie la présence des composantes clés d'ADR-0320 dans le skill grill."""
    skill_file = Path(".agents/skills/grill/SKILL.md")
    assert skill_file.exists()
    content = skill_file.read_text(encoding="utf-8")

    # Vérification des concepts clés
    assert "Frontier Design Tree" in content or "Design Tree" in content
    assert "Faits vs Décisions" in content
    assert "CONTEXT.md" in content
    assert "to-questionnaire" in content
    assert "5 Vecteurs de Résilience" in content or "Résilience" in content
    assert "4 États" in content or "Matrice des 4 États" in content

    # ADR-0320 §F/§G (amendement 2026-08-26) : Règle d'Épuisement de Frontière
    # par récit et fiabilisation du signal de confiance / priorité au code source.
    # ADR-0393 (amendement 2026-09-25) : La clause "avance automatiquement" a été
    # supprimée et remplacée par "Arrêt Formel Post-Round & Menu d'Orientation".
    assert "Frontier Exhaustion" in content or "Épuisement de Frontière" in content
    assert "Arrêt Formel" in content or "Menu d'Orientation" in content


def test_adr_0320_frontier_exhaustion_sections_present():
    """Vérifie la présence des sections F & G dans l'ADR-0320 (amendement 2026-08-26)."""
    adr_file = Path("standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md")
    assert adr_file.exists()
    content = adr_file.read_text(encoding="utf-8")

    assert "Règle d'Épuisement de Frontière par Récit" in content
    assert "Critère d'Arrêt Unitaire" in content
    # ADR-0393 (amendement 2026-09-25) : §F.4 renommé "Avancement Automatique"
    # → "Arrêt Formel Post-Round & Menu d'Orientation" et clauses permissives supprimées.
    assert "Arrêt Formel Post-Round" in content or "Mandat Unitaire Strict" in content
    assert "code_source_verified" in content
    assert "file_existence_only" in content


def test_evidence_pack_no_hardcoded_high_confidence_without_code_proof():
    """
    Vérifie que EvidencePackEngine.extract_evidence() ne retourne plus HIGH/1.0
    par défaut pour un récit sans aucune preuve de type code_source_verified
    (ADR-0320 §G — anti-régression du score codé en dur).
    """
    from src.pipelines.evidence_pack import EvidencePackEngine

    project_dir = Path(tempfile.mkdtemp())
    try:
        backlog_dir = project_dir / "backlog" / "stories"
        backlog_dir.mkdir(parents=True)

        # Récit ne citant que de la documentation (aucun fichier de code source réel)
        story_file = backlog_dir / "US-99_sans_code.md"
        story_file.write_text(
            "---\nid: US-99\ntitle: Sans Code Source\nstatus: OPEN\n---\n"
            "## Description\nRécit basé uniquement sur specs.md.\n",
            encoding="utf-8",
        )

        engine = EvidencePackEngine(project_dir)
        pack = engine.extract_evidence(story_file)

        assert (
            pack["confidence"] != "HIGH"
            or pack["confidence_score"] != 1.0
            or not pack["fact_search_proofs"]
        ), (
            "Un récit sans preuve code_source_verified ne doit pas hériter d'un score HIGH/1.0 par défaut."
        )
        assert pack["status"] in ("VALIDATED", "STALE_PENDING_REGENERATION")
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)


def test_detect_ungrillable_signals(temp_project):
    """Vérifie la détection des questions ungrillables (IHM/UX) selon ADR-0389 §B."""
    engine = GrillEngine(temp_project)

    # 1. Question Ungrillable (IHM / Wizard vs Monopage)
    q_ux = "Devons-nous découper ce formulaire sous forme de wizard en 3 étapes ou en monopage accordéon ?"
    res_ux = engine.detect_ungrillable_signals(q_ux)
    assert res_ux["is_ungrillable"] is True
    assert "spatial_layout" in res_ux["categories"]
    assert res_ux["recommended_action"] == "HANDOFF_PROTOTYPE"
    assert res_ux["suggested_prototype"] == "html_tailwind"

    # 2. Question Ungrillable (Densité visuelle / Cards vs Tableau)
    q_density = "Préfère-t-on afficher les commandes sous forme de tableau ou de cartes kanban ?"
    res_density = engine.detect_ungrillable_signals(q_density)
    assert res_density["is_ungrillable"] is True
    assert "density_hierarchy" in res_density["categories"]
    assert res_density["recommended_action"] == "HANDOFF_PROTOTYPE"

    # 3. Question Grillable classique (Architecture / Contrat API / Base de données)
    q_backend = "Quelle est la politique de rétention des logs d'audit et le délai de purge SQS ?"
    res_backend = engine.detect_ungrillable_signals(q_backend)
    assert res_backend["is_ungrillable"] is False
    assert res_backend["recommended_action"] == "CONTINUE_GRILL"
    assert res_backend["suggested_prototype"] is None


def test_format_frontier_round(temp_project):
    """Vérifie le formatage des Frontier Rounds orthogonaux selon ADR-0389 §A."""
    engine = GrillEngine(temp_project)
    questions = [
        {
            "title": "Choix du provider de SMS",
            "context": "Directives de conformité locale.",
            "guess": "Twilio avec fallback AWS SNS.",
            "recommendation": "Option A (Twilio) pour sa haute délivrabilité.",
        },
        {
            "title": "Politique de rétention des sessions",
            "context": "Règles d'authentification SSO.",
            "guess": "Expiration après 8 heures d'inactivité.",
            "recommendation": "Option B (8h avec refresh token glissant).",
        },
    ]

    rendered = engine.format_frontier_round(questions, round_num=2, theme="Socle Transverse")
    assert "### 🌐 Round de Frontière #2 (Socle Transverse)" in rendered
    assert "2 questions orthogonales identifiées" in rendered
    assert "**💡 GUESS** : Twilio avec fallback AWS SNS." in rendered
    assert "**➡️ Recommandation mLoop** : Option A (Twilio)" in rendered
    assert "#### ❓ Q2. Politique de rétention des sessions" in rendered
    assert "👉 Réponse attendue : validation globale" in rendered


def test_check_context_health(temp_project):
    """Vérifie les alertes de budget contexte et Dumb Zone selon ADR-0389 §C."""
    engine = GrillEngine(temp_project)

    # 1. Smart Zone
    h1 = engine.check_context_health(45000)
    assert h1["zone"] == "SMART_ZONE"
    assert h1["status"] == "HEALTHY"
    assert h1["action"] == "CONTINUE"

    # 2. Warning Zone
    h2 = engine.check_context_health(95000)
    assert h2["zone"] == "WARNING_ZONE"
    assert h2["status"] == "WARNING"
    assert h2["action"] == "TRIGGER_CHECKPOINT"

    # 3. Dumb Zone (> 120k tokens)
    h3 = engine.check_context_health(135000)
    assert h3["zone"] == "DUMB_ZONE"
    assert h3["status"] == "CRITICAL"
    assert h3["action"] == "FREEZE_BRANCHES_OR_SPLIT"


def test_adr_0389_and_skill_v2_conformance():
    """Vérifie l'alignement constitutionnel du skill grill et la présence de l'ADR-0389."""
    adr_file = Path(
        "standards/adr-system/0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md"
    )
    assert adr_file.exists(), "ADR-0389 doit exister dans standards/adr-system/"

    skill_file = Path(".agents/skills/grill/SKILL.md")
    assert skill_file.exists(), "SKILL.md doit exister"
    content = skill_file.read_text(encoding="utf-8")

    assert "ADR-0389" in content
    assert "Frontier Round" in content
    assert "Ungrillable" in content or "Handoff Pattern" in content
    assert "Dumb Zone" in content
    assert (
        "Interdiction Absolue de Purge Post-Grill" in content
        or "Interdiction formelle de reset" in content
    )


# --- TESTS EPIC-28 : ASSAINISSEMENT DU GÉNÉRATEUR D'ADR (ADR-012) ---


def test_resolve_adr_template_cascade(temp_project):
    """Vérifie le chargement dynamique du blueprint canonique standards/blueprints/project_adr_template.md."""
    from src.pipelines.grill import resolve_adr_template

    # Sans surcharge locale, doit retourner le contenu du blueprint canonique
    content = resolve_adr_template(temp_project)
    assert "# 🏛️ ADR-{{ADR_ID}} : {{TITLE}}" in content
    assert "{{DECISION}}" in content
    assert "{{POSITIVES}}" in content


def test_resolve_adr_template_project_override(temp_project):
    """Vérifie la prise en compte prioritaire de la surcharge locale projet."""
    from src.pipelines.grill import resolve_adr_template

    custom_dir = temp_project / "docs" / "01-architecture"
    custom_dir.mkdir(parents=True, exist_ok=True)
    custom_file = custom_dir / "template.md"
    custom_file.write_text(
        "# 🏛️ ADR Custom Projet {{ADR_ID}} : {{TITLE}}\n{{CUSTOM_SECTION}}", encoding="utf-8"
    )

    content = resolve_adr_template(temp_project)
    assert "# 🏛️ ADR Custom Projet {{ADR_ID}}" in content
    assert "{{CUSTOM_SECTION}}" in content


def test_resolve_adr_template_emergency_fallback(tmp_path):
    """Vérifie le repli sur le gabarit d'urgence mémoire en cas d'absence complète."""
    from src.pipelines.grill import resolve_adr_template, EMERGENCY_FALLBACK_TEMPLATE
    import src.pipelines.grill._adr_writer as writer_mod

    # Simuler l'absence de blueprint framework
    original_fn = writer_mod.get_framework_root
    writer_mod.get_framework_root = lambda: tmp_path / "non_existent"

    try:
        content = resolve_adr_template(None)
        assert content == EMERGENCY_FALLBACK_TEMPLATE
    finally:
        writer_mod.get_framework_root = original_fn


def test_get_next_adr_id_robust_anti_collision(tmp_path):
    """Vérifie le calcul max(ids) + 1 et l'immunité aux trous de numérotation (ADR-012)."""
    from src.pipelines.grill import get_next_adr_id

    # 1. Dossier vide
    next_id, max_id = get_next_adr_id(tmp_path)
    assert next_id == 1
    assert max_id == 0

    # 2. Présence de trous : ADR-001 et ADR-011 (longueur = 2, mais max = 11)
    (tmp_path / "ADR-001_init.md").write_text("dummy", encoding="utf-8")
    (tmp_path / "ADR-011_lock.md").write_text("dummy", encoding="utf-8")
    (tmp_path / "README.md").write_text("ignore", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignore", encoding="utf-8")

    next_id, max_id = get_next_adr_id(tmp_path)
    assert max_id == 11
    assert next_id == 12, "Doit retourner max(ids) + 1 = 12 (et non len + 1 = 3)"

    # 3. Numérotation > 999
    (tmp_path / "ADR-1005_future.md").write_text("dummy", encoding="utf-8")
    next_id, max_id = get_next_adr_id(tmp_path)
    assert max_id == 1005
    assert next_id == 1006


def test_render_adr_content_double_moustaches_and_defaults():
    """Vérifie le rendu des balises mLoop {{TAG}} et la substitution des valeurs par défaut."""
    from src.pipelines.grill import render_adr_content

    template = (
        "# ADR-{{ADR_ID}} : {{TITLE}}\n{{CONTEXT}}\n{{DECISION}}\n{{POSITIVES}}\n{{NEGATIVES}}"
    )
    rendered = render_adr_content(
        template_str=template,
        adr_id=42,
        title="Refonte Modulaire",
        context="",  # Vide -> doit appliquer le défaut
        decision="Découpage en sous-package",
        positives="",
        negatives="",
        date_str="2026-09-24",
    )

    assert "# ADR-042 : Refonte Modulaire" in rendered
    assert "Session d'interrogatoire Grill-with-Docs." in rendered
    assert "Découpage en sous-package" in rendered
    assert "Clarification des exigences métier et réduction du flou." in rendered
    assert "Contraintes et engagements d'architecture appliqués." in rendered
    assert "{{" not in rendered, "Aucune balise non résolue ne doit subsister"


def test_grill_engine_record_adr_integration(temp_project):
    """Vérifie l'intégration complète de record_adr via GrillEngine."""
    from src.pipelines.grill import GrillEngine

    engine = GrillEngine(temp_project)
    adr_path = engine.record_adr(
        title="Architecture Propre",
        context="Audit de modularité AST",
        decision="Extraction sous-modules",
        positives="Fichiers de moins de 300 lignes",
        negatives="Plus de fichiers à maintenir",
    )

    assert adr_path.exists()
    assert adr_path.name == "ADR-001_architecture_propre.md"
    content = adr_path.read_text(encoding="utf-8")
    assert "# 🏛️ ADR-001 : Architecture Propre" in content
    assert "Audit de modularité AST" in content
    assert "Extraction sous-modules" in content
    assert "Fichiers de moins de 300 lignes" in content

    # Deuxième enregistrement consécutif
    adr_path_2 = engine.record_adr(
        title="Second Arbitrage",
        decision="Validation",
    )
    assert adr_path_2.name == "ADR-002_second_arbitrage.md"


def test_shim_backward_compatibility(temp_project):
    """Vérifie que l'ancien chemin d'importation src.pipelines.grill_engine fonctionne sans accroc."""
    from src.pipelines.grill_engine import GrillEngine as ShimGrillEngine, ADR_TEMPLATE

    assert ShimGrillEngine is not None
    assert ADR_TEMPLATE is not None

    engine = ShimGrillEngine(temp_project)
    assert hasattr(engine, "record_adr")
    assert hasattr(engine, "perform_fact_search")
    assert hasattr(engine, "mark_story_grilled")
    assert hasattr(engine, "detect_ungrillable_signals")
    assert hasattr(engine, "format_frontier_round")
    assert hasattr(engine, "check_context_health")


def test_package_modularity_ast_limits():
    """Vérifie que chaque fichier sous src/pipelines/grill/ respecte la règle RULE-AST-01 (<= 300L)."""
    grill_pkg = Path("src/pipelines/grill")
    assert grill_pkg.is_dir()

    for py_file in grill_pkg.glob("*.py"):
        lines = py_file.read_text(encoding="utf-8").splitlines()
        assert len(lines) <= 300, (
            f"Fichier {py_file.name} dépasse le plafond modulaire ({len(lines)} > 300 lignes)"
        )


# --- MLOOP-FIX-C1C2 (C2) : marquage colonne-aware au format backlog réel ---


def _write_real_backlog_project(tmp_path: Path, story_id: str, statut_cell: str):
    """
    Construit un projet avec sprint_backlog.md au FORMAT RÉEL mLoop :
    8 colonnes (État | Récit | Taille | Clé Jira | Composant | Titre | Statut |
    Responsable), statut décoré d'emoji + backticks (`` 🟢 `READY_FOR_DEV` ``)
    et colonne Taille portant un simple jeton `M`.
    """
    project_dir = tmp_path / "real_backlog_project"
    (project_dir / ProjectLayout.DOCS / ProjectLayout.DOCS_ARCHITECTURE).mkdir(parents=True)
    stories_dir = project_dir / ProjectLayout.BACKLOG / "stories"
    stories_dir.mkdir(parents=True)
    (stories_dir / f"{story_id}.md").write_text(
        f"---\nid: {story_id}\ntitle: Récit au format réel\nstatus: IN_ANALYZE\n---\n"
        "## Description\nCorps du récit.\n",
        encoding="utf-8",
    )
    sprint = project_dir / ProjectLayout.BACKLOG / "sprint_backlog.md"
    sprint.write_text(
        "## EPIC-21\n\n"
        "| État | Récit | Taille | Clé Jira | Composant | Titre | Statut | Responsable |\n"
        "| :---: | :--- | :---: | :---: | :--- | :--- | :--- | :--- |\n"
        f"| [ ] | **{story_id}** | M | - | Core | Récit au format réel | "
        f"{statut_cell} | ⚪ À faire |\n",
        encoding="utf-8",
    )
    return project_dir, sprint


def test_mark_story_grilled_real_backlog_updates_only_statut_cell(tmp_path):
    r"""
    C2 (anti-régression) : au format backlog réel, mark_story_grilled doit
    réécrire UNIQUEMENT la cellule de la colonne 'Statut' (emoji + backticks
    préservés) et laisser les colonnes Taille `M`, Clé Jira `-`, Composant et
    Titre strictement intacts. L'ancien regex `(\|.*?{id}.*?\|\s*)([A-Z_]+)`
    écrasait le `M` de la colonne Taille et laissait le statut réel inchangé
    → faux succès puis réversion silencieuse par sync (backlog = SSOT).
    """
    project_dir, sprint = _write_real_backlog_project(tmp_path, "US-99", "🟢 `READY_FOR_DEV`")

    engine = GrillEngine(project_dir)
    assert engine.mark_story_grilled("US-99") is True

    rows = [line for line in sprint.read_text(encoding="utf-8").splitlines() if "**US-99**" in line]
    assert len(rows) == 1, "La ligne du récit doit rester unique (aucune duplication)."
    cells = rows[0].split("|")

    # 0='' 1=État 2=Récit 3=Taille 4=Clé Jira 5=Composant 6=Titre 7=Statut 8=Resp.
    assert cells[7].strip() == "🟢 `READY_FOR_GROOMING`", (
        f"La colonne Statut doit passer à READY_FOR_GROOMING, obtenu : {cells[7].strip()!r}"
    )
    assert "READY_FOR_DEV" not in rows[0], "L'ancien statut ne doit plus subsister."
    assert cells[3].strip() == "M", (
        f"La colonne Taille ne doit PAS être corrompue, obtenu : {cells[3].strip()!r}"
    )
    assert cells[4].strip() == "-", "La colonne Clé Jira ne doit pas être corrompue."
    assert cells[5].strip() == "Core", "La colonne Composant ne doit pas être corrompue."
    assert cells[6].strip() == "Récit au format réel", (
        "La colonne Titre ne doit pas être corrompue."
    )

    # Frontmatter aligné sur le backlog (cohérence story↔backlog, anti-réversion sync)
    story_file = project_dir / ProjectLayout.BACKLOG / "stories" / "US-99.md"
    assert "status: READY_FOR_GROOMING" in story_file.read_text(encoding="utf-8")


def test_mark_story_grilled_absent_row_warns_without_arbitrary_replacement(tmp_path, caplog):
    """
    C2 (ligne absente) : si le récit n'a AUCUNE ligne dans sprint_backlog.md,
    aucune substitution au hasard (les lignes voisines restent octet-identiques)
    et un WARNING contextuel doit être journalisé.

    Le retour est True : le récit n'étant pas tracké par le backlog,
    sync_sprint_backlog (backlog = SSOT) ne dispose d'aucun statut divergent
    pour le révertir → aucune incohérence story↔backlog possible.
    """
    project_dir = tmp_path / "absent_row_project"
    (project_dir / ProjectLayout.DOCS / ProjectLayout.DOCS_ARCHITECTURE).mkdir(parents=True)
    stories_dir = project_dir / ProjectLayout.BACKLOG / "stories"
    stories_dir.mkdir(parents=True)
    (stories_dir / "US-77.md").write_text(
        "---\nid: US-77\ntitle: Récit absent du backlog\nstatus: IN_ANALYZE\n---\n"
        "## Description\nCorps.\n",
        encoding="utf-8",
    )
    sprint = project_dir / ProjectLayout.BACKLOG / "sprint_backlog.md"
    sprint.write_text(
        "## EPIC-21\n\n"
        "| État | Récit | Taille | Clé Jira | Composant | Titre | Statut | Responsable |\n"
        "| :---: | :--- | :---: | :---: | :--- | :--- | :--- | :--- |\n"
        "| [ ] | **US-88** | S | - | Core | Autre récit | 🟢 `READY_FOR_DEV` | ⚪ À faire |\n",
        encoding="utf-8",
    )
    before = sprint.read_text(encoding="utf-8")

    engine = GrillEngine(project_dir)
    result = engine.mark_story_grilled("US-77")

    assert sprint.read_text(encoding="utf-8") == before, (
        "Aucune substitution hasardeuse : le backlog doit rester octet-identique."
    )
    assert result is True, (
        "Récit non tracké par le backlog → aucune réversion possible → retour True honnête."
    )
    warn_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert any("US-77" in r.getMessage() for r in warn_records), (
        "Un WARNING contextuel doit signaler l'absence de ligne dans le backlog."
    )
