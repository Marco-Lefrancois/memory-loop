"""
SOW Engine - Moteur de Génération d'Énoncé des Travaux et d'Évaluation Budgétaire (mLoop).

Génère automatiquement un SOW conforme au gabarit officiel standards/blueprints/sow_evaluation_template.md
en exploitant les documents ingérés (docs/00-ingested/), les règles d'affaires (RM-000) et le backlog existant.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

from src.cli import ZeroFluffConsole

logger = logging.getLogger("sow_engine")


class SOWEngine:
    """Génère et structure les Énoncés des Travaux (SOW) et Évaluations Budgétaires."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.project_name = project_path.name
        self.workspace_root = self._find_workspace_root()

    def _find_workspace_root(self) -> Path:
        """Remonte à la racine de mLoop contenant standards/."""
        cur = self.project_path.resolve()
        while cur.parent != cur:
            if (cur / "standards" / "blueprints").exists():
                return cur
            cur = cur.parent
        return Path.cwd()

    def get_blueprint_content(self) -> str:
        """Lit le gabarit officiel sow_evaluation_template.md."""
        bp_path = self.workspace_root / "standards" / "blueprints" / "sow_evaluation_template.md"
        if not bp_path.exists():
            # Fallback relatif
            bp_path = Path("standards/blueprints/sow_evaluation_template.md")
        if bp_path.exists():
            return bp_path.read_text(encoding="utf-8")
        raise FileNotFoundError(f"Gabarit SOW introuvable sous {bp_path}")

    def inspect_project_context(self) -> Dict[str, Any]:
        """Extrait les faits pertinents depuis docs/00-ingested/ et backlog/."""
        context: Dict[str, Any] = {
            "title": self.project_name.replace("_", " "),
            "ingested_files": [],
            "stories_found": [],
            "has_food": False,
            "has_commerce": False,
            "has_sante": False,
        }

        # 1. Ingestion check
        ingested_dir = self.project_path / "docs" / "00-ingested"
        if ingested_dir.exists():
            for f in ingested_dir.glob("*.md"):
                context["ingested_files"].append(f.name)
                txt = f.read_text(encoding="utf-8", errors="ignore").lower()
                if "food" in txt or "metro" in txt or "super c" in txt:
                    context["has_food"] = True
                if "commerce" in txt or "jean coutu" in txt:
                    context["has_commerce"] = True
                if "santé" in txt or "sante" in txt or "brunet" in txt or "rx" in txt:
                    context["has_sante"] = True

        # Si rien de spécifique détecté, activer par défaut le contexte du projet
        if "sante" in self.project_name.lower():
            context["has_sante"] = True
        if "food" in self.project_name.lower():
            context["has_food"] = True

        # 2. Backlog stories check
        stories_dir = self.project_path / "backlog" / "stories"
        if stories_dir.exists():
            for sf in sorted(stories_dir.glob("*.md")):
                if sf.name == "README.md":
                    continue
                c = sf.read_text(encoding="utf-8", errors="ignore")
                m_title = re.search(r"^#\s+(.+)$", c, re.MULTILINE)
                stitle = m_title.group(1).strip() if m_title else sf.stem
                context["stories_found"].append({"id": sf.stem, "title": stitle})

        return context

    def generate_sow(self, title: Optional[str] = None, target_size: str = "M") -> Path:
        """Génère le fichier SOW final sous docs/01-architecture/SOW_<project_name>.md."""
        template_text = self.get_blueprint_content()
        ctx = self.inspect_project_context()

        final_title = title or ctx["title"]
        today_str = date.today().strftime("%d %B %Y")

        # Remplacement des en-têtes principaux
        content = template_text
        content = content.replace("[TITRE DU PROJET]", final_title)
        content = content.replace("[Nom Officiel du Projet]", final_title)
        content = content.replace("[Date de Rédaction ex: 18 août 2026]", today_str)
        content = content.replace("[1.0]", "1.0")
        content = content.replace("`[T-SHIRT_SIZE]`", f"`{target_size}`")

        # Ajuster les montants selon la taille T-Shirt
        pricing_map = {
            "-": (0, 0),
            "xs": (15, 15000),
            "XS": (28.5, 28500),
            "s": (35, 35000),
            "S": (50, 50000),
            "m": (75, 75000),
            "M": (95, 95000),
            "l": (175, 175000),
            "L": (235, 235000),
            "xl": (250, 250000),
        }
        days, cost = pricing_map.get(target_size, (95, 95000))
        hours = int(days * 8)
        sp = int(hours / 8)

        formatted_cost = f"{cost:,} $".replace(",", " ")
        content = content.replace("([N] jours / [N] h / [N] $ CAD)", f"({days} jours / {hours} h / {formatted_cost} CAD)")
        content = content.replace("| **Total Heures Estimées** | **[N]** |", f"| **Total Heures Estimées** | **{hours}** |")
        content = content.replace("| **Total Story Points (1 SP = 8h)** | **[N]** |", f"| **Total Story Points (1 SP = 8h)** | **{sp}** |")
        content = content.replace("| **Total Jours Ouvrés (1 j = 8h)** | **[N]** |", f"| **Total Jours Ouvrés (1 j = 8h)** | **{days}** |")
        content = content.replace("| **Valeur Monétaire Estimée** | **[N] $** |", f"| **Valeur Monétaire Estimée** | **{formatted_cost}** |")

        out_dir = self.project_path / "docs" / "01-architecture"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"SOW_{self.project_name}.md"

        out_file.write_text(content, encoding="utf-8")
        return out_file
