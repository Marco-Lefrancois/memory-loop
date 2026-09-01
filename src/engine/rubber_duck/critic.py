# -*- coding: utf-8 -*-
"""
Devil's Advocate Critic Engine (mLoop Rubber Duck 2.0 - ADR-0326).

Moteur de critique contradictoire qualitative sur 4 axes de fond :
1. Discernement Métier (Intention d'affaires, valeur réelle, détection de fausses bonnes idées).
2. Cohérence Écosystème (Cross-récits, modèles de données, ADRs).
3. Rigueur & Défaillances Silencieuses (Timeouts, concurrence, mode dégradé).
4. Challenge des 4 Piliers Gherkin & Remédiation Chirurgicale.
"""

from __future__ import annotations

import re
import json
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.engine.rubber_duck.coherence import CrossStoryCoherenceChecker, CoherenceIssue
from src.engine.rubber_duck.remediator import RubberDuckRemediator, RemediationPatch
from src.engine.fact_search.retriever import FactSearchRetriever
from src.utils.logger import get_logger

logger = get_logger("rubber_duck.critic")


@dataclass
class DevilAdvocateCritique:
    """Rapport d'audit complet de l'Avocat du Diable."""
    story_id: str
    project_name: str
    timestamp: str
    status: str  # "APPROVED", "ACTION_REQUIRED", "REJECTED"
    business_discernment_score: float  # 0-100
    ecosystem_coherence_score: float   # 0-100
    technical_rigor_score: float       # 0-100
    overall_trust_score: float         # 0-100
    critical_flaws: List[str] = field(default_factory=list)
    silent_failures: List[str] = field(default_factory=list)
    coherence_issues: List[CoherenceIssue] = field(default_factory=list)
    remediation_patches: List[RemediationPatch] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "story_id": self.story_id,
            "project_name": self.project_name,
            "timestamp": self.timestamp,
            "status": self.status,
            "scores": {
                "business_discernment": self.business_discernment_score,
                "ecosystem_coherence": self.ecosystem_coherence_score,
                "technical_rigor": self.technical_rigor_score,
                "overall_trust": self.overall_trust_score,
            },
            "critical_flaws": self.critical_flaws,
            "silent_failures": self.silent_failures,
            "coherence_issues": [c.to_dict() for c in self.coherence_issues],
            "remediation_patches": [p.to_dict() for p in self.remediation_patches],
            "recommendations": self.recommendations,
        }


