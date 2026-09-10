"""
mLoop Engine - Simplicity & Over-Engineering Guard (ADR-0354)
Garde-fou contre le surapprentissage architectural et la sur-ingénierie.
Inspiré de l'Overfitting Guard Protocol du Google Planetary Prediction Engine.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class SimplicityBudget:
    max_modified_files: int = 3
    max_added_lines: int = 150
    allow_new_packages: bool = False
    allow_new_dependencies: bool = False
    task_scope: str = "STANDARD"  # "STANDARD", "PATCH", "EXPANSION"


@dataclass
class SimplicityReport:
    passed: bool
    modified_files_count: int
    added_lines_count: int
    new_packages_detected: List[str] = field(default_factory=list)
    new_dependencies_detected: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    pruning_suggestion: Optional[str] = None

    def format_summary(self) -> str:
        status = "PASSED" if self.passed else "BUDGET EXCEEDED (PRUNING REQUIRED)"
        lines = [
            f"=== SIMPLICITY GUARD REPORT ===",
            f"Statut : {status}",
            f"Fichiers touchés : {self.modified_files_count}",
            f"Lignes ajoutées  : {self.added_lines_count}",
        ]
        if self.new_packages_detected:
            lines.append(f"Nouveaux packages: {', '.join(self.new_packages_detected)}")
        if self.new_dependencies_detected:
            lines.append(f"Nouvelles dépendances: {', '.join(self.new_dependencies_detected)}")
        if self.violations:
            lines.append("Violations du budget :")
            for v in self.violations:
                lines.append(f"  - {v}")
        if self.pruning_suggestion:
            lines.append(f"\nDirective d'élagage (Single-Shot Pruning) :\n{self.pruning_suggestion}")
        return "\n".join(lines)


class SimplicityGuard:
    """
    Garde-fou heuristique en deux temps :
    1. Pre-Assessment : Calcule le budget d'élasticité logicielle autorisé.
    2. Post-Assessment : Vérifie le diff / code généré et déclenche une passe d'auto-correction.
    """

    @classmethod
    def compute_budget(
        cls,
        task_type: str = "feature",
        scope_description: str = "",
        explicit_full_rewrite: bool = False,
    ) -> SimplicityBudget:
        """Dérive le budget de complexité autorisé selon la nature de la demande."""
        if explicit_full_rewrite:
            return SimplicityBudget(
                max_modified_files=10,
                max_added_lines=600,
                allow_new_packages=True,
                allow_new_dependencies=True,
                task_scope="EXPANSION",
            )

        task_type_lower = task_type.lower()
        if "fix" in task_type_lower or "bug" in task_type_lower or "patch" in task_type_lower:
            return SimplicityBudget(
                max_modified_files=2,
                max_added_lines=50,
                allow_new_packages=False,
                allow_new_dependencies=False,
                task_scope="PATCH",
            )

        # Feature standard
        return SimplicityBudget(
            max_modified_files=4,
            max_added_lines=180,
            allow_new_packages=False,
            allow_new_dependencies=False,
            task_scope="STANDARD",
        )

    @classmethod
    def evaluate_diff(cls, diff_content: str, budget: SimplicityBudget) -> SimplicityReport:
        """Analyse un diff unifié (git diff) et valide le respect du budget."""
        modified_files: Set[str] = set()
        added_lines_count = 0
        new_packages: List[str] = []
        new_dependencies: List[str] = []
        violations: List[str] = []

        current_file = None
        for line in diff_content.splitlines():
            if line.startswith("diff --git") or line.startswith("+++ b/"):
                parts = line.split()
                if len(parts) >= 2:
                    raw_path = parts[-1].replace("b/", "")
                    current_file = raw_path
                    modified_files.add(raw_path)

            elif line.startswith("+") and not line.startswith("+++"):
                added_lines_count += 1
                # Vérifier si on tente d'ajouter des dépendances
                if current_file and ("requirements" in current_file or "pyproject" in current_file or "package.json" in current_file):
                    if not budget.allow_new_dependencies:
                        new_dependencies.append(line.strip())

        # Détection de nouveaux packages créés (nouveaux dossiers)
        for f in modified_files:
            p = Path(f)
            if len(p.parts) > 3 and not budget.allow_new_packages:
                new_packages.append(str(p.parent))

        # Vérification du budget
        if len(modified_files) > budget.max_modified_files:
            violations.append(
                f"Trop de fichiers modifiés : {len(modified_files)} (Budget max: {budget.max_modified_files})"
            )

        if added_lines_count > budget.max_added_lines:
            violations.append(
                f"Volume de code excessif : +{added_lines_count} lignes (Budget max: +{budget.max_added_lines} lignes)"
            )

        if new_dependencies and not budget.allow_new_dependencies:
            violations.append(
                f"Ajout de nouvelles dépendances non autorisées ({len(new_dependencies)} lignes détectées)."
            )

        passed = len(violations) == 0
        pruning_suggestion = None
        if not passed:
            pruning_suggestion = (
                f"Action requise (Single-Shot Pruning / Overfitting Guard) : Élaguer la solution. Réutiliser les classes existantes, "
                f"supprimer les abstractions intermédiaires non requises et concentrer l'implémentation sur "
                f"le diff minimal viable (plafond cible: {budget.max_added_lines} lignes sur max {budget.max_modified_files} fichiers)."
            )

        return SimplicityReport(
            passed=passed,
            modified_files_count=len(modified_files),
            added_lines_count=added_lines_count,
            new_packages_detected=list(set(new_packages)),
            new_dependencies_detected=new_dependencies,
            violations=violations,
            pruning_suggestion=pruning_suggestion,
        )
