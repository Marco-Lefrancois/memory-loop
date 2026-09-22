"""
src/dashboard/module_utils.py — Découverte et Résolution SSOT des Modules Métiers (ADR-0369/0370).

Gère la granularité au niveau des sous-dossiers de backlog / initiatives / epics :
- Boire & Frères : 01-reception, 02-incubation, 03-ventes
- Metro Food : OneTrust_FOOD, PAPERCUTS, Metro_Food_Offers, RBC_Avion
- Metro Commerce : OneTrust_COMMERCE, RBC_Avion
- Metro Santé / Pharma : OneTrust_SANTE, AccesDossier
- Metro Shared : OneTrust, Loi25-RGPD, Programme-Moi, SDK-MAUI
Conforme ADR-0202 (<300 lignes, <15 Ko).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.dashboard.project_utils import (
    canonical_key,
    resolve_project_canonical_name,
    resolve_project_path,
)
from src.dashboard._module_metadata import (
    MODULE_METADATA,
    get_module_friendly_info,
    normalize_module_id,
)
from src.utils.logger import get_logger

logger = get_logger("dashboard.module_utils")


def _find_module_key(name: str, existing: Dict[str, Any]) -> Optional[str]:
    ck = canonical_key(name)
    for k in existing:
        e_ck = canonical_key(k)
        if e_ck == ck:
            return k
        if "onetrust" in e_ck and "onetrust" in ck:
            return k
        if "offers" in e_ck and "offers" in ck:
            return k
        if "papercut" in e_ck and "papercut" in ck:
            return k
    return None


def discover_project_modules(project_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Scanne dynamiquement les modules d'un projet (backlog/stories, docs, reference)."""
    canon = resolve_project_canonical_name(project_name)
    p_root = resolve_project_path(canon)
    modules: Dict[str, Dict[str, Any]] = {}

    # 1. Sous-dossiers de backlog/stories/
    stories_root = p_root / "backlog" / "stories"
    if stories_root.exists() and stories_root.is_dir():
        for sub in sorted(stories_root.iterdir()):
            if sub.is_dir() and not sub.name.startswith((".", "_")):
                md_count = len(
                    [
                        f
                        for f in sub.glob("*.md")
                        if f.name.lower() not in ("readme.md", "sprint_backlog.md")
                    ]
                )
                modules[sub.name] = {
                    "id": sub.name,
                    "name": sub.name,
                    "has_stories": True,
                    "stories_count": md_count,
                    "has_docs": False,
                    "has_reference": False,
                    "source": "backlog",
                }

    # 2. Initiatives sous docs/
    docs_root = p_root / "docs"
    excluded_docs = {
        "00-ingested",
        "01-architecture",
        "02-business-rules",
        "03-models",
        "04-transverse",
        "05-assets",
        "adr",
        "diagrammes",
        "templates",
    }
    if docs_root.exists() and docs_root.is_dir():
        for sub in sorted(docs_root.iterdir()):
            if (
                sub.is_dir()
                and not sub.name.startswith(".")
                and sub.name.lower() not in excluded_docs
            ):
                k = _find_module_key(sub.name, modules)
                if k:
                    modules[k]["has_docs"] = True
                else:
                    modules[sub.name] = {
                        "id": sub.name,
                        "name": sub.name,
                        "has_stories": False,
                        "stories_count": 0,
                        "has_docs": True,
                        "has_reference": False,
                        "source": "docs",
                    }

    # 3. Dossiers sous reference/
    ref_root = p_root / "reference"
    excluded_ref = {
        "codebase",
        "codebases",
        "research",
        "schemas",
        "shared",
        "graphify-out",
        "anciens_recits",
        "legacy_sigpa_docs",
        "sigpa.wiki",
        "crawled",
    }
    if ref_root.exists() and ref_root.is_dir():
        for sub in sorted(ref_root.iterdir()):
            if (
                sub.is_dir()
                and not sub.name.startswith(".")
                and sub.name.lower() not in excluded_ref
            ):
                k = _find_module_key(sub.name, modules)
                if k:
                    modules[k]["has_reference"] = True
                else:
                    modules[sub.name] = {
                        "id": sub.name,
                        "name": sub.name,
                        "has_stories": False,
                        "stories_count": 0,
                        "has_docs": False,
                        "has_reference": True,
                        "source": "reference",
                    }

    result = []
    for m_id, data in modules.items():
        if data["stories_count"] == 0 and not data["has_docs"] and not data["has_reference"]:
            continue
        meta = get_module_friendly_info(m_id, canon)
        result.append(
            {
                **data,
                "label": meta["label"],
                "description": meta["description"],
                "category": meta["category"],
            }
        )

    result.sort(key=lambda x: (not x["has_stories"], x["id"]))
    return result


def get_story_module(story_path: Path, project_root: Path) -> str:
    """Déduit le nom du module d'une User Story."""
    try:
        parts = story_path.relative_to(project_root).parts
        if len(parts) >= 4 and parts[0].lower() == "backlog" and parts[1].lower() == "stories":
            return parts[2]
    except Exception as e:
        logger.debug(
            "Déduction du module depuis le chemin story échouée, fallback sur 'default'",
            exc_info=True,
            extra={
                "component": "dashboard.module_utils",
                "operation": "get_story_module",
                "story_path": str(story_path),
                "error": str(e),
            },
        )
    return "default"


def match_module_entry(
    entry_target: str,
    module_id: str,
    context_contributors: Optional[List[str]] = None,
) -> bool:
    """Vérifie si une entrée de trace ou ledger correspond à un module cible."""
    if not module_id or module_id.upper() in ("ALL", "*", "TOUS"):
        return True

    mod_norm = normalize_module_id(module_id)
    mod_ck = canonical_key(mod_norm)
    haystack = [entry_target or ""] + (context_contributors or [])

    for item in haystack:
        if not item:
            continue
        clean = str(item).replace("\\", "/").lower()
        if mod_norm in clean:
            return True
        ck = canonical_key(clean)
        if mod_ck and mod_ck in ck:
            return True
        if mod_ck in ("reception", "01reception") and ("rec0" in ck or "reception" in ck):
            return True
        if mod_ck in ("incubation", "02incubation") and ("inc0" in ck or "incubation" in ck):
            return True
        if mod_ck in ("ventes", "03ventes") and ("vnt0" in ck or "vente" in ck):
            return True
        if "onetrust" in mod_ck and "onetrust" in ck:
            return True
        if "papercut" in mod_ck and "papercut" in ck:
            return True

    return False


def get_all_projects_modules() -> Dict[str, List[Dict[str, Any]]]:
    """Retourne la cartographie des modules pour tous les projets."""
    from src.dashboard.project_utils import list_available_projects

    return {p: discover_project_modules(p) for p in list_available_projects() if p != "ALL"}
