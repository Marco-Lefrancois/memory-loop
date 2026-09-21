"""
Sous-module Jira : jira_item_sync.py
Responsabilité : Synchronisation individuelle d'un récit vers Jira Cloud.
"""

import os
import httpx
from pathlib import Path
from src.state import LoopState, SprintBacklogItem
from src.cli import ZeroFluffConsole
from src.pipelines.jira.md_cleaner import load_rich_description, clean_markdown_description
from src.pipelines.jira.adf_converter import markdown_to_adf
from src.pipelines.jira.jira_helpers import (
    _clean_title,
    _clean_adf_description,
    is_jira_status_closed,
)
from src.pipelines.jira.jira_subtasks import sync_subtasks_for_story
from src.pipelines.jira.jira_story_creator import create_new_story
from src.pipelines.jira.jira_story_resolver import (
    resolve_story_key,
    enrich_components_from_existing,
)


def _update_existing_story(
    client: httpx.Client,
    story_key: str,
    clean_story_title: str,
    adf_description: dict,
    story_epic_key: str,
    subtasks_to_sync: list,
    item: SprintBacklogItem,
    state: LoopState,
    allowed_subtasks: dict,
    actions_log: list,
    current_billing_id: str,
    current_components: list,
    manifest_id: str,
):
    """Met à jour une story existante et ses sous-tâches."""
    try:
        update_payload = {"fields": {"summary": clean_story_title, "description": adf_description}}
        r_update = client.put(f"/rest/api/3/issue/{story_key}", json=update_payload)
        try:
            struct_payload = {"fields": {"issuetype": {"name": "Story"}}}
            if story_epic_key:
                struct_payload["fields"]["parent"] = {"key": story_epic_key}
            client.put(f"/rest/api/3/issue/{story_key}", json=struct_payload)
        except Exception:
            pass

        if r_update.status_code in [200, 204]:
            actions_log.append(
                {
                    "type": "Story",
                    "id": story_key,
                    "title": clean_story_title,
                    "action": "MAJ",
                    "details": f"Synchronisation réussie (manifeste {manifest_id})",
                }
            )
            sync_subtasks_for_story(
                client,
                story_key,
                item.title,
                subtasks_to_sync,
                state.jira_project_key,
                allowed_subtasks,
                actions_log,
                current_billing_id,
                current_components,
                state,
            )
        else:
            actions_log.append(
                {
                    "type": "Story",
                    "id": story_key,
                    "title": clean_story_title,
                    "action": "ECHEC",
                    "details": f"Erreur {r_update.status_code}: {r_update.text[:80]}",
                }
            )
    except Exception as e:
        actions_log.append(
            {
                "type": "Story",
                "id": story_key,
                "title": clean_story_title,
                "action": "ECHEC",
                "details": str(e),
            }
        )


def sync_single_item(
    client: httpx.Client,
    item: SprintBacklogItem,
    project_path: Path,
    state: LoopState,
    existing_stories_map: dict,
    allowed_subtasks: dict,
    global_epic_key: str,
    billing_id: str,
    components_payload: list,
    actions_log: list,
    manifest_id: str,
    jira_cache: dict,
) -> bool:
    """Synchronise un seul récit vers Jira. Retourne True si traité, False si skippé."""
    story_files = list((project_path / "backlog" / "stories").rglob(f"*{item.id}*.md"))
    story_file_path = story_files[0] if story_files else None
    mtime = os.path.getmtime(story_file_path) if story_file_path and story_file_path.exists() else 0

    cached_item = jira_cache.get(item.id, {})
    if (
        mtime > 0
        and cached_item.get("mtime") == mtime
        and cached_item.get("status") == getattr(item, "status", None)
        and cached_item.get("jira_key")
    ):
        actions_log.append(
            {
                "type": "Story",
                "id": cached_item["jira_key"],
                "title": item.title,
                "action": "INCHANGEE",
                "details": "Synchronisation sautée (Cache Hit mtime)",
            }
        )
        return False

    rich_description = load_rich_description(project_path, item.description, item.description)
    story_key, story_epic_key, already_exists = resolve_story_key(
        client, rich_description, global_epic_key, existing_stories_map, item
    )

    current_billing_id = billing_id
    current_components = components_payload[:]

    if already_exists and item.id in existing_stories_map:
        map_entry = existing_stories_map[item.id]
        if is_jira_status_closed(
            map_entry.get("status", ""),
            map_entry.get("status_category", ""),
        ):
            s_name = map_entry.get("status", "Fermé")
            ZeroFluffConsole.warning(
                f"🔒 Story {story_key} ({item.id}) est au statut FERMÉ "
                f"('{s_name}') dans Jira — synchronisation strictement ignorée "
                f"(règle constitutionnelle)."
            )
            actions_log.append(
                {
                    "type": "Story",
                    "id": story_key or map_entry.get("key"),
                    "title": _clean_title(item.title),
                    "action": "IGNORE_FERME",
                    "details": (
                        f"Statut Jira '{s_name}' (FERMÉ) — "
                        f"synchronisation interdite (règle constitutionnelle)"
                    ),
                }
            )
            return False

    status_name, status_action, current_billing_id, current_components = (
        enrich_components_from_existing(
            client,
            story_key,
            story_epic_key,
            current_billing_id,
            current_components,
        )
    )
    if status_action == "CLOSED":
        ZeroFluffConsole.warning(
            f"🔒 Story {story_key} ({item.id}) est au statut FERMÉ "
            f"('{status_name}') dans Jira — synchronisation strictement ignorée "
            f"(règle constitutionnelle)."
        )
        actions_log.append(
            {
                "type": "Story",
                "id": story_key,
                "title": _clean_title(item.title),
                "action": "IGNORE_FERME",
                "details": (
                    f"Statut Jira '{status_name}' (FERMÉ) — "
                    f"synchronisation interdite (règle constitutionnelle)"
                ),
            }
        )
        return False

    description_no_title = _clean_adf_description(rich_description)
    cleaned_description = clean_markdown_description(description_no_title)
    adf_description = markdown_to_adf(cleaned_description)

    subtasks_to_sync = (
        state.jira_default_subtasks
        if state.jira_default_subtasks
        else [
            "- Analyse",
            "- Architecture de solutions",
            "- Programmation applicative mobile",
            "- Assurance qualité",
        ]
    )
    clean_story_title = _clean_title(item.title)

    if already_exists and story_key:
        _update_existing_story(
            client,
            story_key,
            clean_story_title,
            adf_description,
            story_epic_key,
            subtasks_to_sync,
            item,
            state,
            allowed_subtasks,
            actions_log,
            current_billing_id,
            current_components,
            manifest_id,
        )
    else:
        create_new_story(
            client,
            item,
            clean_story_title,
            adf_description,
            story_epic_key,
            subtasks_to_sync,
            state,
            allowed_subtasks,
            project_path,
            actions_log,
            current_billing_id,
            current_components,
            manifest_id,
        )
    return True
