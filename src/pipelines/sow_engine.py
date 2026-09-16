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
        bp_path = (
            self.workspace_root
            / "standards"
            / "blueprints"
            / "sow_evaluation_template.md"
        )
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

        # 2. Backlog check (ADR-0339 : Découpage macro dans sprint_backlog.md en Phase 1)
        context["macro_stories"] = []
        backlog_file = self.project_path / "backlog" / "sprint_backlog.md"
        if backlog_file.exists():
            try:
                b_lines = backlog_file.read_text(encoding="utf-8", errors="ignore").splitlines()
                for line in b_lines:
                    line_s = line.strip()
                    if (
                        line_s.startswith("|")
                        and not line_s.startswith("| :---")
                        and not line_s.startswith("| ID")
                        and not line_s.startswith("| #")
                        and not line_s.startswith("| Métrique")
                    ):
                        cols = [c.strip() for c in line_s.split("|")[1:-1]]
                        if len(cols) >= 3:
                            story_id = cols[0].replace("**", "").replace("`", "").strip()
                            story_title = cols[1].strip()
                            story_comp = cols[2].strip() if len(cols) > 2 else ""
                            story_status = cols[3].strip() if len(cols) > 3 else "OPEN"
                            context["macro_stories"].append(
                                {
                                    "id": story_id,
                                    "title": story_title,
                                    "component": story_comp,
                                    "status": story_status,
                                }
                            )
            except Exception as e:
                logger.debug(f"Erreur lecture sprint_backlog.md : {e}", exc_info=True)

        # 3. Check récits physiques détaillés (Avertissement ADR-0339)
        stories_dir = self.project_path / "backlog" / "stories"
        context["detailed_stories_count"] = 0
        if stories_dir.exists():
            detailed_files = [
                sf for sf in stories_dir.glob("*.md") if sf.name != "README.md"
            ]
            context["detailed_stories_count"] = len(detailed_files)
            for sf in sorted(detailed_files):
                c = sf.read_text(encoding="utf-8", errors="ignore")
                m_title = re.search(r"^#\s+(.+)$", c, re.MULTILINE)
                stitle = m_title.group(1).strip() if m_title else sf.stem
                context["stories_found"].append({"id": sf.stem, "title": stitle})

            if detailed_files:
                logger.warning(
                    "[ADR-0339 Notice] %d récit(s) détaillé(s) détecté(s) sous backlog/stories/ "
                    "pendant l'évaluation SOW. En Phase 1 (SOW), le découpage doit demeurer "
                    "macroscopique dans sprint_backlog.md.",
                    len(detailed_files),
                )

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
        content = content.replace(
            "([N] jours / [N] h / [N] $ CAD)",
            f"({days} jours / {hours} h / {formatted_cost} CAD)",
        )
        content = content.replace(
            "| **Total Heures Estimées** | **[N]** |",
            f"| **Total Heures Estimées** | **{hours}** |",
        )
        content = content.replace(
            "| **Total Story Points (1 SP = 8h)** | **[N]** |",
            f"| **Total Story Points (1 SP = 8h)** | **{sp}** |",
        )
        content = content.replace(
            "| **Total Jours Ouvrés (1 j = 8h)** | **[N]** |",
            f"| **Total Jours Ouvrés (1 j = 8h)** | **{days}** |",
        )
        content = content.replace(
            "| **Valeur Monétaire Estimée** | **[N] $** |",
            f"| **Valeur Monétaire Estimée** | **{formatted_cost}** |",
        )

        # Injection dynamique des récits macro dans Section 4 si présents
        if ctx.get("macro_stories"):
            macro_rows = []
            for s in ctx["macro_stories"]:
                macro_rows.append(
                    f"| `{s['id']}` | {s['component'] or 'Composant'} | 3 | **{s['title']}** : Découpage macro en attente de cadrage fin (Gate 2). |"
                )
            if macro_rows:
                macro_table_block = (
                    "| ID | Parcours / Composant | SP | Titre & Description Sommaire (*INVEST*) |\n"
                    "| :--- | :--- | :---: | :--- |\n"
                    + "\n".join(macro_rows)
                )
                # Remplacer le bloc par défaut dans le template s'il existe
                default_table_pattern = (
                    r"\| ID \| Parcours / Composant \| SP \| Titre & Description Sommaire \(\*INVEST\*\) \|\n"
                    r"\| :--- \| :--- \| :---: \| :--- \|\n"
                    r"(?:\| `.+` \| .+ \| \d+ \| .+ \|\n?)+"
                )
                content = re.sub(default_table_pattern, macro_table_block + "\n", content)

        out_dir = self.project_path / "docs" / "01-architecture"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"SOW_{self.project_name}.md"

        out_file.write_text(content, encoding="utf-8")
        return out_file

    # ── ADR-0331 §2.2.3 : Interdiction Formelle des Libellés Génériques ──────

    _GENERIC_LABEL_PATTERNS = [
        r"\[Détail des récits\]",
        r"Composant générique",
        r"Développement divers",
    ]

    def validate_task_granularity(self, sow_file: Path) -> List[str]:
        """
        Linter de conformité ADR-0331 §2.2 Règle #3 : détecte les libellés
        vagues proscrits (« [Détail des récits] », « Composant générique »,
        « Développement divers ») dans le tableau de chiffrage détaillé d'un
        SOW généré. Retourne la liste des libellés génériques rencontrés
        (liste vide si le SOW est conforme).
        """
        violations: List[str] = []
        if not sow_file.exists():
            return violations

        content = sow_file.read_text(encoding="utf-8", errors="ignore")
        for pattern in self._GENERIC_LABEL_PATTERNS:
            for m in re.finditer(pattern, content, re.IGNORECASE):
                violations.append(
                    f"Libellé générique proscrit détecté : « {m.group(0)} » "
                    f"(ADR-0331 §2.2 Règle #3 — Interdiction Formelle des "
                    f"Libellés Génériques). Remplacer par une description "
                    f"fonctionnelle concrète des écrans/flux/protocoles concernés."
                )
        return violations
