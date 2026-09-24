"""
_critic_analysis.py — Analyse contradictoire sur 4 axes (MLOOP-172-BE).

Contient la logique d'évaluation de DevilAdvocateCritic :
  - Axe 1 : Discernement Métier
  - Axe 2 : Cohérence Écosystème & SSOT
  - Axe 3 : Rigueur Technique & Défaillances Silencieuses
  - Axe 4 : Challenge des 4 Piliers Gherkin

Conforme ADR-0369 : zéro except pass nu.
Conforme ADR-0202 : <300 L / 15 Ko.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional, Tuple

from src.engine.rubber_duck.coherence import CrossStoryCoherenceChecker, CoherenceIssue
from src.engine.rubber_duck.remediator import RubberDuckRemediator, RemediationPatch
from src.utils.logger import get_logger

logger = get_logger("rubber_duck.critic._critic_analysis")

# ── Patterns de détection ─────────────────────────────────────────────────────

_VAGUE_PATTERNS = [
    (
        r"(?<!double-clic\s)(?<!clic\s)\b(?:rapide|facile|approprié|performant|si possible|éventuellement)\b",
        "Présence de termes d'évaluation subjectifs sans métrique chiffrée.",
    ),
    (
        r"\b(?:interface moderne|bel écran|affichage clair|intuitif)\b",
        "Formulations vagues sur l'UX. Exiger la spécification des composants et interactions.",
    ),
]

_FAILURE_MODES = [
    (
        r"(?:timeout|délai d'attente|503|408|coupure réseau|offline)",
        "Absence de scénario en cas de timeout API ou de coupure réseau inopinée.",
    ),
    (
        r"(?:double-clic|double clic|soumission multiple|anti-rebond|concurren)",
        "Absence de protection contre la soumission multiple rapide (anti-rebond).",
    ),
    (
        r"(?:session expirée|token expiré|401|non authentifié)",
        "Absence de gestion de l'expiration de session en cours de formulaire.",
    ),
    (
        r"(?:données partielles|champ vide|valeur null|caractère spécial)",
        "Absence de validation des saisies extrêmes ou champs incomplets.",
    ),
]


# ── Axe 1 : Discernement Métier ───────────────────────────────────────────────


def analyse_business_discernment(content: str, critical_flaws: List[str]) -> float:
    """
    Axe 1 : Détecte les exigences creuses, termes vagues et absence de contexte métier.

    Returns:
        Score 0-100 (100 = aucun problème).
    """
    score = 100.0

    for pat, desc in _VAGUE_PATTERNS:
        matches = re.findall(pat, content, re.IGNORECASE)
        if matches:
            critical_flaws.append(f"{desc} (Termes relevés : {list(set(matches))})")
            score -= 15.0

    if "## Critères d'acceptation" not in content and "## Contexte métier" not in content:
        critical_flaws.append(
            "Absence de contextualisation d'affaires ou de critères d'acceptation formalisés."
        )
        score -= 30.0

    return score


# ── Axe 2 : Cohérence Écosystème & SSOT ──────────────────────────────────────


def analyse_ecosystem_coherence(
    story_file: Path, project_dir: Optional[Path]
) -> Tuple[List[CoherenceIssue], float]:
    """
    Axe 2 : Vérifie la cohérence avec les autres récits et le modèle de données.

    Returns:
        (coherence_issues, score_0_100)
    """
    coherence_issues = CrossStoryCoherenceChecker.check_story_coherence(
        story_file=story_file,
        project_dir=project_dir,
    )
    score = max(0.0, 100.0 - len(coherence_issues) * 20.0)
    return coherence_issues, score


# ── Axe 3 : Rigueur Technique & Défaillances Silencieuses ────────────────────


def analyse_technical_rigor(content: str, silent_failures: List[str]) -> float:
    """
    Axe 3 : Traque les cas limites et modes de défaillance silencieuse.

    Returns:
        Score 0-100 (100 = aucun problème).
    """
    score = 100.0

    for pat, desc in _FAILURE_MODES:
        if not re.search(pat, content, re.IGNORECASE):
            silent_failures.append(desc)
            score -= 12.0

    return score


# ── Axe 4 : Challenge des 4 Piliers Gherkin ──────────────────────────────────


def analyse_gherkin_pillars(content: str, critical_flaws: List[str]) -> float:
    """
    Axe 4 : Vérifie la présence des 4 piliers Gherkin obligatoires.

    Returns:
        Score décrément (0 si tous présents, -N*10 par pilier manquant).
    """
    has_nominal = bool(re.search(r"(?:nominal|succès)", content, re.IGNORECASE))
    has_exception = bool(re.search(r"(?:exception|erreur|rejet)", content, re.IGNORECASE))
    has_resilience = bool(
        re.search(r"(?:résilience|resilience|timeout|dégradé)", content, re.IGNORECASE)
    )
    has_ux = bool(re.search(r"(?:ux|accessibilité|clavier|focus|aria)", content, re.IGNORECASE))

    missing = []
    if not has_nominal:
        missing.append("Pilier 1 (Nominal)")
    if not has_exception:
        missing.append("Pilier 2 (Exceptions)")
    if not has_resilience:
        missing.append("Pilier 3 (Résilience)")
    if not has_ux:
        missing.append("Pilier 4 (UX / Accessibilité)")

    if missing:
        critical_flaws.append(
            f"Gherkin 4-Piliers incomplet. Piliers manquants : {', '.join(missing)}."
        )
        return -len(missing) * 10.0

    return 0.0


# ── Score global & statut ─────────────────────────────────────────────────────


def compute_status_and_scores(
    business_score: float,
    coherence_score: float,
    tech_score: float,
    coherence_issues: List[CoherenceIssue],
    critical_flaws: List[str],
    silent_failures: List[str],
) -> Tuple[str, float, float, float, float]:
    """
    Calcule les scores bornés et détermine le statut final.

    Returns:
        (status, business_score, coherence_score, tech_score, overall_score)
    """
    bs = max(0.0, min(100.0, business_score))
    cs = max(0.0, min(100.0, coherence_score))
    ts = max(0.0, min(100.0, tech_score))
    overall = round((bs * 0.35) + (cs * 0.30) + (ts * 0.35), 1)

    blocking_count = len([c for c in coherence_issues if c.severity == "BLOCKING"])
    if blocking_count > 0 or len(critical_flaws) >= 3 or overall < 50.0:
        status = "REJECTED"
    elif len(critical_flaws) > 0 or len(silent_failures) >= 2 or overall < 75.0:
        status = "ACTION_REQUIRED"
    else:
        status = "APPROVED"

    return status, bs, cs, ts, overall


# ── Génération des patchs de remédiation ─────────────────────────────────────


def generate_patches(
    content: str, critical_flaws: List[str], silent_failures: List[str], story_id: str
) -> List[RemediationPatch]:
    """Génère les patchs de remédiation chirurgicale."""
    all_flaws = critical_flaws + silent_failures
    return RubberDuckRemediator.generate_remediation_patches(
        story_content=content,
        detected_flaws=all_flaws,
        story_id=story_id,
    )


# ── Génération des recommandations ────────────────────────────────────────────


def build_recommendations(
    silent_failures: List[str], coherence_issues: List[CoherenceIssue]
) -> List[str]:
    """Construit la liste des recommandations."""
    recs: List[str] = []
    if silent_failures:
        recs.append(
            "Compléter les scénarios de test pour couvrir les modes de défaillance silencieuse relevés."
        )
    if coherence_issues:
        recs.append(
            "Vérifier les frontières de périmètre avec les récits voisins du sprint backlog."
        )
    return recs
