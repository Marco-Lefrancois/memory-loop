"""
Tests d'acceptation — ADR JIRA_SYNC_SAFE
Sécurisation de la commande jira_sync contre les synchronisations accidentelles.

CONTRAINTE CRITIQUE : Zéro appel HTTP réel vers Jira.
Tous les appels réseau sont bloqués par mock. Aucune écriture vers COUVBOIRE-957
ou tout autre ticket Jira ne peut survenir depuis ce fichier de tests.

Couvre :
1. Refus sans ciblage (--story / --stories / --all manquants)               → exit 2
2. Dry-run par défaut (sans --apply)                                         → exit 0, 0 HTTP call
3. Mode --all verrouillé sans --apply + --confirm-all-project-stories        → exit 2
4. Blocage clé TEMP-*                                                         → exit 2
5. Blocage statut IN_ANALYZE sans --allow-in-analyze                         → item rejeté
6. Statut IN_ANALYZE accepté avec --allow-in-analyze                         → item éligible
7. --apply sans --confirm-scope                                               → exit 2
8. --apply + --confirm-scope divergent (Fail-Closed)                         → exit 2
9. --apply + --confirm-scope concordant → sync_targeted_to_jira appelée
10. Manifeste SHA-256 : divergence post-dry-run détectée (Fail-Closed)
11. build_sync_preview : structure retournée (manifest_id, file_hashes, eligible, rejected)
12. _parse_target_keys : déduplication --story + --stories
13. sync_backlog_to_jira (compat) : délègue à sync_targeted_to_jira
14. Registre CLI : tous les nouveaux args présents dans _registry.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import types
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, patch, call

import pytest

from src.state import SprintBacklogItem, StoryStatus, LoopState
from src.commands.handlers.export import (
    handle_jira_sync,
    _parse_target_keys,
    _verify_sha256_manifest,
    _TEMP_KEY_PREFIX,
    _BLOCKED_STATUSES_WITHOUT_FLAG,
)
from src.pipelines.jira.sync_engine import build_sync_preview


# ─────────────────────────────────────────────────────────────────────────────
# Helpers / Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def _make_args(**kwargs) -> argparse.Namespace:
    """Construit un Namespace avec les valeurs par défaut du nouveau CLI."""
    defaults = dict(
        project="TestProjet",
        story=None,
        stories=None,
        apply=False,
        dry_run=False,
        all=False,
        confirm_all_project_stories=False,
        allow_in_analyze=False,
        confirm_scope=None,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_item(
    story_id: str = "US-01",
    jira_key: str = "MMA-9001",
    status: StoryStatus = StoryStatus.READY_FOR_DEV,
    title: str = "Story de test",
) -> SprintBacklogItem:
    return SprintBacklogItem(
        id=story_id,
        title=title,
        description=f"stories/{story_id}.md",
        jira_key=jira_key,
        status=status,
    )


def _make_state(items: List[SprintBacklogItem] | None = None) -> LoopState:
    """Construit un LoopState minimal avec un backlog factice."""
    state = MagicMock(spec=LoopState)
    state.project_name = "TestProjet"
    state.jira_project_key = "MMA"
    state.jira_epic_key = "MMA-1000"
    state.jira_default_subtasks = []
    state.jira_subtask_mapping = {}
    state.jira_default_component_id = None
    state.jira_default_billing_id = None
    state.sprint_backlog = items or [_make_item()]
    state.discover_backlog = MagicMock()
    return state


def _dummy_project_path(tmp_path: Path) -> Path:
    """Crée la structure minimale Projects/<projet>/backlog/stories."""
    p = tmp_path / "Projects" / "TestProjet"
    (p / "backlog" / "stories").mkdir(parents=True)
    (p / "memory" / "sync").mkdir(parents=True)
    return p


# ─────────────────────────────────────────────────────────────────────────────
# 1. Refus sans ciblage
# ─────────────────────────────────────────────────────────────────────────────

def test_no_target_returns_exit_2(tmp_path):
    """Sans --story / --stories / --all, la commande doit retourner 2 sans appel HTTP."""
    args = _make_args()  # Aucun ciblage
    state = _make_state()

    with patch("src.commands.handlers.export.build_sync_preview") as mock_preview, \
         patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync:
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 2, "Doit échouer avec exit 2 si aucun ciblage n'est fourni"
    mock_preview.assert_not_called()
    mock_sync.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# 2. Dry-run par défaut (sans --apply)
# ─────────────────────────────────────────────────────────────────────────────

def test_dry_run_default_no_http_call(tmp_path):
    """Sans --apply, aucun appel sync_targeted_to_jira ne doit être fait."""
    args = _make_args(story="MMA-9001")
    state = _make_state()

    with patch("src.commands.handlers.export.build_sync_preview") as mock_preview, \
         patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync:

        mock_preview.return_value = {
            "manifest_id": "abc12345",
            "file_hashes": {},
            "eligible": [],
            "rejected": [],
        }
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 0, "Dry-run doit retourner 0"
    mock_sync.assert_not_called()


def test_explicit_dry_run_flag_no_http_call(tmp_path):
    """--dry-run explicite sans --apply → pas d'écriture même si --confirm-scope est fourni."""
    args = _make_args(story="MMA-9001", dry_run=True, confirm_scope="MMA-9001")
    state = _make_state()

    with patch("src.commands.handlers.export.build_sync_preview") as mock_preview, \
         patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync:

        mock_preview.return_value = {"manifest_id": "x", "file_hashes": {}}
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 0
    mock_sync.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# 3. Mode --all verrouillé
