"""
ADR Writer - mLoop Grill Package (ADR-0320 / ADR-012)
Gestion de la cascade de templates, du calcul d'ID anti-collision et de l'écriture disque.
"""

import datetime
import logging
from pathlib import Path
import re
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

EMERGENCY_FALLBACK_TEMPLATE = """# 🏛️ ADR-{{ADR_ID}} : {{TITLE}}

- **Statut** : DECIDED
- **Date** : {{DATE}}
- **Décideurs** : Utilisateur & mLoop Agent

## Contexte & Problème
{{CONTEXT}}

## Décision Retenue
{{DECISION}}

## Conséquences
### Positives
{{POSITIVES}}

### Négatives / Risques
{{NEGATIVES}}

---
*Généré via Fallback d'urgence mLoop le {{DATE}}.*
"""


def get_framework_root() -> Path:
    """Retourne la racine du framework mLoop (C:/Memory Loop)."""
    return Path(__file__).resolve().parent.parent.parent.parent


def resolve_adr_template(project_path: Optional[Path] = None) -> str:
    """
    Résout le gabarit d'ADR selon la cascade à 3 niveaux (ADR-012) :
    1. Surcharge locale projet (Projects/<p>/docs/01-architecture/template.md)
    2. Blueprint canonique du framework (standards/blueprints/project_adr_template.md)
    3. Fallback mémoire minimal de sécurité avec log WARNING
    """
    # 1. Surcharge locale projet
    if project_path:
        project_template = project_path / "docs" / "01-architecture" / "template.md"
        if project_template.is_file():
            try:
                content = project_template.read_text(encoding="utf-8")
                logger.debug(
                    "Utilisation du template local d'ADR projet",
                    extra={"component": "pipelines.grill", "template": str(project_template)},
                )
                return content
            except Exception as exc:
                logger.warning(
                    f"Échec de lecture du template local projet ({exc}), passage au framework.",
                    extra={"component": "pipelines.grill"},
                )

    # 2. Blueprint canonique du framework
    framework_template = (
        get_framework_root() / "standards" / "blueprints" / "project_adr_template.md"
    )
    if framework_template.is_file():
        try:
            return framework_template.read_text(encoding="utf-8")
        except Exception as exc:
            logger.warning(
                f"Échec de lecture du blueprint framework ({exc}), bascule sur fallback d'urgence.",
                extra={"component": "pipelines.grill"},
            )

    # 3. Fallback d'urgence mémoire
    logger.warning(
        "Blueprint d'ADR introuvable. Utilisation du gabarit d'urgence en mémoire.",
        extra={"component": "pipelines.grill"},
    )
    return EMERGENCY_FALLBACK_TEMPLATE


def get_next_adr_id(docs_dir: Path) -> Tuple[int, int]:
    """
    Extrait tous les numéros d'ADR existants par regex anti-collision (ADR-012)
    et retourne (next_id, max_existing_id).
    Gère les trous de numérotation en prenant strictement max(ids) + 1.
    """
    if not docs_dir.exists():
        return (1, 0)

    pattern = re.compile(r"^ADR-(\d+)", re.IGNORECASE)
    ids = []

    for entry in docs_dir.glob("ADR-*.md"):
        if not entry.is_file():
            continue
        match = pattern.match(entry.name)
        if match:
            try:
                ids.append(int(match.group(1)))
            except ValueError:
                continue

    max_id = max(ids, default=0)
    return (max_id + 1, max_id)


def render_adr_content(
    template_str: str,
    adr_id: int,
    title: str,
    context: str = "",
    decision: str = "",
    positives: str = "",
    negatives: str = "",
    date_str: Optional[str] = None,
    max_id: int = 0,
) -> str:
    """
    Substitue déterministement les balises mLoop {{TAG}} et supporte le format {tag}.
    Applique des valeurs par défaut pour tout champ omis.
    """
    date_val = date_str or datetime.date.today().isoformat()
    # Formatage de l'ID : 3 chiffres par défaut, 4 chiffres si > 999
    formatted_id = f"{adr_id:04d}" if max_id > 999 or adr_id > 999 else f"{adr_id:03d}"

    ctx_val = context or "Session d'interrogatoire Grill-with-Docs."
    dec_val = decision or "Arbitrage d'architecture validé."
    pos_val = positives or "Clarification des exigences métier et réduction du flou."
    neg_val = negatives or "Contraintes et engagements d'architecture appliqués."

    rendered = template_str

    # Remplacement des balises doubles {{TAG}}
    replacements = {
        "{{ADR_ID}}": formatted_id,
        "{{TITLE}}": title,
        "{{DATE}}": date_val,
        "{{CONTEXT}}": ctx_val,
        "{{DECISION}}": dec_val,
        "{{POSITIVES}}": pos_val,
        "{{NEGATIVES}}": neg_val,
    }
    for tag, val in replacements.items():
        rendered = rendered.replace(tag, val)

    # Rétrocompatibilité avec les balises simples {tag}
    legacy_replacements = {
        "{adr_id:03d}": formatted_id,
        "{adr_id:04d}": formatted_id,
        "{adr_id}": str(adr_id),
        "{title}": title,
        "{date}": date_val,
        "{context}": ctx_val,
        "{decision}": dec_val,
        "{positives}": pos_val,
        "{negatives}": neg_val,
    }
    for tag, val in legacy_replacements.items():
        rendered = rendered.replace(tag, val)

    return rendered


def write_adr_file(
    docs_dir: Path,
    next_id: int,
    title: str,
    content: str,
    max_id: int = 0,
) -> Path:
    """Écrit le fichier Markdown dans le dossier docs_dir avec slug anti-collision."""
    docs_dir.mkdir(parents=True, exist_ok=True)
    slug_title = re.sub(r"[^a-zA-Z0-9_-]", "_", title.lower()).strip("_")
    formatted_id = f"{next_id:04d}" if max_id > 999 or next_id > 999 else f"{next_id:03d}"
    filename = f"ADR-{formatted_id}_{slug_title}.md"
    target_path = docs_dir / filename
    target_path.write_text(content, encoding="utf-8")
    return target_path
