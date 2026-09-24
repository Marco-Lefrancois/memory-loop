"""
Package critic/__init__.py — Façade du moteur Avocat du Diable (MLOOP-172-BE).

Expose les symboles publics gelés (ADR-0202) :
  - DevilAdvocateCritic  : moteur d'analyse contradictoire
  - DevilAdvocateCritique : rapport d'audit complet

Délègue chaque axe à son sous-module dédié :
  - _critic_models   : dataclasses
  - _critic_analysis : axes 1-4
  - _critic_api      : checks F/G + persistance
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from src.engine.rubber_duck.critic._critic_models import DevilAdvocateCritique
from src.engine.rubber_duck.critic._critic_analysis import (
    analyse_business_discernment,
    analyse_ecosystem_coherence,
    analyse_gherkin_pillars,
    analyse_technical_rigor,
    build_recommendations,
    compute_status_and_scores,
    generate_patches,
)
from src.engine.rubber_duck.critic._critic_api import (
    run_api_traceability_checks,
    persist_critique_to_evidence,
    extract_layer,
    extract_api_routes,
    has_contract_matrix,
    has_oq_exemption,
    _PHANTOM_ROUTE_TOKENS,
)
from src.utils.logger import get_logger

logger = get_logger("rubber_duck.critic")


class DevilAdvocateCritic:
    """Moteur d'analyse contradictoire avec discernement et rigueur."""

    # ── Méthodes de classe publiques — rétrocompatibilité callers (ADR-0202) ──

    _PHANTOM_ROUTE_TOKENS = _PHANTOM_ROUTE_TOKENS

    @classmethod
    def _extract_layer(cls, content: str) -> Optional[str]:
        """Délégué vers _critic_api.extract_layer (rétrocompatibilité)."""
        return extract_layer(content)

    @classmethod
    def _extract_api_routes(cls, content: str) -> list[str]:
        """Délégué vers _critic_api.extract_api_routes (rétrocompatibilité)."""
        return extract_api_routes(content)

    @classmethod
    def _has_contract_matrix(cls, content: str) -> bool:
        """Délégué vers _critic_api.has_contract_matrix (rétrocompatibilité)."""
        return has_contract_matrix(content)

    @classmethod
    def _has_oq_exemption(cls, content: str) -> bool:
        """Délégué vers _critic_api.has_oq_exemption (rétrocompatibilité)."""
        return has_oq_exemption(content)

    @classmethod
    def _run_api_traceability_checks(
        cls, content: str, critical_flaws: list, silent_failures: list
    ) -> None:
        """Délégué vers _critic_api.run_api_traceability_checks (rétrocompatibilité)."""
        run_api_traceability_checks(content, critical_flaws, silent_failures)

    @classmethod
    def _persist_critique_to_evidence(
        cls, critique: "DevilAdvocateCritique", project_dir: "Path"
    ) -> None:
        """Délégué vers _critic_api.persist_critique_to_evidence (rétrocompatibilité)."""
        persist_critique_to_evidence(critique, project_dir)

    @classmethod
    def evaluate_story(
        cls,
        story_file: "Path | str",
        project_name: str,
        project_dir: Optional[Path] = None,
        db_path: Optional[Any] = None,
        persist_evidence: bool = True,
    ) -> DevilAdvocateCritique:
        """Exécute l'audit contradictoire approfondi sur un récit."""
        target_path = Path(story_file)
        if not target_path.exists():
            raise FileNotFoundError(f"Fichier story introuvable : {target_path}")

        content = target_path.read_text(encoding="utf-8", errors="ignore")
        story_id = target_path.stem

        fm_id_match = re.search(r"^id:\s*([A-Za-z0-9_-]+)", content, re.MULTILINE)
        if fm_id_match:
            story_id = fm_id_match.group(1).strip()

        critical_flaws: list[str] = []
        silent_failures: list[str] = []

        # Axe 1 : Discernement Métier
        business_score = analyse_business_discernment(content, critical_flaws)

        # Axe 2 : Cohérence Écosystème
        coherence_issues, coherence_score = analyse_ecosystem_coherence(target_path, project_dir)

        # Axe 3 : Rigueur Technique
        tech_score = analyse_technical_rigor(content, silent_failures)

        # Axe 4 : 4 Piliers Gherkin
        tech_score += analyse_gherkin_pillars(content, critical_flaws)

        # Axe 4b : Checks F/G — Traçabilité API & Anti-Invention de Routes
        run_api_traceability_checks(content, critical_flaws, silent_failures)

        # Patchs de remédiation
        patches = generate_patches(content, critical_flaws, silent_failures, story_id)

        # Score global & statut
        status, bs, cs, ts, overall = compute_status_and_scores(
            business_score,
            coherence_score,
            tech_score,
            coherence_issues,
            critical_flaws,
            silent_failures,
        )

        recommendations = build_recommendations(silent_failures, coherence_issues)

        critique = DevilAdvocateCritique(
            story_id=story_id,
            project_name=project_name,
            timestamp=datetime.now().isoformat(),
            status=status,
            business_discernment_score=bs,
            ecosystem_coherence_score=cs,
            technical_rigor_score=ts,
            overall_trust_score=overall,
            critical_flaws=critical_flaws,
            silent_failures=silent_failures,
            coherence_issues=coherence_issues,
            remediation_patches=patches,
            recommendations=recommendations,
        )

        if persist_evidence:
            persist_critique_to_evidence(critique, project_dir or Path.cwd())

        return critique


__all__ = ["DevilAdvocateCritic", "DevilAdvocateCritique"]