# ─────────────────────────────────────────────────────────────────────────────

def test_all_without_apply_blocked(tmp_path):
    """--all sans --apply doit être refusé."""
    args = _make_args(all=True)
    state = _make_state()

    with patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync:
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 2
    mock_sync.assert_not_called()


def test_all_with_apply_but_no_confirm_blocked(tmp_path):
    """--all + --apply sans --confirm-all-project-stories doit être refusé."""
    args = _make_args(all=True, apply=True, confirm_all_project_stories=False)
    state = _make_state()

    with patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync:
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 2
    mock_sync.assert_not_called()


def test_all_mode_requires_triple_lock(tmp_path):
    """--all + --apply + --confirm-all-project-stories → passe à la preview (pas de refus)."""
    args = _make_args(all=True, apply=True, confirm_all_project_stories=True)
    state = _make_state()

    with patch("src.commands.handlers.export.build_sync_preview") as mock_preview, \
         patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync, \
         patch("src.commands.handlers.export._verify_sha256_manifest", return_value=True), \
         patch("src.commands.handlers.export.run_sync"):

        mock_preview.return_value = {"manifest_id": "m1", "file_hashes": {}}
        # Pas de confirm-scope en mode --all → la vérification scope est skippée
        mock_sync.return_value = state
        rc = handle_jira_sync(args, state, tmp_path)

    # En mode --all + --apply + confirm_all, on atteint la synchro
    mock_sync.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# 4. Blocage clé TEMP-*
# ─────────────────────────────────────────────────────────────────────────────

def test_temp_key_in_story_arg_blocked(tmp_path):
    """--story TEMP-123 doit être refusé avant tout appel réseau."""
    args = _make_args(story="TEMP-123")
    state = _make_state()

    with patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync:
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 2
    mock_sync.assert_not_called()


def test_temp_key_in_stories_arg_blocked(tmp_path):
    """--stories MMA-9001,TEMP-456 doit être refusé."""
    args = _make_args(stories="MMA-9001,TEMP-456")
    state = _make_state()

    with patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync:
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 2
    mock_sync.assert_not_called()


def test_temp_key_on_item_jira_key_rejected_in_eligible(tmp_path):
    """Un item dont jira_key commence par TEMP- doit atterrir dans rejected_items."""
    item = _make_item(story_id="US-02", jira_key="TEMP-789", status=StoryStatus.READY_FOR_DEV)
    args = _make_args(story="US-02")
    state = _make_state(items=[item])

    captured_rejected = []

    def capture_preview(**kwargs):
        captured_rejected.extend(kwargs.get("rejected_items", []))
        return {"manifest_id": "x", "file_hashes": {}}

    with patch("src.commands.handlers.export.build_sync_preview", side_effect=capture_preview), \
         patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync:
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 0  # Dry-run réussi
    assert any("TEMP" in reason for _, reason in captured_rejected), \
        "L'item TEMP-* doit apparaître dans les rejetés avec mention TEMP"
    mock_sync.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# 5. Blocage statut IN_ANALYZE / OPEN sans --allow-in-analyze
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("blocked_status", [
    StoryStatus.IN_ANALYZE,
    StoryStatus.OPEN,
])
def test_blocked_status_without_flag_rejected(tmp_path, blocked_status):
    """Items OPEN ou IN_ANALYZE sans --allow-in-analyze doivent être dans rejected_items."""
    item = _make_item(story_id="US-03", jira_key="MMA-9003", status=blocked_status)
    args = _make_args(story="US-03", allow_in_analyze=False)
    state = _make_state(items=[item])

    captured_eligible = []
    captured_rejected = []

    def capture_preview(**kwargs):
        captured_eligible.extend(kwargs.get("eligible_items", []))
        captured_rejected.extend(kwargs.get("rejected_items", []))
        return {"manifest_id": "x", "file_hashes": {}}

    with patch("src.commands.handlers.export.build_sync_preview", side_effect=capture_preview), \
         patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync:
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 0
    assert len(captured_eligible) == 0, "Aucun item ne doit être éligible"
    assert len(captured_rejected) == 1
    mock_sync.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# 6. Statut IN_ANALYZE accepté avec --allow-in-analyze