class DevilAdvocateCritic:
    """Moteur d'analyse contradictoire avec discernement et rigueur."""

    @classmethod
    def evaluate_story(
        cls,
        story_file: Path | str,
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

        # Extraire l'ID YAML si présent
        fm_id_match = re.search(r'^id:\s*([A-Za-z0-9_-]+)', content, re.MULTILINE)
        if fm_id_match:
            story_id = fm_id_match.group(1).strip()

        critical_flaws: List[str] = []
        silent_failures: List[str] = []
        recommendations: List[str] = []

        # ── 1. AXE 1 : DISCERNEMENT MÉTIER ─────────────────────────────────────
        business_score = 100.0
        
        # A. Détection des exigences creuses ou floues (excluant expressions techniques comme double-clic rapide)
        vague_patterns = [
            (r"(?<!double-clic\s)(?<!clic\s)\b(?:rapide|facile|approprié|performant|si possible|éventuellement)\b", "Présence de termes d'évaluation subjectifs sans métrique chiffrée."),
            (r"\b(?:interface moderne|bel écran|affichage clair|intuitif)\b", "Formulations vagues sur l'UX. Exiger la spécification des composants et interactions."),
        ]
        for pat, desc in vague_patterns:
            matches = re.findall(pat, content, re.IGNORECASE)
            if matches:
                critical_flaws.append(f"{desc} (Termes relevés : {list(set(matches))})")
                business_score -= 15.0

        # B. Vérification de la complétude INVEST (Dépendance et Testabilité)
        if "## Critères d'acceptation" not in content and "## Contexte métier" not in content:
            critical_flaws.append("Absence de contextualisation d'affaires ou de critères d'acceptation formalisés.")
            business_score -= 30.0

        # ── 2. AXE 2 : COHÉRENCE ÉCOSYSTÈME & SSOT ────────────────────────────
        coherence_issues = CrossStoryCoherenceChecker.check_story_coherence(
            story_file=target_path,
            project_dir=project_dir,
        )
        coherence_score = 100.0 - (len(coherence_issues) * 20.0)

        # ── 3. AXE 3 : RIGUEUR TECHNIQUE & DÉFAILLANCES SILENCIEUSES ──────────
        tech_score = 100.0

        # Traque des cas limites méchants (Silent Failure Modes)
        failure_modes = [
            (r"(?:timeout|délai d'attente|503|408|coupure réseau|offline)", "Absence de scénario en cas de timeout API ou de coupure réseau inopinée."),
            (r"(?:double-clic|double clic|soumission multiple|anti-rebond|concurren)", "Absence de protection contre la soumission multiple rapide (anti-rebond)."),
            (r"(?:session expirée|token expiré|401|non authentifié)", "Absence de gestion de l'expiration de session en cours de formulaire."),
            (r"(?:données partielles|champ vide|valeur null|caractère spécial)", "Absence de validation des saisies extrêmes ou champs incomplets."),
        ]

        for pat, desc in failure_modes:
            if not re.search(pat, content, re.IGNORECASE):
                silent_failures.append(desc)
                tech_score -= 12.0

        # ── 4. AXE 4 : CHALLENGE DES 4 PILIERS GHERKIN & REMÉDIATION ──────────
        scenarios = re.findall(r"(?:###\s*(?:Pilier\s*\d+|Scénario|1\.|2\.|3\.|4\.))", content, re.IGNORECASE)
        has_nominal = bool(re.search(r"(?:nominal|succès|nominal)", content, re.IGNORECASE))
        has_exception = bool(re.search(r"(?:exception|erreur|rejet)", content, re.IGNORECASE))
        has_resilience = bool(re.search(r"(?:résilience|resilience|timeout|dégradé)", content, re.IGNORECASE))
        has_ux = bool(re.search(r"(?:ux|accessibilité|clavier|focus|aria)", content, re.IGNORECASE))

        missing_pillars = []
        if not has_nominal: missing_pillars.append("Pilier 1 (Nominal)")
        if not has_exception: missing_pillars.append("Pilier 2 (Exceptions)")
        if not has_resilience: missing_pillars.append("Pilier 3 (Résilience)")
        if not has_ux: missing_pillars.append("Pilier 4 (UX / Accessibilité)")

        if missing_pillars:
            critical_flaws.append(f"Gherkin 4-Piliers incomplet. Piliers manquants : {', '.join(missing_pillars)}.")
            tech_score -= len(missing_pillars) * 10.0

        # ── 5. GÉNÉRATION DES PATCHS DE REMÉDIATION CHIRURGICALE ───────────────
        all_flaws_for_remediation = critical_flaws + silent_failures
        patches = RubberDuckRemediator.generate_remediation_patches(
            story_content=content,
            detected_flaws=all_flaws_for_remediation,
            story_id=story_id,
        )

        # ── 6. CALCUL DU SCORE GLOBAL & STATUT DU RAPPORT ──────────────────────
        business_score = max(0.0, min(100.0, business_score))
        coherence_score = max(0.0, min(100.0, coherence_score))
        tech_score = max(0.0, min(100.0, tech_score))
        overall_score = round((business_score * 0.35) + (coherence_score * 0.30) + (tech_score * 0.35), 1)

        blocking_count = len([c for c in coherence_issues if c.severity == "BLOCKING"])
        if blocking_count > 0 or len(critical_flaws) >= 3 or overall_score < 50.0:
            status = "REJECTED"
        elif len(critical_flaws) > 0 or len(silent_failures) >= 2 or overall_score < 75.0:
            status = "ACTION_REQUIRED"
        else:
            status = "APPROVED"

        if silent_failures:
            recommendations.append("Compléter les scénarios de test pour couvrir les modes de défaillance silencieuse relevés.")
        if coherence_issues:
            recommendations.append("Vérifier les frontières de périmètre avec les récits voisins du sprint backlog.")

        critique = DevilAdvocateCritique(
            story_id=story_id,
            project_name=project_name,
            timestamp=datetime.now().isoformat(),
            status=status,
            business_discernment_score=business_score,
            ecosystem_coherence_score=coherence_score,
            technical_rigor_score=tech_score,
            overall_trust_score=overall_score,
            critical_flaws=critical_flaws,
            silent_failures=silent_failures,
            coherence_issues=coherence_issues,
            remediation_patches=patches,
            recommendations=recommendations,
        )

        # ── 7. PERSISTANCE DANS L'EVIDENCEPACK ──────────────────────────────────
        if persist_evidence:
            cls._persist_critique_to_evidence(critique, project_dir or Path.cwd())

        return critique

    @classmethod
    def _persist_critique_to_evidence(cls, critique: DevilAdvocateCritique, project_dir: Path):
        """Injecte le rapport de l'Avocat du Diable dans l'EvidencePack du récit."""
        evidence_dir = project_dir / "memory" / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence_file = evidence_dir / f"{critique.story_id}_evidence.json"

        evidence_data: Dict[str, Any] = {}
        if evidence_file.exists():
            try:
                evidence_data = json.loads(evidence_file.read_text(encoding="utf-8"))
            except Exception:
                evidence_data = {}

        evidence_data["story_id"] = critique.story_id
        evidence_data["project_name"] = critique.project_name
        evidence_data["last_updated"] = critique.timestamp
        evidence_data["devil_advocate_review"] = critique.to_dict()

        evidence_file.write_text(json.dumps(evidence_data, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Rapport Avocat du Diable consigné dans {evidence_file}")
