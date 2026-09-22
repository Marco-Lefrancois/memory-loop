"""
Sous-module Jira : jira_story_resolver.py
Responsabilité : Résolution des clés Jira et enrichissement des métadonnées story/epic.
"""

import re
import httpx
from src.state import SprintBacklogItem
from src.pipelines.jira.jira_helpers import is_jira_status_closed
from src.utils.logger import get_logger

logger = get_logger("pipelines.jira.jira_story_resolver")


def resolve_story_key(
    client: httpx.Client,
    rich_description: str,
    global_epic_key: str,
    existing_stories_map: dict,
    item: SprintBacklogItem,
):
    """Résout la clé Jira existante ou forcée pour un récit donné."""
    key_match = re.search(r"jira_key:\s*([A-Z0-9-]+)", rich_description)
    forced_key = key_match.group(1) if key_match else None

    if forced_key and (
        forced_key.endswith("-XXX")
        or "TBD" in forced_key.upper()
        or forced_key.upper().startswith("TEMP-")
    ):
        forced_key = None
    elif forced_key:
        try:
            r_chk = client.get(f"/rest/api/3/issue/{forced_key}?fields=issuetype")
            if r_chk.status_code == 200:
                itype = r_chk.json().get("fields", {}).get("issuetype", {})
                if itype.get("subtask", False):
                    forced_key = None
        except Exception as e:
            logger.debug(
                "Vérification du type d'issue pour la clé forcée échouée, clé conservée",
                exc_info=True,
                extra={
                    "component": "pipelines.jira.jira_story_resolver",
                    "operation": "forced_key_issuetype_check",
                    "forced_key": forced_key,
                    "error": str(e),
                },
            )

    epic_match = re.search(r"epic_key:\s*([A-Z0-9-]+)", rich_description)
    story_epic_key = epic_match.group(1) if epic_match else global_epic_key

    already_exists = (forced_key is not None) or (item.id in existing_stories_map)
    story_key = (
        forced_key
        if forced_key
        else (existing_stories_map.get(item.id, {}).get("key") if already_exists else None)
    )
    return story_key, story_epic_key, already_exists


def enrich_components_from_existing(
    client: httpx.Client,
    story_key: str,
    story_epic_key: str,
    current_billing_id: str,
    current_components: list,
):
    """Enrichit billing_id et components depuis la story ou l'epic existante."""
    if story_key:
        try:
            r_existing = client.get(f"/rest/api/3/issue/{story_key}")
            if r_existing.status_code == 200:
                e_fields = r_existing.json().get("fields", {})
                e_status = e_fields.get("status", {})
                s_name = e_status.get("name", "")
                s_cat = e_status.get("statusCategory", {}).get("key", "")
                if is_jira_status_closed(s_name, s_cat):
                    return s_name, "CLOSED", current_billing_id, current_components
                if not current_components:
                    epic_comps = e_fields.get("components", [])
                    if epic_comps:
                        current_components = [
                            {"id": c["id"]} if "id" in c else {"name": c["name"]}
                            for c in epic_comps
                        ]
                if not current_billing_id:
                    b_f = e_fields.get("customfield_10151")
                    if isinstance(b_f, dict):
                        current_billing_id = b_f.get("id")
                    elif b_f:
                        current_billing_id = str(b_f)
        except Exception as e:
            logger.warning(
                "Enrichissement depuis la story Jira existante échoué, valeurs inchangées",
                exc_info=True,
                extra={
                    "component": "pipelines.jira.jira_story_resolver",
                    "operation": "enrich_components_from_existing",
                    "story_key": story_key,
                    "error": str(e),
                },
            )

    if story_epic_key and (not current_billing_id or not current_components):
        try:
            r_epic = client.get(f"/rest/api/3/issue/{story_epic_key}")
            if r_epic.status_code == 200:
                e_f = r_epic.json().get("fields", {})
                if not current_billing_id:
                    b_f = e_f.get("customfield_10151")
                    if isinstance(b_f, dict):
                        current_billing_id = b_f.get("id")
                    elif b_f:
                        current_billing_id = str(b_f)
                if not current_components:
                    epic_comps = e_f.get("components", [])
                    if epic_comps:
                        current_components = [
                            {"id": c["id"]} if "id" in c else {"name": c["name"]}
                            for c in epic_comps
                        ]
        except Exception as e:
            logger.warning(
                "Enrichissement depuis l'epic Jira échoué, valeurs inchangées",
                exc_info=True,
                extra={
                    "component": "pipelines.jira.jira_story_resolver",
                    "operation": "enrich_components_from_epic",
                    "story_epic_key": story_epic_key,
                    "error": str(e),
                },
            )

    return None, None, current_billing_id, current_components