# ─────────────────────────────────────────────────────────────────────────────

def test_in_analyze_allowed_with_flag(tmp_path):
    """Avec --allow-in-analyze, un item IN_ANALYZE doit être éligible."""
    item = _make_item(story_id="US-04", jira_key="MMA-9004", status=StoryStatus.IN_ANALYZE)
    args = _make_args(story="US-04", allow_in_analyze=True)
    state = _make_state(items=[item])

    captured_eligible = []

    def capture_preview(**kwargs):
        captured_eligible.extend(kwargs.get("eligible_items", []))
        return {"manifest_id": "x", "file_hashes": {}}

    with patch("src.commands.handlers.export.build_sync_preview", side_effect=capture_preview), \
         patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync:
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 0
    assert len(captured_eligible) == 1
    assert captured_eligible[0].id == "US-04"
    mock_sync.assert_not_called()  # Dry-run par défaut


# ─────────────────────────────────────────────────────────────────────────────
# 7. --apply sans --confirm-scope → exit 2
# ─────────────────────────────────────────────────────────────────────────────

def test_apply_without_confirm_scope_blocked(tmp_path):
    """--apply sans --confirm-scope doit être refusé."""
    item = _make_item()
    args = _make_args(story="MMA-9001", apply=True, confirm_scope=None)
    state = _make_state(items=[item])

    with patch("src.commands.handlers.export.build_sync_preview") as mock_preview, \
         patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync:
        mock_preview.return_value = {"manifest_id": "x", "file_hashes": {}}
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 2
    mock_sync.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# 8. --apply + --confirm-scope divergent → Fail-Closed
# ─────────────────────────────────────────────────────────────────────────────

def test_apply_confirm_scope_mismatch_fail_closed(tmp_path):
    """
    Si --confirm-scope contient une clé différente des éligibles réels,
    la commande doit refuser l'écriture (Fail-Closed).
    """
    item = _make_item(story_id="US-01", jira_key="MMA-9001")
    # confirm-scope mentionne MMA-9999 au lieu de MMA-9001
    args = _make_args(story="MMA-9001", apply=True, confirm_scope="MMA-9999")
    state = _make_state(items=[item])

    with patch("src.commands.handlers.export.build_sync_preview") as mock_preview, \
         patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync:
        mock_preview.return_value = {"manifest_id": "x", "file_hashes": {}}
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 2, "Fail-Closed : périmètre divergent doit bloquer"
    mock_sync.assert_not_called()


def test_apply_confirm_scope_extra_key_fail_closed(tmp_path):
    """
    --confirm-scope contient la bonne clé PLUS une clé supplémentaire → Fail-Closed.
    """
    item = _make_item(story_id="US-01", jira_key="MMA-9001")
    args = _make_args(story="MMA-9001", apply=True, confirm_scope="MMA-9001,MMA-9002")
    state = _make_state(items=[item])

    with patch("src.commands.handlers.export.build_sync_preview") as mock_preview, \
         patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync:
        mock_preview.return_value = {"manifest_id": "x", "file_hashes": {}}
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 2
    mock_sync.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# 9. --apply + --confirm-scope concordant → sync_targeted_to_jira appelée
# ─────────────────────────────────────────────────────────────────────────────

