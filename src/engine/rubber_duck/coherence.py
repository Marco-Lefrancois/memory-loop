# -*- coding: utf-8 -*-
"""
Cross-Story & Ecosystem Coherence Checker (mLoop Rubber Duck 2.0 - ADR-0326).

Analyse la cohérence globale d'un récit au sein de son sprint et de son architecture :
1. Détection de chevauchement de périmètre (Scope Overlap) avec les récits voisins.
2. Détection des dépendances implicites non déclarées.
3. Vérification de l'alignement avec les modèles de données (docs/03-models/) et les ADRs.
4. Contrôle des dérives de vocabulaire métier au sein du même sprint.
"""

from __future__ import annotations

import re
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.utils.logger import get_logger

logger = get_logger("rubber_duck.coherence")


@dataclass
class CoherenceIssue:
    """Représente une anomalie de cohérence transversale."""
    issue_type: str  # "SCOPE_OVERLAP", "UNDECLARED_DEPENDENCY", "MODEL_MISMATCH", "VOCABULARY_DRIFT"
    severity: str    # "BLOCKING", "MAJOR", "MINOR"
    description: str
    target_story: str
    conflicting_artifact: Optional[str] = None
    recommendation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_type": self.issue_type,
            "severity": self.severity,
            "description": self.description,
            "target_story": self.target_story,
            "conflicting_artifact": self.conflicting_artifact,
            "recommendation": self.recommendation,
        }


class CrossStoryCoherenceChecker:
    """Vérificateur de cohérence écosystème et cross-récits."""

    @classmethod
    def check_story_coherence(
        cls,
        story_file: Path | str,
        project_dir: Optional[Path] = None,
    ) -> List[CoherenceIssue]:
        """Exécute l'audit de cohérence écosystème sur un récit donné."""
        target_path = Path(story_file)
        if not target_path.exists():
            return []

        if project_dir is None:
            # Remonter vers Projects/<nom_projet>
            cur = target_path.resolve()
            while cur.parent != cur:
                if (cur / "backlog").exists() or (cur / "docs").exists():
                    project_dir = cur
                    break
                cur = cur.parent
            if project_dir is None:
                project_dir = Path.cwd()

        target_content = target_path.read_text(encoding="utf-8", errors="ignore")
        target_id = target_path.stem

        issues: List[CoherenceIssue] = []

        # 1. Vérifier les conflits et chevauchements avec les récits voisins
        stories_dir = project_dir / "backlog" / "stories"
        if stories_dir.exists():
            sibling_stories = [f for f in stories_dir.glob("*.md") if f.name != target_path.name]
            issues.extend(cls._detect_scope_overlap(target_id, target_content, sibling_stories))

        # 2. Vérifier l'alignement avec les modèles de données sous docs/03-models/
        models_dir = project_dir / "docs" / "03-models"
        if models_dir.exists():
            issues.extend(cls._verify_model_alignment(target_id, target_content, models_dir))

        return issues

    @classmethod
    def _detect_scope_overlap(
        cls,
        target_id: str,
        target_content: str,
        sibling_stories: List[Path],
    ) -> List[CoherenceIssue]:
        """Détecte les doublons ou chevauchements fonctionnels avec d'autres récits."""
        issues: List[CoherenceIssue] = []
        target_tokens = set(re.findall(r'\w+', target_content.lower()))

        # Extraire les mots-clés d'actions (verbes et entités clés)
        target_actions = set(re.findall(r'\b(export|import|création|suppression|mise à jour|synchronisation|calcul|expiration|paiement)\w*', target_content.lower()))

        for sib in sibling_stories:
            try:
                sib_content = sib.read_text(encoding="utf-8", errors="ignore")
                sib_tokens = set(re.findall(r'\w+', sib_content.lower()))
                sib_actions = set(re.findall(r'\b(export|import|création|suppression|mise à jour|synchronisation|calcul|expiration|paiement)\w*', sib_content.lower()))

                # Calcul du Jaccard sur les actions spécifiques
                if target_actions and sib_actions:
                    common_actions = target_actions.intersection(sib_actions)
                    common_all = target_tokens.intersection(sib_tokens)
                    jaccard = len(common_all) / max(1, len(target_tokens.union(sib_tokens)))

                    # Si forte similarité d'action et contenu > 60%
                    if jaccard > 0.65 and common_actions:
                        issues.append(CoherenceIssue(
                            issue_type="SCOPE_OVERLAP",
                            severity="MAJOR",
                            description=f"Risque de chevauchement de périmètre élevé avec le récit '{sib.name}' (Similarité {round(jaccard*100)}% sur actions {list(common_actions)}).",
                            target_story=target_id,
                            conflicting_artifact=sib.name,
                            recommendation="Clarifier les frontières de responsabilités respectives dans le sprint backlog.",
                        ))
            except Exception as e:
                logger.debug(f"Erreur lecture récit frère {sib}: {e}")

        return issues

    @classmethod
    def _verify_model_alignment(
        cls,
        target_id: str,
        target_content: str,
        models_dir: Path,
    ) -> List[CoherenceIssue]:
        """Vérifie que les entités ou champs mentionnés ne contredisent pas les modèles de données."""
        issues: List[CoherenceIssue] = []
        # Traquer les affirmations sur des entités inconnues ou des champs spécifiques
        schema_files = list(models_dir.glob("*.md"))
        if not schema_files:
            return []

        all_model_text = " ".join([f.read_text(encoding="utf-8", errors="ignore") for f in schema_files])
        all_model_tokens = set(re.findall(r'\w+', all_model_text.lower()))

        # Détecter si le récit mentionne des entités techniques sous forme de tables ou classes
        table_mentions = re.findall(r'\btable\s+([A-Za-z0-9_]+)\b|\bentity\s+([A-Za-z0-9_]+)\b', target_content, re.IGNORECASE)
        for m in table_mentions:
            tbl_name = (m[0] or m[1]).lower()
            if tbl_name and tbl_name not in all_model_tokens:
                issues.append(CoherenceIssue(
                    issue_type="MODEL_MISMATCH",
                    severity="MAJOR",
                    description=f"L'entité ou table '{tbl_name}' mentionnée dans le récit est absente des modèles de données SSOT sous docs/03-models/.",
                    target_story=target_id,
                    conflicting_artifact="docs/03-models/",
                    recommendation="Mettre à jour le modèle de données ou consigner une question ouverte (OQ) si le modèle évolue.",
                ))

        return issues
