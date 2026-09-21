"""
Sous-module Jira : jira_story_creator.py
Responsabilité : Création de nouvelles stories Jira et mise à jour des fichiers locaux.
"""

import re
import httpx
from pathlib import Path
from src.state import LoopState, ProjectLayout, SprintBacklogItem
from src.pipelines.jira.jira_subtasks import _create_subtask


def _update_local_files(
    project_path: Path,
    item: SprintBacklogItem,
    new_key: str,
    actions_log: list,
    clean_story_title: str,
):
    """Met à jour le frontmatter MD local et sprint_backlog.md après création."""
    try:
        md_file_path = project_path / "backlog" / item.description
        if md_file_path.exists():
            content = md_file_path.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    if "jira_key:" not in frontmatter:
                        new_frontmatter = frontmatter.rstrip() + f"\njira_key: {new_key}\n"
                    else:
                        new_frontmatter = re.sub(
                            r"jira_key:\s*[A-Z0-9-]+",
                            f"jira_key: {new_key}",
                            frontmatter,
                        )
                    new_content = f"---{new_frontmatter}---{parts[2]}"
                    md_file_path.write_text(new_content, encoding="utf-8")
    except Exception as e_md:
        actions_log.append(
            {
                "type": "Story",
                "id": new_key,
                "title": clean_story_title,
                "action": "WARN",
                "details": f"MAJ MD local échouée: {e_md}",
            }
        )

    try:
        sb_path = project_path / ProjectLayout.BACKLOG / ProjectLayout.SPRINT_BACKLOG_FILE
        if sb_path.exists():
            sb_content = sb_path.read_text(encoding="utf-8")
            updated = re.sub(
                rf"(\|\s*\*\*{re.escape(item.id)}[^|]*\|)\s*-\s*(\|)",
                rf"\1 {new_key} \2",
                sb_content,
            )
            if updated != sb_content:
                sb_path.write_text(updated, encoding="utf-8")
    except Exception as e_sb:
        actions_log.append(
            {
                "type": "Story",
                "id": new_key,
                "title": clean_story_title,
                "action": "WARN",
                "details": f"MAJ sprint_backlog.md échouée: {e_sb}",
            }
        )


def create_new_story(
    client: httpx.Client,
    item: SprintBacklogItem,
    clean_story_title: str,
    adf_description: dict,
    story_epic_key: str,
    subtasks_to_sync: list,
    state: LoopState,
    allowed_subtasks: dict,
    project_path: Path,
    actions_log: list,
    current_billing_id: str,
    current_components: list,
    manifest_id: str,
):
    """Crée une nouvelle story Jira avec sous-tâches et met à jour les fichiers locaux."""
    try:
        escaped_title = clean_story_title.replace('"', '\\"')
        check_jql = f'project = {state.jira_project_key} AND summary ~ "\\"{escaped_title}\\""'
        r_check = client.get(f"/rest/api/3/search/jql?jql={check_jql}&maxResults=1&fields=summary")
        if r_check.status_code == 200 and r_check.json().get("total", 0) > 0:
            existing_issue = r_check.json().get("issues")[0]
            actions_log.append(
                {
                    "type": "Story",
                    "id": item.id,
                    "title": clean_story_title,
                    "action": "DOUBLON",
                    "details": f"Existe déjà ({existing_issue.get('key')})",
                }
            )
            return
    except Exception:
        pass

    payload = {
        "fields": {
            "project": {"key": state.jira_project_key},
            "summary": clean_story_title,
            "description": adf_description,
            "issuetype": {"name": "Story"},
        }
    }
    if current_billing_id:
        payload["fields"]["customfield_10151"] = {"id": current_billing_id}
    if current_components:
        payload["fields"]["components"] = current_components
    if story_epic_key:
        payload["fields"]["parent"] = {"key": story_epic_key}

    try:
        r = client.post("/rest/api/3/issue", json=payload)
        if r.status_code == 201:
            new_key = r.json().get("key")
            _update_local_files(project_path, item, new_key, actions_log, clean_story_title)
            actions_log.append(
                {
                    "type": "Story",
                    "id": new_key,
                    "title": clean_story_title,
                    "action": "CREEE",
                    "details": f"Nouvelle story créée (manifeste {manifest_id})",
                }
            )
            for comp in subtasks_to_sync:
                _create_subtask(
                    client,
                    comp,
                    new_key,
                    item.title,
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
                    "id": item.id,
                    "title": clean_story_title,
                    "action": "ECHEC",
                    "details": r.text[:80],
                }
            )
    except Exception as e:
        actions_log.append(
            {
                "type": "Story",
                "id": item.id,
                "title": clean_story_title,
                "action": "ECHEC",
                "details": str(e),
            }
        )