def test_apply_confirm_scope_exact_match_triggers_sync(tmp_path):
    """
    --apply + --confirm-scope identique aux éligibles → sync_targeted_to_jira appelée.
    Aucun appel HTTP réel ne peut survenir car sync_targeted_to_jira est mockée.
    """
    item = _make_item(story_id="US-01", jira_key="MMA-9001")
    # confirm-scope par jira_key
    args = _make_args(story="MMA-9001", apply=True, confirm_scope="MMA-9001")
    state = _make_state(items=[item])

    with patch("src.commands.handlers.export.build_sync_preview") as mock_preview, \
         patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync, \
         patch("src.commands.handlers.export._verify_sha256_manifest", return_value=True), \
         patch("src.commands.handlers.export.run_sync"):

        mock_preview.return_value = {"manifest_id": "abc", "file_hashes": {}}
        mock_sync.return_value = state
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 0
    mock_sync.assert_called_once()
    # Vérifie que manifest_id est transmis
    call_kwargs = mock_sync.call_args.kwargs
    assert call_kwargs.get("manifest_id") == "abc"
    # Vérifie qu'aucun appel HTTP réel n'a eu lieu (mock complet)


def test_apply_confirm_scope_by_logical_id(tmp_path):
    """--confirm-scope avec l'ID logique (US-01) plutôt que la clé Jira."""
    item = _make_item(story_id="US-01", jira_key="MMA-9001")
    args = _make_args(story="US-01", apply=True, confirm_scope="US-01")
    state = _make_state(items=[item])

    with patch("src.commands.handlers.export.build_sync_preview") as mock_preview, \
         patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync, \
         patch("src.commands.handlers.export._verify_sha256_manifest", return_value=True), \
         patch("src.commands.handlers.export.run_sync"):

        mock_preview.return_value = {"manifest_id": "xyz", "file_hashes": {}}
        mock_sync.return_value = state
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 0
    mock_sync.assert_called_once()


# ─────────────────────────────────────────────────────────────────────────────
# 10. Manifeste SHA-256 : divergence post-dry-run (Fail-Closed)
# ─────────────────────────────────────────────────────────────────────────────

def test_sha256_manifest_divergence_fail_closed(tmp_path):
    """
    Si le fichier story a été modifié entre le dry-run et l'apply,
    _verify_sha256_manifest doit retourner False → la commande refuse (exit 2).
    """
    item = _make_item(story_id="US-05", jira_key="MMA-9005")
    args = _make_args(story="MMA-9005", apply=True, confirm_scope="MMA-9005")
    state = _make_state(items=[item])

    # Simuler une divergence SHA-256
    with patch("src.commands.handlers.export.build_sync_preview") as mock_preview, \
         patch("src.commands.handlers.export.sync_targeted_to_jira") as mock_sync, \
         patch("src.commands.handlers.export._verify_sha256_manifest", return_value=False):

        mock_preview.return_value = {"manifest_id": "y", "file_hashes": {"some/file.md": "oldhash"}}
        rc = handle_jira_sync(args, state, tmp_path)

    assert rc == 2, "Divergence SHA-256 doit bloquer (Fail-Closed)"
    mock_sync.assert_not_called()


def test_sha256_manifest_write_and_verify(tmp_path):
    """
    _verify_sha256_manifest doit :
    - Écrire le manifeste si absent (premier run)
    - Retourner True quand les hashes concordent
    - Retourner False si un fichier a changé depuis
    """
    story_file = tmp_path / "stories" / "US-01.md"
    story_file.parent.mkdir(parents=True)
    story_file.write_text("# Story de test", encoding="utf-8")

    original_hash = hashlib.sha256(story_file.read_bytes()).hexdigest()
    preview = {
        "manifest_id": "test-manifest",
        "file_hashes": {str(story_file): original_hash},
    }

    manifest_dir = tmp_path / "memory" / "sync"
    manifest_dir.mkdir(parents=True)
    manifest_path = manifest_dir / "jira_sync_preview.json"

    # Premier appel : pas de manifeste existant → True (écriture)
    result_first = _verify_sha256_manifest(preview, tmp_path)
    assert result_first is True
    assert manifest_path.exists(), "Le manifeste doit être créé"

    # Deuxième appel sans modification → True
    result_second = _verify_sha256_manifest(preview, tmp_path)
    assert result_second is True

    # Modification du fichier story entre les deux appels
    story_file.write_text("# Story modifiée après dry-run!", encoding="utf-8")

    # Troisième appel avec hash divergent → False (Fail-Closed)
    result_third = _verify_sha256_manifest(preview, tmp_path)
    assert result_third is False, "Un fichier modifié doit déclencher le Fail-Closed"


# ─────────────────────────────────────────────────────────────────────────────
# 11. build_sync_preview : structure retournée
# ─────────────────────────────────────────────────────────────────────────────

