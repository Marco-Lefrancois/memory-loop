"""
Sous-module Jira : jira_helpers.py
Responsabilité : Types d'erreur, constantes de mapping et fonctions utilitaires
pour l'interaction avec l'API Jira Cloud.
"""

import re
import httpx
from pathlib import Path
from src.state import LoopState
from src.utils.logger import get_logger

logger = get_logger("pipelines.jira.jira_helpers")


class JiraMappingRequiredError(Exception):
    def __init__(self, missing_subtasks: list, allowed_subtasks: dict):
        self.missing_subtasks = missing_subtasks
        self.allowed_subtasks = allowed_subtasks

        types_info = []
        for v in sorted(allowed_subtasks.values(), key=lambda x: x["name"]):
            types_info.append(f"  - {v['name']} (ID: {v['id']})")
        options_str = "\n".join(types_info)

        msg = (
            f"ACTION REQUIRED: The following subtask types are not mapped: {missing_subtasks}\n"
            f"Please configure them in LoopState (jira_subtask_mapping).\n"
            f"Available Jira issue types:\n{options_str}"
        )
        super().__init__(msg)


SUBTASK_TYPE_VARIATIONS = {
    "analyse": ["analyse", "analysis", "architecture"],
    "développement": ["développement", "developpement", "development", "programmation"],
    "test": ["assurance qualité", "assurance qualite", "qa", "test"],
    "assurance": ["assurance qualité", "assurance qualite", "qa", "test"],
    "déploiement": ["déploiement", "deploiement", "deployment"],
}


def _clean_title(title: str) -> str:
    """Nettoie le titre du markdown (retire les '# ' et les tags/préfixes)."""
    t = title.replace("# ", "").strip()
    return re.sub(
        r"^(?:\[.*?\]\s*)?(?:STORY|ST|REC)[A-Z0-9\-]*\s*[:\-]\s*", "", t, flags=re.IGNORECASE
    ).strip()


def _clean_adf_description(md_content: str) -> str:
    """Retire le titre H1 (s'il existe) même après le frontmatter."""
    content_to_check = md_content
    if content_to_check.startswith("---"):
        parts = content_to_check.split("---", 2)
        if len(parts) >= 3:
            content_to_check = parts[2]

    lines = content_to_check.splitlines()
    h1_found = None
    if lines:
        for line in lines:
            if line.strip().startswith("# "):
                h1_found = line
                break
            elif line.strip():
                break

    if h1_found:
        return md_content.replace(h1_found, "", 1).strip()
    return md_content.strip()


def _fetch_allowed_subtask_types(client: httpx.Client, project_key: str) -> dict:
    allowed_subtasks = {}
    try:
        r_meta = client.get("/rest/api/3/issuetype")
        if r_meta.status_code == 200:
            issue_types = r_meta.json()
            for it in issue_types:
                if it.get("subtask"):
                    it_name = it.get("name", "")
                    it_id = it.get("id")
                    clean_name = it_name.lstrip("- ").lower()
                    allowed_subtasks[clean_name] = {"id": it_id, "name": it_name}
    except Exception as e:
        logger.warning(
            "Récupération des types de sous-tâche Jira échouée, dict vide retourné",
            exc_info=True,
            extra={
                "component": "pipelines.jira.jira_helpers",
                "operation": "fetch_allowed_subtask_types",
                "project_key": project_key,
                "error": str(e),
            },
        )
    return allowed_subtasks


def is_jira_status_closed(status_name: str, status_category_key: str = "") -> bool:
    """
    Détermine si un statut Jira correspond à un état FERMÉ / TERMINÉ / ARCHIVÉ.
    Règle constitutionnelle mLoop : 'si un récit est au statut FERMÉ dans jira ne jamais sync'.
    """
    if not status_name and not status_category_key:
        return False

    if status_category_key and status_category_key.strip().lower() == "done":
        return True

    normalized = status_name.strip().lower()
    closed_keywords = {
        "fermé",
        "fermee",
        "fermée",
        "ferme",
        "closed",
        "close",
        "clos",
        "terminé",
        "terminee",
        "terminée",
        "termine",
        "done",
        "resolved",
        "résolu",
        "resolu",
        "archived",
        "archivé",
        "archive",
        "abandonné",
        "abandonne",
        "cancelled",
        "canceled",
        "annulé",
        "annule",
    }
    return normalized in closed_keywords


