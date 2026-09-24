# -*- coding: utf-8 -*-
"""
Tests unitaires pour EvalsEngine (Google Agents CLI Eval Standard - ADR-0308).
Conforme ADR-0369 (Python Senior) et ADR-0202 (<= 300 lignes).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.pipelines.evals import EvalsEngine, SENTINEL_EVAL_JUDGE_SYSTEM_PROMPT


class TestEvalsEngine(unittest.TestCase):
    """Suite de tests pour le moteur d'évaluation hybride Google Agents CLI Eval."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.tmp_dir.name)
        self.stories_dir = self.project_path / "backlog" / "stories"
        self.stories_dir.mkdir(parents=True, exist_ok=True)
        self.engine = EvalsEngine(project_name="test_proj")
        self.engine.project_path = self.project_path

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_system_prompt_presence(self) -> None:
        """Vérifie que le prompt LLM-as-a-judge contient les directives clés."""
        self.assertIn("Lint is a floor, not the goal", SENTINEL_EVAL_JUDGE_SYSTEM_PROMPT)
        self.assertIn("Anti-Sycophancy", SENTINEL_EVAL_JUDGE_SYSTEM_PROMPT)
        self.assertIn("RUBRIQUE D'ÉVALUATION", SENTINEL_EVAL_JUDGE_SYSTEM_PROMPT)

    def test_deterministic_checks_compliant(self) -> None:
        """Vérifie le passage des assertions déterministes sur un contenu propre."""
        valid_story = """---
id: US-101
status: READY_FOR_DEV
---
# US-101 : Paiement Sécurisé
En tant que client, je veux payer afin de finaliser ma commande.
"""
        checks, flaws = EvalsEngine._run_deterministic_checks(Path("dummy.md"), valid_story)
        self.assertTrue(checks["max_file_lines"])
        self.assertTrue(checks["frontmatter_valid"])
        self.assertTrue(checks["zero_local_hardcoded_paths"])
        self.assertTrue(checks["zero_code_snippets"])
        self.assertEqual(len(flaws), 0)

    def test_deterministic_checks_violations(self) -> None:
        """Vérifie la détection de violations mécaniques (code physique, chemins locaux, taille)."""
        bad_story = """---
id: US-102
---
# Titre
Voir documentation locale : file:///C:/Memory%20Loop/docs/spec.md
Voici le code d'implémentation :
```csharp
public class PaymentController {}
```
""" + "\n" * 310  # Dépasse 300 lignes

        checks, flaws = EvalsEngine._run_deterministic_checks(Path("bad.md"), bad_story)
        self.assertFalse(checks["max_file_lines"])
        self.assertFalse(checks["frontmatter_valid"])  # status manquant
        self.assertFalse(checks["zero_local_hardcoded_paths"])
        self.assertFalse(checks["zero_code_snippets"])
        self.assertEqual(len(flaws), 4)

    def test_rubric_scoring_phantom_route(self) -> None:
        """Vérifie la pénalité éliminatoire (0 pt) en cas d'hallucination de route."""
        content_with_phantom = """---
id: US-201
status: READY_FOR_DEV
---
## Contrats d'échange API
POST /api/dummy
POST /api/checkout/pay
"""
        total_score, breakdown, blocking, recs = EvalsEngine._compute_rubric_scores(
            content=content_with_phantom,
            rubber_duck_res={"blocking_issues": [], "suggestions": []},
            det_checks={"zero_code_snippets": True},
        )
        self.assertEqual(breakdown["grounding_and_hallucination"], 0.0)
        self.assertTrue(any("HALLUCINATION ROUTE" in b for b in blocking))

    def test_rubric_scoring_gherkin_pillars(self) -> None:
        """Vérifie le calcul proportionnel des 4 piliers Gherkin (7.5 pts par pilier)."""
        content_only_nominal = """---
id: US-301
status: DRAFT
---
## Scénarios de test
Scénario: Chemin nominal avec succès.
"""
        total_score, breakdown, blocking, recs = EvalsEngine._compute_rubric_scores(
            content=content_only_nominal,
            rubber_duck_res={"blocking_issues": [], "suggestions": []},
            det_checks={"zero_code_snippets": True},
        )
        # Seul nominal présent -> 7.5 pts sur 30
        self.assertEqual(breakdown["gherkin_four_pillars"], 7.5)

    def test_run_evals_end_to_end(self) -> None:
        """Exécution complète du harnais avec écriture des rapports JSON et MD."""
        story_content = """---
id: US-999
status: READY_FOR_DEV
---
# US-999 : Déconnexion Utilisateur
## Contexte & Périmètre
### In-Scope
Déconnexion sécurisée de la session utilisateur.
### Out-of-Scope
Gestion des comptes suspendus.

## Contrats d'échange API
POST /api/v1/auth/logout

## Scénarios de test
- Nominal : Déconnexion avec succès et token révoqué.
- Exceptions / Erreurs : Rejet si token déjà révoqué.
- Résilience : Timeout réseau et rejeu avec idempotence.
- UX : Toast de notification et redirection vers l'accueil.
"""
        story_file = self.stories_dir / "US-999.md"
        story_file.write_text(story_content, encoding="utf-8")

        report = self.engine.run_evals()

        self.assertIn("score", report)
        self.assertIn("semantic_quality_score", report)
        self.assertEqual(report["total_stories"], 1)
        self.assertEqual(report["eval_framework"], "Google Agents CLI Eval (Harness Engineering)")
        self.assertGreaterEqual(report["score"], 80.0)

        # Vérification de la création des rapports dans memory/
        memory_dir = self.project_path / "memory"
        self.assertTrue((memory_dir / "evals_report.json").exists())
        self.assertTrue((memory_dir / "evals_report.md").exists())