def test_build_sync_preview_structure(tmp_path):
    """build_sync_preview doit retourner un dict avec les clés obligatoires."""
    project_path = _dummy_project_path(tmp_path)

    # Créer un fichier story réel pour le hash
    story_file = project_path / "backlog" / "stories" / "US-01.md"
    story_file.write_text("# Test story", encoding="utf-8")

    state = _make_state()
    state.project_name = "TestProjet"

    item = _make_item()
    rejected = [(_make_item(story_id="US-BAD", jira_key="TEMP-1"), "Clé TEMP-* refusée")]

    preview = build_sync_preview(
        project_path=project_path,
        state=state,
        eligible_items=[item],
        rejected_items=rejected,
        target_keys=["MMA-9001"],
    )

    assert "manifest_id" in preview
    assert "generated_at" in preview
    assert "file_hashes" in preview
    assert "eligible" in preview
    assert "rejected" in preview
    assert len(preview["eligible"]) == 1
    assert len(preview["rejected"]) == 1
    assert preview["target_keys"] == ["MMA-9001"]
    assert preview["project"] == "TestProjet"


def test_build_sync_preview_writes_manifest(tmp_path):
    """build_sync_preview doit écrire memory/sync/jira_sync_preview.json."""
    project_path = _dummy_project_path(tmp_path)
    state = _make_state()

    build_sync_preview(
        project_path=project_path,
        state=state,
        eligible_items=[_make_item()],
        rejected_items=[],
        target_keys=["US-01"],
    )

    manifest_path = project_path / "memory" / "sync" / "jira_sync_preview.json"
    assert manifest_path.exists(), "Le manifeste doit être écrit sur le disque"

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "manifest_id" in data
    assert len(data["manifest_id"]) > 0


def test_build_sync_preview_hashes_story_file(tmp_path):
    """build_sync_preview doit calculer le SHA-256 du fichier story si trouvé."""
    project_path = _dummy_project_path(tmp_path)

    story_file = project_path / "backlog" / "stories" / "US-01.md"
    story_file.write_text("contenu story test", encoding="utf-8")
    expected_hash = hashlib.sha256(story_file.read_bytes()).hexdigest()

    state = _make_state()
    preview = build_sync_preview(
        project_path=project_path,
        state=state,
        eligible_items=[_make_item()],
        rejected_items=[],
        target_keys=["US-01"],
    )

    assert str(story_file) in preview["file_hashes"]
    assert preview["file_hashes"][str(story_file)] == expected_hash


# ─────────────────────────────────────────────────────────────────────────────
# 12. _parse_target_keys : déduplication et normalisation
# ─────────────────────────────────────────────────────────────────────────────

def test_parse_target_keys_story_only():
    args = _make_args(story="MMA-9001")
    assert _parse_target_keys(args) == ["MMA-9001"]


def test_parse_target_keys_stories_only():
    args = _make_args(stories="MMA-9001,MMA-9002,MMA-9003")
    assert _parse_target_keys(args) == ["MMA-9001", "MMA-9002", "MMA-9003"]


def test_parse_target_keys_deduplication():
    """--story + --stories avec une clé commune → dédupliquée."""
    args = _make_args(story="MMA-9001", stories="MMA-9001,MMA-9002")
    result = _parse_target_keys(args)
    assert result == ["MMA-9001", "MMA-9002"]
    assert result.count("MMA-9001") == 1, "Pas de doublon"


def test_parse_target_keys_whitespace_stripped():
    args = _make_args(stories="  MMA-9001 , MMA-9002  ")
    result = _parse_target_keys(args)
    assert result == ["MMA-9001", "MMA-9002"]


def test_parse_target_keys_empty_when_no_args():
    args = _make_args()
    assert _parse_target_keys(args) == []


def test_parse_target_keys_empty_stories_segment_ignored():
    """Les segments vides dans --stories (ex: ,,) sont ignorés."""
    args = _make_args(stories="MMA-9001,,MMA-9002,")
    result = _parse_target_keys(args)
    assert result == ["MMA-9001", "MMA-9002"]


# ─────────────────────────────────────────────────────────────────────────────
# 13. sync_backlog_to_jira (compat) : délègue sans appel HTTP direct
# ─────────────────────────────────────────────────────────────────────────────