def _fetch_existing_stories(client: httpx.Client, state: LoopState) -> dict:
    existing_stories_map = {}
    try:
        jql = f"project = {state.jira_project_key} AND issuetype in (Story) ORDER BY created DESC"
        start_at = 0
        max_results = 100
        while start_at < 500:
            r_search = client.get(
                f"/rest/api/3/search/jql?jql={jql}&startAt={start_at}"
                f"&maxResults={max_results}&fields=summary,status"
            )
            if r_search.status_code == 200:
                search_data = r_search.json()
                issues = search_data.get("issues", [])
                if not issues:
                    break
                for issue in issues:
                    summary = issue.get("fields", {}).get("summary", "")
                    status_obj = issue.get("fields", {}).get("status", {})
                    for story_item in state.sprint_backlog:
                        if (
                            story_item.id in summary
                            or _clean_title(story_item.title).lower()
                            == _clean_title(summary).lower()
                        ):
                            existing_stories_map[story_item.id] = {
                                "key": issue.get("key"),
                                "id": issue.get("id"),
                                "status": status_obj.get("name", ""),
                                "status_category": (
                                    status_obj.get("statusCategory", {}).get("key", "")
                                ),
                            }
                if len(issues) < max_results:
                    break
                start_at += max_results
            else:
                break
    except Exception as e:
        logger.warning(
            "Récupération des stories Jira existantes échouée, map vide retournée",
            exc_info=True,
            extra={
                "component": "pipelines.jira.jira_helpers",
                "operation": "fetch_existing_stories",
                "project_key": state.jira_project_key,
                "error": str(e),
            },
        )
    return existing_stories_map


def _fetch_existing_subtask_data(client: httpx.Client, story_key: str) -> dict:
    existing_sub_data = {}
    try:
        r_issue = client.get(f"/rest/api/2/issue/{story_key}?fields=subtasks")
        if r_issue.status_code == 200:
            issue_details = r_issue.json()
            subtasks = issue_details.get("fields", {}).get("subtasks", [])
            for sub in subtasks:
                sub_summary = sub.get("fields", {}).get("summary", "")
                sub_key = sub.get("key")
                existing_sub_data[sub_summary.strip().lower()] = sub_key
    except Exception as e:
        logger.warning(
            "Récupération des sous-tâches existantes échouée, dict vide retourné",
            exc_info=True,
            extra={
                "component": "pipelines.jira.jira_helpers",
                "operation": "fetch_existing_subtask_data",
                "story_key": story_key,
                "error": str(e),
            },
        )
    return existing_sub_data


def _validate_subtasks_mapping(
    state: LoopState, allowed_subtasks: dict, project_path: Path
) -> None:
    all_needed = set(state.jira_default_subtasks)
    for item in state.sprint_backlog:
        if getattr(item, "grilled", False) and getattr(item, "subtasks", None):
            all_needed.update(item.subtasks)

    missing_mappings = []
    for st_name in all_needed:
        st_lower = st_name.lower().strip()
        if st_lower not in state.jira_subtask_mapping:
            missing_mappings.append(st_name)

    if missing_mappings:
        raise JiraMappingRequiredError(missing_mappings, allowed_subtasks)


def _get_subtask_type_id(sub_name: str, allowed_subtasks: dict, state: LoopState) -> dict:
    comp_lower = sub_name.lower().strip()

    if comp_lower in state.jira_subtask_mapping:
        return {"id": state.jira_subtask_mapping[comp_lower]}

    for clean_key, info in allowed_subtasks.items():
        if comp_lower == clean_key:
            return {"id": info["id"]}

    for clean_key, info in allowed_subtasks.items():
        if comp_lower in clean_key or clean_key in comp_lower:
            return {"id": info["id"]}

    for target_key, variations in SUBTASK_TYPE_VARIATIONS.items():
        if any(v in comp_lower for v in variations) or target_key in comp_lower:
            for v in variations:
                for name, info in allowed_subtasks.items():
                    if v in name:
                        return {"id": info["id"]}

    standard_names = ["sub-task", "sous-tâche", "subtask", "sous-tache"]
    for sn in standard_names:
        for name, info in allowed_subtasks.items():
            if sn == name:
                return {"id": info["id"]}

    if allowed_subtasks:
        first_key = list(allowed_subtasks.keys())[0]
        return {"id": allowed_subtasks[first_key]["id"]}
    return None
