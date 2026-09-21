"""
Sous-module Jira : jira_subtasks.py
Responsabilité : Logique de création et synchronisation des sous-tâches Jira.
"""

import re
import httpx
from src.state import LoopState
from src.cli import ZeroFluffConsole
from src.pipelines.jira.jira_helpers import (
    SUBTASK_TYPE_VARIATIONS,
    _clean_title,
    _get_subtask_type_id,
    _fetch_existing_subtask_data,
)


def _create_subtask(
    client: httpx.Client,
    sub_name: str,
    parent_key: str,
    parent_title: str,
    project_key: str,
    allowed_subtasks: dict,
    actions_log: list,
    billing_id: str,
    components_payload: list,
    state: LoopState,
):
    """Crée une sous-tâche Jira avec payload résilient et fallback automatique."""
    clean_st_title = _clean_title(parent_title)
    full_summary = f"{sub_name} - {clean_st_title}"
    matched_issuetype = _get_subtask_type_id(sub_name, allowed_subtasks, state)

    sub_payload = {
        "fields": {
            "project": {"key": project_key},
            "parent": {"key": parent_key},
            "summary": full_summary,
            "issuetype": matched_issuetype,
        }
    }
    if components_payload:
        sub_payload["fields"]["components"] = components_payload
    if billing_id:
        sub_payload["fields"]["customfield_10151"] = {"id": billing_id}

    try:
        r_sub = client.post("/rest/api/3/issue", json=sub_payload)
        if r_sub.status_code == 201:
            created_sub = r_sub.json()
            actions_log.append(
                {
                    "type": "  Sub-task",
                    "id": created_sub.get("key", "-"),
                    "title": sub_name,
                    "action": "CREEE",
                    "details": f"Sous-tache de {parent_key}",
                }
            )
            return

        if r_sub.status_code in [400, 422]:
            minimal_payload = {
                "fields": {
                    "project": {"key": project_key},
                    "parent": {"key": parent_key},
                    "summary": full_summary,
                    "issuetype": matched_issuetype,
                }
            }
            r_fallback = client.post("/rest/api/3/issue", json=minimal_payload)
            if r_fallback.status_code == 201:
                created_sub = r_fallback.json()
                actions_log.append(
                    {
                        "type": "  Sub-task",
                        "id": created_sub.get("key", "-"),
                        "title": sub_name,
                        "action": "CREEE",
                        "details": f"Sous-tache de {parent_key} (payload minimal)",
                    }
                )
                return
            else:
                actions_log.append(
                    {
                        "type": "  Sub-task",
                        "id": "-",
                        "title": sub_name,
                        "action": "ECHEC",
                        "details": f"Erreur fallback: {r_fallback.text[:80]}",
                    }
                )
        else:
            actions_log.append(
                {
                    "type": "  Sub-task",
                    "id": "-",
                    "title": sub_name,
                    "action": "ECHEC",
                    "details": f"Erreur: {r_sub.text[:80]}",
                }
            )
    except Exception as e:
        actions_log.append(
            {
                "type": "  Sub-task",
                "id": "-",
                "title": sub_name,
                "action": "ECHEC",
                "details": f"Exception: {str(e)[:60]}",
            }
        )


def sync_subtasks_for_story(
    client: httpx.Client,
    story_key: str,
    story_title: str,
    subtasks_to_sync: list,
    project_key: str,
    allowed_subtasks: dict,
    actions_log: list,
    billing_id: str,
    components_payload: list,
    state: LoopState,
):
    """Synchronise les sous-tâches d'une story existante (mise à jour ou création)."""
    clean_story_title = _clean_title(story_title)
    existing_sub_data = _fetch_existing_subtask_data(client, story_key)

    for comp in subtasks_to_sync:
        expected_summary = f"{comp} - {clean_story_title}"
        found_key = None
        found_summary = ""
        comp_lower = comp.lower()

        intent_variations = []
        for target, vars in SUBTASK_TYPE_VARIATIONS.items():
            if target in comp_lower:
                intent_variations = vars
                break
        if not intent_variations:
            intent_variations = [comp_lower]

        for s_summary, s_key in existing_sub_data.items():
            for var in intent_variations:
                if var in s_summary:
                    found_key = s_key
                    found_summary = s_summary
                    break
            if found_key:
                break

        if found_key:
            if found_summary != expected_summary.lower():
                try:
                    r_sub_up = client.put(
                        f"/rest/api/3/issue/{found_key}",
                        json={"fields": {"summary": expected_summary}},
                    )
                    if r_sub_up.status_code in [200, 204]:
                        actions_log.append(
                            {
                                "type": "  Sub-task",
                                "id": found_key,
                                "title": comp,
                                "action": "MAJ",
                                "details": "Titre synchronisé",
                            }
                        )
                    else:
                        actions_log.append(
                            {
                                "type": "  Sub-task",
                                "id": found_key,
                                "title": comp,
                                "action": "ECHEC",
                                "details": f"MAJ {r_sub_up.status_code}",
                            }
                        )
                except Exception:
                    actions_log.append(
                        {
                            "type": "  Sub-task",
                            "id": found_key,
                            "title": comp,
                            "action": "IGNORE",
                            "details": "Déjà présente",
                        }
                    )
            else:
                actions_log.append(
                    {
                        "type": "  Sub-task",
                        "id": found_key,
                        "title": comp,
                        "action": "IGNORE",
                        "details": "Déjà présente",
                    }
                )
        else:
            _create_subtask(
                client,
                comp,
                story_key,
                story_title,
                project_key,
                allowed_subtasks,
                actions_log,
                billing_id,
                components_payload,
                state,
            )
