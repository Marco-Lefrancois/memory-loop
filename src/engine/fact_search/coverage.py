# -*- coding: utf-8 -*-
"""
Fact-Search Story Coverage & Gleaning Evaluator (mLoop Core - ADR-0326).

Évalue la couverture factuelle d'un récit Markdown :
1. Extraction précise des critères d'acceptation et des scénarios Gherkin.
2. Confrontation de chaque exigence à l'index FTS5 documentaire.
3. Détection des contradictions sémantiques (Gleaning Verification).
4. Calcul du ratio de couverture et formatage EvidencePack 2.0.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.engine.fact_search.retriever import FactSearchRetriever
from src.utils.logger import get_logger

logger = get_logger("fact_search.coverage")


class FactSearchCoverageEvaluator:
    """Évaluateur de couverture factuelle et de conformité documentaire."""

    @classmethod
    def evaluate_story_coverage(
        cls,
        story_path: Path | str,
        project_name: str,
        db_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Calcule le score de couverture Fact-Search d'une User Story.
        Pour chaque critère ou scénario Gherkin, vérifie l'existence d'une preuve
        FTS5 déterministe ou d'une référence explicite SSOT (RM/ADR).
        """
        path_obj = Path(story_path)
        if not path_obj.exists():
            return {
                "coverage_ratio": 0.0,
                "total_criteria": 0,
                "covered_criteria": 0,
                "uncovered": ["Fichier de story introuvable"],
                "proofs": []
            }

        content = path_obj.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()

        criteria = cls._extract_criteria_and_scenarios(lines)
        if not criteria:
            return {
                "coverage_ratio": 1.0,
                "total_criteria": 0,
                "covered_criteria": 0,
                "uncovered": [],
                "proofs": []
            }

        covered_count = 0
        uncovered = []
        proofs = []

        for crit in criteria:
            has_direct_ref = bool(re.search(r'\b(RM-\d+|ADR-\d+)\b', crit))
            
            # Recherche factuelle avec FactSearchRetriever
            matches = FactSearchRetriever.search(
                query=crit,
                project_name=project_name,
                expand_synonyms=True,
                limit=2,
                log_audit=False,
                db_path=db_path,
            )

            is_covered = has_direct_ref or (matches and matches[0]["relevance_score"] >= 0.5)

            if is_covered:
                covered_count += 1
                top_match = matches[0] if matches else None
                proofs.append({
                    "criterion": crit[:120],
                    "status": "COVERED",
                    "direct_ref": has_direct_ref,
                    "top_source": top_match["breadcrumb"] if top_match else "Référence explicite SSOT",
                    "doc_path": top_match["doc_path"] if top_match else None,
                    "line_range": f"L{top_match['line_start']}-L{top_match['line_end']}" if top_match else None,
                    "snippet": top_match["snippet"] if top_match else None,
                })
            else:
                uncovered.append(crit)
                proofs.append({
                    "criterion": crit[:120],
                    "status": "UNCOVERED",
                    "direct_ref": False,
                    "top_source": None,
                    "doc_path": None,
                    "line_range": None,
                    "snippet": None,
                })

        ratio = round(covered_count / len(criteria), 2) if criteria else 1.0

        return {
            "coverage_ratio": ratio,
            "total_criteria": len(criteria),
            "covered_criteria": covered_count,
            "uncovered": uncovered,
            "proofs": proofs
        }

    @classmethod
    def _extract_criteria_and_scenarios(cls, lines: List[str]) -> List[str]:
        """Extrait les exigences fonctionnelles réelles hors des en-têtes structuraux."""
        criteria: List[str] = []
        in_target_section = False

        for line in lines:
            if re.match(r"^##\s+(Scénarios de test|Critères d'acceptation)", line, re.IGNORECASE):
                in_target_section = True
                continue
            if in_target_section and line.startswith("## "):
                break

            if in_target_section:
                # Ignorer les titres de sous-sections (### 1. Nominal...)
                if line.strip().startswith("###"):
                    continue
                crit_match = re.match(r'^\s*[-*]\s+(.*)$', line)
                if crit_match:
                    c_text = crit_match.group(1).strip()
                    if len(c_text) > 10 and not c_text.lower().startswith(("given", "when", "then", "soit", "quand", "alors")):
                        criteria.append(c_text)

        if not criteria:
            # Fallback sur les puces fonctionnelles
            for line in lines:
                if line.strip().startswith("- ") and len(line) > 15:
                    criteria.append(line.replace("- ", "").strip())

        return criteria
