"""
src/dashboard/project_utils.py — Utilitaires SSOT de Résolution et Typage des Projets (ADR-0369).

Résout les alias canoniques, les chemins sur disque et le matching tolérant
pour l'ensemble des modules métiers : Boire & Frères, Metro (Commerce, Food, Pharma/Santé, Shared),
Memory Loop Core et tiers.
Conforme ADR-0202 (<300 lignes, <15 Ko) et ADR-0369.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger("dashboard.project_utils")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def canonical_key(name: str) -> str:
    """Normalise une chaîne pour comparaison floue stricte (sans accents, sans ponctuation)."""
    if not name:
        return ""
    normalized = unicodedata.normalize("NFD", str(name))
    clean = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-zA-Z0-9]", "", clean).lower()


def resolve_project_canonical_name(project_name: Optional[str]) -> str:
    """
    Résout le nom canonique du projet en gérant tous les alias métiers connus.
    Exemples :
      - 'boire', 'boire et frere' -> 'BoireFrere_Segment2'
      - 'metro commerce', 'commerce' -> 'Metro_COMMERCE'
      - 'metro food', 'food', 'alimentation' -> 'Metro_FOOD'
      - 'metro pharma', 'pharma', 'sante', 'jean coutu', 'brunet' -> 'Metro_SANTE'
      - 'shared', 'metro shared' -> 'Metro_SHARED'
      - 'ALL', 'global', '*' -> 'ALL'
    """
    if not project_name:
        return "Memory Loop"

    clean = project_name.strip()
    if clean.upper() in ("ALL", "GLOBAL", "TOUS", "*") or clean in ("All", "global", "*"):
        return "ALL"

    if clean.lower() in ("default", "core", "memory loop", "mloop"):
        return "Memory Loop"

    ck = canonical_key(clean)

    # 1. Alias métiers explicites prioritaires
    if "boire" in ck or "couvoir" in ck:
        return "BoireFrere_Segment2"

    # Modules Metro
    if "food" in ck or "aliment" in ck or "epicerie" in ck:
        return "Metro_FOOD"
    if "commerce" in ck or "ecom" in ck:
        return "Metro_COMMERCE"
    if "pharma" in ck or "sante" in ck or "jeancoutu" in ck or "brunet" in ck or "rxpro" in ck:
        return "Metro_SANTE"
    if "shared" in ck or "socle" in ck:
        return "Metro_SHARED"
    if ck == "metro":
        return "Metro_FOOD"

    if "htc" in ck:
        return "HTC"
    if "shopify" in ck:
        return "Shopify_AI_Item_Creator"

    # 2. Utilisation du résolveur officiel mLoop si disponible
    try:
        from src.swarm import resolve_project_name

        resolved = resolve_project_name(clean)
        if resolved:
            return resolved
    except Exception as e:
        logger.debug(
            "Résolveur de projet mLoop indisponible, fallback sur le scan physique Projects/",
            exc_info=True,
            extra={
                "component": "dashboard.project_utils",
                "operation": "resolve_project_canonical_name",
                "project_input": clean,
                "error": str(e),
            },
        )

    # 3. Scan direct des dossiers physiques sous Projects/
    projects_dir = REPO_ROOT / "Projects"
    if projects_dir.exists():
        for p in projects_dir.iterdir():
            if (
                p.is_dir()
                and not p.name.startswith(".")
                and not p.name.startswith("_")
                and not p.name.endswith("_DEPRECATED")
            ):
                p_ck = canonical_key(p.name)
                if ck == p_ck or (ck and (ck in p_ck or p_ck in ck)):
                    return p.name

    return clean


def resolve_project_path(project: Optional[str]) -> Path:
    """Résout le chemin absolu du dossier d'un projet cible."""
    canon = resolve_project_canonical_name(project)
    if not canon or canon in ("Memory Loop", "mLoop", "global", "ALL"):
        main_p = REPO_ROOT / "Projects" / "mLoop"
        if main_p.exists():
            return main_p
        return REPO_ROOT

    p_path = REPO_ROOT / "Projects" / canon
    if p_path.exists():
        return p_path

    return REPO_ROOT


