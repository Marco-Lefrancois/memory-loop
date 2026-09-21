"""
Sous-module Jira : jira_reader.py
Responsabilité : Lecture d'un ticket Jira Cloud (API v3) et restitution de sa
description ADF en Markdown lisible, pour permettre le diff Jira <-> récit local.

Réutilise le pattern d'authentification de sync_engine (JIRA_URL / JIRA_EMAIL /
JIRA_API_TOKEN chargés depuis l'environnement, jamais affichés).
"""

import logging
import os
import httpx

from src.cli import ZeroFluffConsole

logger = logging.getLogger(__name__)


def _adf_inline_to_md(node: dict) -> str:
    """Convertit un node inline ADF (text, hardBreak) en Markdown."""
    t = node.get("type")
    if t == "hardBreak":
        return "\n"
    if t == "text":
        txt = node.get("text", "")
        marks = [m.get("type") for m in node.get("marks", [])]
        if "code" in marks:
            txt = f"`{txt}`"
        if "strong" in marks:
            txt = f"**{txt}**"
        if "em" in marks:
            txt = f"*{txt}*"
        link = next((m for m in node.get("marks", []) if m.get("type") == "link"), None)
        if link:
            href = link.get("attrs", {}).get("href", "")
            txt = f"[{txt}]({href})"
        return txt
    # Fallback : descendre dans les enfants
    return "".join(_adf_inline_to_md(c) for c in node.get("content", []) or [])


def adf_to_markdown(desc: dict) -> str:
    """Convertit une description ADF (dict) en Markdown lisible."""
    if not isinstance(desc, dict):
        return ""
    out = []

    def render(node: dict) -> str:
        t = node.get("type")
        children = node.get("content", []) or []
        inner = "".join(render(c) for c in children)
        if t == "text" or t == "hardBreak":
            return _adf_inline_to_md(node)
        if t == "paragraph":
            return "".join(_adf_inline_to_md(c) for c in children) + "\n\n"
        if t == "heading":
            lvl = node.get("attrs", {}).get("level", 1)
            head = "".join(_adf_inline_to_md(c) for c in children)
            return "#" * lvl + " " + head + "\n\n"
        if t == "codeBlock":
            lang = node.get("attrs", {}).get("language", "")
            code = "".join(_adf_inline_to_md(c) for c in children)
            return f"```{lang}\n{code}\n```\n\n"
        if t == "bulletList":
            lines = []
            for li in children:
                li_txt = "".join(render(c) for c in li.get("content", [])).strip()
                lines.append(f"- {li_txt}")
            return "\n".join(lines) + "\n\n"
        if t == "orderedList":
            start = node.get("attrs", {}).get("order", 1)
            lines = []
            for i, li in enumerate(children, start):
                li_txt = "".join(render(c) for c in li.get("content", [])).strip()
                lines.append(f"{i}. {li_txt}")
            return "\n".join(lines) + "\n\n"
        if t == "table":
            rows = []
            for r_i, row in enumerate(children):
                cells = row.get("content", [])
                texts = [
                    "".join(render(c) for c in cell.get("content", [])).strip().replace("\n", " ")
                    for cell in cells
                ]
                rows.append("| " + " | ".join(texts) + " |")
                if r_i == 0:
                    rows.append("| " + " | ".join("---" for _ in texts) + " |")
            return "\n".join(rows) + "\n\n"
        if t == "rule":
            return "---\n\n"
        if t in ("panel", "blockquote"):
            body = inner.strip().replace("\n", "\n> ")
            return "> " + body + "\n\n"
        return inner

    for n in desc.get("content", []):
        out.append(render(n))
    return "".join(out).strip() + "\n"


def read_jira_issue(issue_key: str) -> dict | None:
    """
    Lit un ticket Jira et retourne {key, summary, status, description_md}.
    Retourne None si credentials manquants ou erreur API.
    """
    jira_url = (os.getenv("JIRA_URL") or "").rstrip("/")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")

    if not all([jira_url, jira_email, jira_token]):
        ZeroFluffConsole.error("Identifiants Jira manquants dans le fichier .env.")
        logger.error(
            "jira.read.config_missing",
            extra={"jira_key": issue_key, "config_missing": True},
        )
        return None

    auth = (str(jira_email), str(jira_token))
    headers = {"Accept": "application/json", "Accept-Encoding": "gzip, deflate"}

    try:
        with httpx.Client(base_url=jira_url, auth=auth, headers=headers, timeout=30.0) as client:
            resp = client.get(
                f"/rest/api/3/issue/{issue_key}",
                params={"fields": "summary,status,description"},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        ZeroFluffConsole.error(f"Jira API {e.response.status_code} pour {issue_key}.")
        if e.response.status_code == 429:
            logger.warning(
                "jira.read.rate_limited",
                extra={
                    "jira_key": issue_key,
                    "http_status": 429,
                    "retry_after": e.response.headers.get("Retry-After"),
                    "fields_requested": "summary,status,description",
                },
            )
        else:
            logger.error(
                "jira.read.http_error",
                extra={
                    "jira_key": issue_key,
                    "http_status": e.response.status_code,
                    "fields_requested": "summary,status,description",
                },
                exc_info=True,
            )
        return None
    except Exception as e:  # noqa: BLE001
        ZeroFluffConsole.error(f"Erreur lecture Jira {issue_key}: {type(e).__name__}.")
        logger.error(
            "jira.read.unexpected_error",
            extra={
                "jira_key": issue_key,
                "fields_requested": "summary,status,description",
                "mapping_errors": type(e).__name__,
            },
            exc_info=True,
        )
        return None

    fields = data.get("fields", {})
    return {
        "key": data.get("key"),
        "summary": fields.get("summary"),
        "status": (fields.get("status") or {}).get("name"),
        "description_md": adf_to_markdown(fields.get("description") or {}),
    }
