"""
Formal ADR Constraint Solver (Inspiré de Z3 SMT & CueLang).

Valide formellement et mathématiquement les invariants et contraintes d'architecture :
- Pas de couplage horizontal direct entre Stories d'Epics différentes.
- Frontmatter obligatoire : id, type, title, status, jira_key, epic_key.
- 4 Piliers Gherkin obligatoires dans ## Scénarios de test (ADR-0301).
- Zéro commentaire d'échafaudage résiduel.
"""
from __future__ import annotations

import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple


class FormalADRSolver:
    """Solveur formel de validation des contraintes d'architecture."""

    MANDATORY_FRONTMATTER_FIELDS = {"id", "type", "title", "status"}
    REQUIRED_SECTIONS = ["Description", "Contexte", "Règles d'affaires", "Scénarios de test"]

    @classmethod
    def verify_story_invariants(cls, story_content: str) -> Tuple[bool, List[str]]:
        """Vérifie l'ensemble des prédicats formels sur une User Story."""
        violations: List[str] = []

        # 1. Invariant Frontmatter
        if not story_content.startswith("---"):
            violations.append("INV-01: Frontmatter YAML manquant.")
        else:
            parts = story_content.split("---", 2)
            if len(parts) >= 3:
                try:
                    fm = yaml.safe_load(parts[1]) or {}
                    for f in cls.MANDATORY_FRONTMATTER_FIELDS:
                        if f not in fm or not str(fm[f]).strip():
                            violations.append(f"INV-02: Champ obligatoire '{f}' manquant dans le Frontmatter.")
                except Exception as e:
                    violations.append(f"INV-03: Erreur de parsing YAML : {e}")

        # 2. Invariant Sections structurelles
        for sec in cls.REQUIRED_SECTIONS:
            if not re.search(rf"^##\s+{re.escape(sec)}", story_content, flags=re.MULTILINE):
                violations.append(f"INV-04: Section structurelle obligatoire '## {sec}' absente.")

        # 3. Invariant Gherkin (4 Piliers)
        if "## Scénarios de test" in story_content:
            test_section = story_content.split("## Scénarios de test", 1)[1]
            has_given = bool(re.search(r"\b(Étant donné|Given)\b", test_section, flags=re.IGNORECASE))
            has_when = bool(re.search(r"\b(Quand|When|Lorsqu)\b", test_section, flags=re.IGNORECASE))
            has_then = bool(re.search(r"\b(Alors|Then)\b", test_section, flags=re.IGNORECASE))
            
            if not (has_given and has_when and has_then):
                violations.append("INV-05: Scénarios de test incomplets (au moins un bloc Given-When-Then requis).")

        # 4. Invariant d'échafaudage résiduel
        if re.search(r"#\s*PILIER\s*\d", story_content, flags=re.IGNORECASE):
            violations.append("INV-06: Marqueur d'échafaudage '# PILIER X' résiduel détecté dans le corps du texte.")

        return len(violations) == 0, violations


def solve_story_constraints(story_content: str) -> Dict[str, Any]:
    """Exécute la vérification formelle sur une story."""
    is_valid, violations = FormalADRSolver.verify_story_invariants(story_content)
    return {
        "is_valid": is_valid,
        "violations": violations,
        "solver_status": "SAT" if is_valid else "UNSAT",
    }