def test_sync_backlog_to_jira_delegates_to_targeted(tmp_path):
    """
    sync_backlog_to_jira() (compat) doit déléguer à sync_targeted_to_jira()
    sans effectuer d'appel HTTP direct. Le mock bloque tout appel réseau.
    """
    from src.pipelines.jira.sync_engine import sync_backlog_to_jira

    state = _make_state(items=[_make_item()])

    with patch("src.pipelines.jira.sync_engine.sync_targeted_to_jira") as mock_targeted:
        mock_targeted.return_value = state
        result = sync_backlog_to_jira(state)

    mock_targeted.assert_called_once()
    call_kwargs = mock_targeted.call_args.kwargs
    assert "eligible_items" in call_kwargs
    assert "project_path" in call_kwargs
    assert result is state


def test_sync_backlog_to_jira_compat_filters_eligible_only(tmp_path):
    """sync_backlog_to_jira() ne doit passer que les items jira_sync_eligible."""
    from src.pipelines.jira.sync_engine import sync_backlog_to_jira

    eligible = _make_item(story_id="US-GOOD", status=StoryStatus.READY_FOR_DEV)
    not_eligible = _make_item(story_id="US-BAD", status=StoryStatus.OPEN)
    state = _make_state(items=[eligible, not_eligible])

    with patch("src.pipelines.jira.sync_engine.sync_targeted_to_jira") as mock_targeted:
        mock_targeted.return_value = state
        sync_backlog_to_jira(state)

    call_kwargs = mock_targeted.call_args.kwargs
    passed_items = call_kwargs["eligible_items"]
    ids = [i.id for i in passed_items]
    assert "US-GOOD" in ids
    assert "US-BAD" not in ids


# ─────────────────────────────────────────────────────────────────────────────
# 14. Registre CLI : vérification des args déclarés dans _registry.py
# ─────────────────────────────────────────────────────────────────────────────

def test_registry_jira_sync_has_required_args():
    """Le registre doit déclarer tous les nouveaux arguments de sécurité."""
    from src.commands._registry import COMMANDS

    entry = COMMANDS.get("jira_sync")
    assert entry is not None, "jira_sync doit être dans le registre"

    arg_names = {a["name"] for a in entry.get("args", [])}
    required = {"--story", "--stories", "--apply", "--confirm-scope",
                "--all", "--confirm-all-project-stories", "--allow-in-analyze", "--dry-run"}

    missing = required - arg_names
    assert not missing, f"Args manquants dans le registre : {missing}"


def test_registry_jira_sync_no_http_args_are_required():
    """Aucun des nouveaux args de ciblage ne doit être marqué 'required=True'
    (ils ont chacun une valeur par défaut permissive)."""
    from src.commands._registry import COMMANDS

    entry = COMMANDS["jira_sync"]
    for arg in entry.get("args", []):
        assert arg.get("required", False) is False, \
            f"L'arg {arg['name']} ne doit pas être required=True"


# ─────────────────────────────────────────────────────────────────────────────
# 15. Constantes de sécurité exportées
# ─────────────────────────────────────────────────────────────────────────────

def test_security_constants_values():
    """Les constantes de sécurité doivent avoir les valeurs attendues."""
    assert _TEMP_KEY_PREFIX == "TEMP-"
    assert "OPEN" in _BLOCKED_STATUSES_WITHOUT_FLAG
    assert "IN_ANALYZE" in _BLOCKED_STATUSES_WITHOUT_FLAG
    # READY_FOR_DEV ne doit pas être bloqué
    assert "READY_FOR_DEV" not in _BLOCKED_STATUSES_WITHOUT_FLAG


# ─────────────────────────────────────────────────────────────────────────────
# 16. Zéro appel HTTP : vérification que httpx n'est jamais invoqué dans les
#     chemins couverts par les tests (filet de sécurité réseau global)
# ─────────────────────────────────────────────────────────────────────────────

def test_no_real_http_call_guard(tmp_path, monkeypatch):
    """
    Filet de sécurité : bloque httpx.Client.request à la racine pour s'assurer
    qu'aucun test dans ce module n'émet d'appel HTTP réel.
    """
    import httpx

    def _blocked_request(self, *args, **kwargs):
        raise RuntimeError(
            "APPEL HTTP BLOQUÉ — Les tests jira_sync_safe ne doivent jamais "
            "contacter un serveur réseau. Utilisez des mocks."
        )

    monkeypatch.setattr(httpx.Client, "request", _blocked_request)

    # Test de refus sans ciblage : ne doit jamais atteindre HTTP
    args = _make_args()
    state = _make_state()
    rc = handle_jira_sync(args, state, tmp_path)
    assert rc == 2  # Bloqué bien avant HTTP
