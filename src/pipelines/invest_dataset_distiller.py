# -*- coding: utf-8 -*-
"""
INVEST & Gherkin Dataset Distiller (mLoop Core - ADR-0328).

Inspiré du pipeline de distillation de dataset (Decoding AI / Aug 2026) :
Génère des jeux de données d'instructions synthétiques (Instruct Dataset) au format JSONL
à partir des gabarits et récits de référence pour entraîner (Fine-Tuning QLoRA / Unsloth)
des petits modèles locaux spécialisés dans l'audit INVEST et la vérification des 4 Piliers Gherkin.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


SYSTEM_PROMPT = (
    "Tu es l'agent Sentinel de mLoop. Ton rôle est d'auditer les User Stories contre "
    "le Gold Standard (story_template.md), les critères INVEST et les 4 Piliers Gherkin "
    "(Nominal, Exceptions, Résilience, UX). Décèle impérativement toute fuite de code physique "
    "ou dérive de gabarit."
)


@dataclass
class DistillationExample:
    """Exemple d'entraînement d'instruction unitaire."""
    example_id: str
    instruction: str
    input_text: str
    output_text: str
    category: str  # "compliant", "missing_gherkin", "code_leak", "invest_defect"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_chatml(self) -> Dict[str, Any]:
        """Format ChatML standard compatible Unsloth, Hugging Face et OpenAI."""
        return {
            "id": self.example_id,
            "category": self.category,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"{self.instruction}\n\n```markdown\n{self.input_text}\n```"},
                {"role": "assistant", "content": self.output_text},
            ],
            "metadata": self.metadata,
        }


class InvestDatasetDistiller:
    """Moteur de distillation et de génération de dataset d'audit."""

    def __init__(self, project_path: Optional[Path | str] = None) -> None:
        self.project_path = Path(project_path) if project_path else Path(".")
        self.output_dir = self.project_path / "memory" / "datasets"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_distilled_dataset(self) -> List[DistillationExample]:
        """Génère une suite complète d'exemples d'audit positifs et contradictoires."""
        examples: List[DistillationExample] = []

        # 1. Exemple Positif : Récit Conforme Gold Standard
        compliant_story = """---
id: US-01-AUTH
jira_key: MMA-1001
epic_key: MMA-1000
type: Story
title: Authentification biométrique
tags: [auth, security]
status: READY_FOR_DEV
---

## Description
En tant qu'utilisateur mobile, je souhaite m'authentifier via FaceID/TouchID afin d'accéder rapidement à mon compte.

---

## Contexte
L'authentification s'appuie sur le gestionnaire de sécurité natif de l'OS.

### Interface et UX
Un dialogue modal natif s'affiche invitant l'utilisateur à présenter son empreinte ou visage.

### Liste Call to Actions
- Bouton : S'authentifier
- Bouton : Utiliser mon mot de passe

---

## Règles d'affaires
- **Validation Biométrique** : L'accès est déverrouillé uniquement après succès de l'OS.
- **Repli Mot de Passe** : En cas de 3 échecs, l'écran propose la saisie du code PIN.

---

## Contrats UI & API Backend
- Endpoint API : `POST /api/v1/auth/session`
- Code statut retour : 200 OK avec jeton de session.

---

## Scénarios de test

### Scénario 1 (Nominal) : Authentification réussie
- **Étant donné** un utilisateur avec biométrie activée
- **Quand** il appuie sur "S'authentifier" et valide son empreinte
- **Alors** la session est ouverte et il est redirigé vers l'accueil

### Scénario 2 (Exceptions) : Échec de reconnaissance
- **Étant donné** un utilisateur sur l'écran de verrouillage
- **Quand** l'OS renvoie un échec de reconnaissance
- **Alors** un message invite à réessayer

### Scénario 3 (Résilience) : Absence de capteur
- **Étant donné** un appareil sans capteur biométrique
- **Quand** l'application s'ouvre
- **Alors** le formulaire bascule directement sur le mot de passe

### Scénario 4 (UX) : Animation de succès
- **Étant donné** une validation réussie
- **Quand** le retour API est validé
- **Alors** un indicateur vert confirme l'accès
"""

        examples.append(DistillationExample(
            example_id="EX-INVEST-001",
            instruction="Audite cette User Story contre les 4 Piliers Gherkin, l'isolation technique et les critères INVEST.",
            input_text=compliant_story.strip(),
            output_text=(
                "### ✅ Rapport d'Audit Sentinel : APPROBATION\n\n"
                "- **Critères INVEST** : Conforme (Indépendant, Négociable, Valeur claire, Estimable, Small, Testable).\n"
                "- **4 Piliers Gherkin** : Validé (1. Nominal, 2. Exceptions, 3. Résilience, 4. UX).\n"
                "- **Isolation Technique** : Aucune fuite de syntaxe physique ou méthode interne.\n"
                "- **Verdict** : `APPROVE` — Statut `READY_FOR_DEV` autorisé."
            ),
            category="compliant",
            metadata={"source": "gold_standard"},
        ))

        # 2. Exemple Négatif 1 : Fuite technique et méthode physique
        leak_story = compliant_story.replace(
            "- **Validation Biométrique** : L'accès est déverrouillé uniquement après succès de l'OS.",
            "- **Validation Biométrique** : La méthode `BiometricService.VerifyFingerprintAsync()` doit être invoquée dans `MauiProgram.cs`."
        )
        examples.append(DistillationExample(
            example_id="EX-INVEST-002",
            instruction="Audite cette User Story contre les 4 Piliers Gherkin, l'isolation technique et les critères INVEST.",
            input_text=leak_story.strip(),
            output_text=(
                "### ❌ Rapport d'Audit Sentinel : REJET\n\n"
                "- **Fuite Technique Détectée (Règle Renaud / ADR-0319)** : Présence de méthode de code physique (`BiometricService.VerifyFingerprintAsync()`) et de fichier de code (`MauiProgram.cs`).\n"
                "- **Correction requise** : Remplacer par une description fonctionnelle en langage naturel clair.\n"
                "- **Verdict** : `REJECT` — Bloqué avant handoff."
            ),
            category="code_leak",
            metadata={"anomaly": "technical_leak"},
        ))

        # 3. Exemple Négatif 2 : Scénarios Gherkin manquants (1 seul scénario)
        incomplete_gherkin_story = re.sub(r"### Scénario 2[\s\S]*", "", compliant_story)
        examples.append(DistillationExample(
            example_id="EX-INVEST-003",
            instruction="Audite cette User Story contre les 4 Piliers Gherkin, l'isolation technique et les critères INVEST.",
            input_text=incomplete_gherkin_story.strip(),
            output_text=(
                "### ❌ Rapport d'Audit Sentinel : REJET\n\n"
                "- **4 Piliers Gherkin Incomplets (ADR-0301)** : Seulement 1 scénario sur 4 fourni.\n"
                "- **Scénarios manquants** : Exceptions (Scénario 2), Résilience (Scénario 3), UX (Scénario 4).\n"
                "- **Verdict** : `REJECT` — Bloqué."
            ),
            category="missing_gherkin",
            metadata={"anomaly": "missing_gherkin_pillars"},
        ))

        return examples

    def export_dataset_jsonl(self, examples: Optional[List[DistillationExample]] = None, filename: str = "invest_gherkin_distilled.jsonl") -> Path:
        """Exporte le dataset au format JSONL ChatML prêt pour fine-tuning."""
        if examples is None:
            examples = self.generate_distilled_dataset()

        out_file = self.output_dir / filename
        with open(out_file, "w", encoding="utf-8") as f:
            for ex in examples:
                f.write(json.dumps(ex.to_chatml(), ensure_ascii=False) + "\n")

        return out_file
