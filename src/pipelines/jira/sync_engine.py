"""
Sous-module Jira : sync_engine.py
Responsabilité : Point d'entrée de synchronisation du backlog local vers Jira Cloud.
Délègue la logique métier aux sous-modules jira_helpers.py, jira_report.py,
jira_subtasks.py et jira_item_sync.py.

Sécurité (ADR JIRA_SYNC_SAFE) :
- La fonction publique principale est sync_targeted_to_jira() (périmètre explicite).
- build_sync_preview() génère le manifeste SHA-256 et le rapport dry-run.
- sync_backlog_to_jira() est maintenue pour la compatibilité ascendante uniquement.
"""

import hashlib
import logging
import os
import uuid
import httpx
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from src.state import LoopState, SprintBacklogItem
from src.cli import ZeroFluffConsole

logger = logging.getLogger(__name__)
from src.pipelines.jira.jira_helpers import (
    _fetch_allowed_subtask_types,
    _validate_subtasks_mapping,
    _fetch_existing_stories,
    is_jira_status_closed,
)
from src.pipelines.jira.jira_item_sync import sync_single_item
from src.pipelines.jira.jira_report import _print_audit_report, _write_markdown_report


def build_sync_preview(
    project_path: Path,
    state: LoopState,
    eligible_items: List[SprintBacklogItem],
    rejected_items: list,
    target_keys: List[str],
) -> dict:
    """
    Construit le manifeste de prévisualisation (dry-run) et calcule les SHA-256
    de chaque fichier story éligible. Écrit le manifeste sous memory/sync/jira_sync_preview.json.
    """
    run_ts = datetime.now().isoformat()
    manifest_id = str(uuid.uuid4())[:8]
    file_hashes: dict = {}
    stories_dir = project_path / "backlog" / "stories"

    for item in eligible_items:
        candidates = list(stories_dir.rglob(f"*{item.id}*.md"))
        if not candidates:
            jk = getattr(item, "jira_key", None) or ""
            if jk:
                candidates = list(stories_dir.rglob(f"*{jk}*.md"))
        if candidates:
            try:
                file_hashes[str(candidates[0])] = hashlib.sha256(
                    candidates[0].read_bytes()
                ).hexdigest()
            except Exception:
                logger.warning(
                    "jira.sync.preview.hash_failed",
                    extra={
                        "manifest_id": manifest_id,
                        "story_id": item.id,
                        "story_path": str(candidates[0]),
                    },
                    exc_info=True,
                )

    preview = {
        "manifest_id": manifest_id,
        "generated_at": run_ts,
        "project": state.project_name,
        "target_keys": target_keys,
        "eligible": [
            {
                "id": i.id,
                "jira_key": getattr(i, "jira_key", None) or "",
                "title": i.title,
                "status": getattr(i.status, "value", str(i.status)),
            }
            for i in eligible_items
        ],
        "rejected": [
            {
                "id": i.id,
                "jira_key": getattr(i, "jira_key", None) or "",
                "reason": reason,
            }
            for i, reason in rejected_items
        ],
        "file_hashes": file_hashes,
    }

    manifest_path = project_path / "memory" / "sync" / "jira_sync_preview.json"
    try:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(preview, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except Exception as e:
        ZeroFluffConsole.warning(f"Impossible d'écrire le manifeste SHA-256 : {e}")
        logger.error(
            "jira.sync.preview.manifest_write_failed",
            extra={
                "manifest_id": manifest_id,
                "target_keys": target_keys,
                "eligible_count": len(eligible_items),
                "dry_run": True,
                "apply_mode": False,
            },
            exc_info=True,
        )

    return preview


def sync_targeted_to_jira(
    state: LoopState,
    project_path: Path,
    eligible_items: List[SprintBacklogItem],
    manifest_id: str = "",
) -> Optional[LoopState]:
    """
    Synchronise uniquement les items de la liste `eligible_items` vers Jira.
    Point d'entrée sécurisé ; toutes les gardes sont vérifiées par handle_jira_sync().
    """
    ZeroFluffConsole.step_s2(
        "Scrum Master",
        f"Synchronisation ciblée vers Jira ({len(eligible_items)} story(s), manifeste={manifest_id})...",
    )

    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")

    if not all([jira_url, jira_email, jira_token]):
        ZeroFluffConsole.error("Identifiants Jira manquants dans le fichier .env.")
        logger.error(
            "jira.sync.config_missing",
            extra={"config_missing": True, "manifest_id": manifest_id},
        )
        return None

    auth = (jira_email, jira_token)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Accept-Encoding": "gzip, deflate",
    }

    with httpx.Client(base_url=jira_url, auth=auth, headers=headers, timeout=30.0) as client:
        if state.jira_default_component_id:
            if str(state.jira_default_component_id).isdigit():
                components_payload = [{"id": str(state.jira_default_component_id)}]
            else:
                components_payload = [{"name": str(state.jira_default_component_id)}]
        else:
            components_payload = []

        billing_id = state.jira_default_billing_id
        global_epic_key = state.jira_epic_key

        allowed_subtasks = _fetch_allowed_subtask_types(client, state.jira_project_key)
        _validate_subtasks_mapping(state, allowed_subtasks, project_path)
        existing_stories_map = _fetch_existing_stories(client, state)

        cache_dir = project_path / "memory" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "jira_sync_cache.json"
        jira_cache: dict = {}
        if cache_file.exists():
            try:
                jira_cache = json.loads(cache_file.read_text(encoding="utf-8"))
            except Exception:
                logger.warning(
                    "jira.sync.cache_read_failed",
                    extra={"manifest_id": manifest_id, "cache_file": str(cache_file)},
                    exc_info=True,
                )

        actions_log: list = []
        if global_epic_key:
            actions_log.append(
                {
                    "type": "Epic",
                    "id": global_epic_key,
                    "title": "Epic de rattachement",
                    "action": "RATTACHEE",
                    "details": f"Liaison active sous {global_epic_key}",
                }
            )

        for item in eligible_items:
            sync_single_item(
                client,
                item,
                project_path,
                state,
                existing_stories_map,
                allowed_subtasks,
                global_epic_key,
                billing_id,
                components_payload,
                actions_log,
                manifest_id,
                jira_cache,
            )

        try:
            for act in actions_log:
                if (
                    act.get("action") in ("CREEE", "MISE_A_JOUR", "MAJ", "EXISTE", "INCHANGEE")
                    and act.get("id")
                    and act["id"] != "-"
                ):
                    for item in eligible_items:
                        if item.id in act["title"] or act["id"] in getattr(item, "jira_key", ""):
                            story_files = list(
                                (project_path / "backlog" / "stories").rglob(f"*{item.id}*.md")
                            )
                            if story_files and story_files[0].exists():
                                jira_cache[item.id] = {
                                    "mtime": os.path.getmtime(story_files[0]),
                                    "jira_key": act["id"],
                                    "status": getattr(item, "status", None),
                                }
            cache_file.write_text(
                json.dumps(jira_cache, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            logger.warning(
                "jira.sync.cache_write_failed",
                extra={
                    "manifest_id": manifest_id,
                    "eligible_count": len(eligible_items),
                    "cache_file": str(cache_file),
                },
                exc_info=True,
            )

        _print_audit_report(actions_log)
        _write_markdown_report(project_path, state.project_name, actions_log)

    return state


def sync_backlog_to_jira(state: LoopState) -> LoopState:
    """
    Point d'entrée de compatibilité ascendante (conservé pour les appels internes).
    Délègue à sync_targeted_to_jira() avec la liste complète des éligibles.
    """
    ZeroFluffConsole.warning(
        "[COMPAT] sync_backlog_to_jira() est appelée en mode rétro-compatibilité.\n"
        "  Pour une synchronisation sécurisée, utilisez la CLI :\n"
        "  python src/swarm.py jira_sync --project <P> --story <CLE>"
    )
    logger.warning(
        "jira.sync.compat_entrypoint",
        extra={"apply_mode": False, "dry_run": True, "manifest_id": "compat"},
    )
    project_path = Path(r"C:\Memory Loop\Projects") / state.project_name
    state.discover_backlog(project_path)

    eligible_items = [
        item for item in state.sprint_backlog if getattr(item, "jira_sync_eligible", item.grilled)
    ]
    result = sync_targeted_to_jira(
        state=state,
        project_path=project_path,
        eligible_items=eligible_items,
        manifest_id="compat",
    )
    return result if result is not None else state