def match_project_alias(
    candidate: str, target: str, entry: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Vérifie si une entrée candidate de journal correspond au projet cible.
    Gère la tolérance d'alias et les projets transverses (ex: Metro_OneTrust -> COMMERCE/FOOD/SANTE).
    """
    if not candidate or not target:
        return False

    if target.upper() in ("ALL", "GLOBAL", "*"):
        return True

    if candidate.lower() == target.lower():
        return True

    c_ck = canonical_key(candidate)
    t_ck = canonical_key(target)
    if c_ck == t_ck:
        return True

    # Boire & Frères (englobe Segment 2 et Réception)
    if "boire" in t_ck:
        return "boire" in c_ck

    # Modules Metro
    if "metro" in t_ck or t_ck in ("food", "commerce", "sante", "pharma", "shared"):
        # Cible Metro Alimentation / Food
        if "food" in t_ck or "aliment" in t_ck:
            if "food" in c_ck:
                return True
            if candidate == "Metro_OneTrust" and entry:
                contribs = (
                    str(entry.get("context_contributors", [])) + str(entry.get("target", ""))
                ).lower()
                return "food" in contribs
            return False

        # Cible Metro E-Commerce
        if "commerce" in t_ck or "ecom" in t_ck:
            if "commerce" in c_ck:
                return True
            if candidate == "Metro_OneTrust" and entry:
                contribs = (
                    str(entry.get("context_contributors", [])) + str(entry.get("target", ""))
                ).lower()
                return "commerce" in contribs
            return False

        # Cible Metro Santé / Pharma (Jean Coutu & Brunet)
        if "sante" in t_ck or "pharma" in t_ck:
            if "sante" in c_ck or "pharma" in c_ck:
                return True
            if candidate == "Metro_OneTrust" and entry:
                contribs = (
                    str(entry.get("context_contributors", [])) + str(entry.get("target", ""))
                ).lower()
                return "sante" in contribs or "pharma" in contribs
            return False

        # Cible Metro Shared
        if "shared" in t_ck or "socle" in t_ck:
            return "shared" in c_ck

        # Cible Metro générique
        if t_ck == "metro":
            return "metro" in c_ck

    # Dashboard mLoop
    if "dashboard" in t_ck:
        if "dashboard" in c_ck:
            return True
        if c_ck in ("mloop", "memoryloop"):
            if entry:
                haystack = (
                    str(entry.get("target", ""))
                    + " "
                    + str(entry.get("action", ""))
                    + " "
                    + str(entry.get("context_contributors", []))
                ).lower()
                if "dashboard" in haystack:
                    return True
            return True

    return False


FRIENDLY_PROJECT_NAMES: Dict[str, str] = {
    "ALL": "📊 Tous les projets (Global Consolidé)",
    "BoireFrere_Segment2": "🐣 Boire & Frères — Couvoir & Segment 2",
    "Metro_FOOD": "🛒 Metro — Alimentation (Food)",
    "Metro_COMMERCE": "💳 Metro — E-Commerce / Commerce Pharma",
    "Metro_SANTE": "🏥 Metro — Santé / Pharma (Jean Coutu & Brunet)",
    "Metro_SHARED": "📦 Metro — Shared (Socle Commun)",
    "Memory Loop": "🌀 Memory Loop (Framework Core)",
    "mLoop-Dashboard": "📊 mLoop Dashboard",
    "HTC": "🧱 HTC Maçonnerie",
    "Shopify_AI_Item_Creator": "🛍️ Shopify AI Creator",
}


def get_friendly_project_label(project_id: str) -> str:
    """Retourne l'intitulé métier convivial pour l'affichage UI."""
    return FRIENDLY_PROJECT_NAMES.get(project_id, project_id)


def list_available_projects() -> List[str]:
    """Retourne la liste ordonnée de tous les projets disponibles avec les modules métiers en tête."""
    projects = set()
    projects_dir = REPO_ROOT / "Projects"
    excluded = {
        "default",
        "cacheproj",
        "timeoutproj",
        "testproject",
        "testspecial",
        "testlegacy",
        "_archive",
    }

    if projects_dir.exists():
        for p in projects_dir.iterdir():
            if (
                p.is_dir()
                and not p.name.startswith(".")
                and not p.name.startswith("_")
                and not p.name.endswith("_DEPRECATED")
                and p.name.lower() not in excluded
            ):
                projects.add(p.name)

    # Ordre de priorité métier
    priority_order = [
        "ALL",
        "BoireFrere_Segment2",
        "Metro_FOOD",
        "Metro_COMMERCE",
        "Metro_SANTE",
        "Metro_SHARED",
        "Memory Loop",
    ]

    result = [p for p in priority_order if p == "ALL" or p in projects or p == "Memory Loop"]
    other_projects = sorted([p for p in projects if p not in priority_order])
    return result + other_projects
