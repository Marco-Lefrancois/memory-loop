# -*- coding: utf-8 -*-
"""
Rubber Duck Remediator Engine (mLoop Core - ADR-0326).

Génère des propositions concrètes et chirurgicales de scénarios Gherkin
et de critères d'acceptation pour réparer immédiatement les failles décelées.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class RemediationPatch:
    """Représente une suggestion de correctif chirurgical."""
    pillar_target: str       # "Pilier 1 : Nominal", "Pilier 2 : Exceptions", "Pilier 3 : Résilience", "Pilier 4 : UX"
    issue_addressed: str
    suggested_gherkin: str
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pillar_target": self.pillar_target,
            "issue_addressed": self.issue_addressed,
            "suggested_gherkin": self.suggested_gherkin,
            "rationale": self.rationale,
        }


class RubberDuckRemediator:
    """Générateur de correctifs et de scénarios de remédiation."""

    @classmethod
    def generate_remediation_patches(
        cls,
        story_content: str,
        detected_flaws: List[str],
        story_id: str = "US-XXX",
    ) -> List[RemediationPatch]:
        """Produit des correctifs Gherkin ciblés pour chaque angle mort identifié."""
        patches: List[RemediationPatch] = []

        # 1. Remédiation si Résilience (Pilier 3) défaillante ou absente
        if any(term in f.lower() for f in detected_flaws for term in ["résilience", "resilience", "timeout", "offline", "coupure", "indisponib", "503"]):
            patches.append(RemediationPatch(
                pillar_target="Pilier 3 : Résilience & Mode Dégradé",
                issue_addressed="Manque de couverture sur la perte de réseau et les indisponibilités de service.",
                suggested_gherkin="""### Pilier 3 : Résilience
Étant donné une perte de connectivité réseau ou un timeout de l'API (503)
Quand l'utilisateur déclenche l'action principale
Alors le système affiche une notification d'avertissement 'Service temporairement indisponible'
Et les données saisies sont préservées dans l'état local sans perte ni rechargement.""",
                rationale="Garantit que l'application ne crash pas en cas de coupure réseau inopinée et protège la saisie utilisateur."
            ))

        # 2. Remédiation si Concurrence / Double-clic non couvert
        if any(term in f.lower() for f in detected_flaws for term in ["concurren", "double-clic", "double clic", "anti-rebond", "soumission multiple", "race"]):
            patches.append(RemediationPatch(
                pillar_target="Pilier 3 : Résilience (Concurrence)",
                issue_addressed="Absence de protection contre la double-soumission rapide.",
                suggested_gherkin="""### Pilier 3 : Résilience (Anti-Rebond & Concurrence)
Étant donné un formulaire en cours de validation
Quand l'utilisateur effectue un double-clic rapide sur le bouton de soumission
Alors le bouton est immédiatement désactivé avec un indicateur de chargement
Et une seule requête de traitement est émise vers l'API.""",
                rationale="Évite les écritures dupliquées et les transactions fantômes en base de données."
            ))

        # 3. Remédiation si UX / Accessibilité (Pilier 4) insuffisant
        if any(term in f.lower() for f in detected_flaws for term in ["ux", "accessibilit", "focus", "loading", "chargement", "clavier", "aria"]):
            patches.append(RemediationPatch(
                pillar_target="Pilier 4 : UX & Accessibilité",
                issue_addressed="Spécification insuffisante des états de chargement et de la navigation clavier.",
                suggested_gherkin="""### Pilier 4 : UX & Accessibilité
Étant donné l'ouverture du modal de confirmation
Quand l'interface s'affiche
Alors le focus clavier est automatiquement positionné sur le bouton principal
Et la touche 'Échap' permet de fermer la fenêtre sans valider l'action.""",
                rationale="Assure la conformité aux normes d'accessibilité RGAA et offre une ergonomie fluide au clavier."
            ))

        return patches
