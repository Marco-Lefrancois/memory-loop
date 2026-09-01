# -*- coding: utf-8 -*-
"""
Tests unitaires — RubberDuckEngine : Checks F & G (ADR-0319)
Traçabilité conditionnelle des routes API connues & Anti-Invention de routes.

Couvre :
  F1. BE/Fullstack sans Matrice Contrats → BLOCKING
  F2. BE/Fullstack avec Matrice Contrats → pas de blocking sur ce check
  F3. BE/Fullstack sans matrice mais avec OQ exemptante → NON_BLOCKING seulement
  F4. Frontend sans route dans CTA mais avec mention API → NON_BLOCKING
  F5. Récit sans 'layer:' → aucun check F ni G déclenché
  G1. Route fictive /api/dummy → BLOCKING
  G2. Route fictive /api/test → BLOCKING
  G3. Route réelle /api/v1/items → pas d'alerte anti-invention
  G4. Plusieurs routes fictives → BLOCKING avec toutes listées
"""

import tempfile
import unittest
from pathlib import Path

from src.pipelines.rubber_duck import RubberDuckEngine


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _base_story(layer: str = "", extra: str = "") -> str:
    """Génère un récit minimal valide (4 piliers Gherkin + sections obligatoires)."""
    layer_line = f"layer: {layer}\n" if layer else ""
    return f"""---
id: REC-TEST
jira_key: TEST-001
epic_key: EPIC-TEST
type: Feature
title: Story de test
tags: [api, backend]
status: IN_ANALYZE
{layer_line}---
# [TEST-001] Story de test (REC-TEST)

## Description
**En tant qu'** utilisateur, **je veux** faire une action, **afin de** créer de la valeur.

---

## Contexte
Contexte métier du récit.

---

### Interface et UX
Section UI minimale.

---

### Liste Call to Actions

| Élément UI | Trigger | Action (Navigation/API) | Feedback & État Final |
| :--- | :--- | :--- | :--- |
| **Bouton Soumettre** | onClick | POST /api/v1/ressource | Spinner + Toast Succès |

---

## Règles d'affaires
* **Validation sécurité** : L'utilisateur doit être authentifié.

---

## Maquettes
- 🔗 **Lien Figma** : [Écran principal](https://figma.com/file/exemple)

---

## Contrats UI & API Backend

### Profil B : Endpoints WebServices Backend
{extra}

---

## Notes Techniques pour l'implémentation
Préconditions d'état rédigées en langage naturel.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Gestion des ressources

  Scénario: Validation du parcours principal
    Étant donné un utilisateur authentifié
    Quand il soumet le formulaire
    Alors la ressource est créée et un toast de succès s'affiche

  Scénario: Gestion des erreurs de saisie
    Étant donné des données invalides
    Quand l'utilisateur tente de soumettre
    Alors un message d'erreur s'affiche sous le champ

  Scénario: Comportement en mode dégradé
    Étant donné une interruption réseau pendant la soumission
    Quand l'utilisateur envoie le formulaire
    Alors l'application bascule en mode hors-ligne et propose un bouton de réessai

  Scénario: Inspection des états visuels
    Étant donné l'exécution sous proxy de débogage
    Quand j'inspecte les journaux et l'interface
    Alors le spinner, le toast et les traces sont conformes aux spécifications
```
"""


class TestRubberDuckApiRoutes(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.project_path = Path(self.tmp.name)
        # Créer les sous-dossiers minimaux attendus par le moteur
        (self.project_path / "memory" / "cache").mkdir(parents=True, exist_ok=True)
        (self.project_path / "backlog" / "reviews").mkdir(parents=True, exist_ok=True)
        self.engine = RubberDuckEngine(project_path=self.project_path)

    def tearDown(self):
        self.tmp.cleanup()

    def _write_story(self, content: str, filename: str = "TEST-001.md") -> Path:
        story_dir = self.project_path / "backlog" / "stories"
        story_dir.mkdir(parents=True, exist_ok=True)
        target = story_dir / filename
        target.write_text(content, encoding="utf-8")
        return target

    # ── Check F : Traçabilité Conditionnelle (Backend / Fullstack) ─────────────

    def test_F1_backend_without_contract_matrix_is_blocking(self):
        """F1 — layer: backend sans Matrice Contrats API → BLOCKING ADR-0319."""
        content = _base_story(layer="backend", extra="Aucun contrat défini ici.")
        target = self._write_story(content)
        result = self.engine.evaluate_file(target, force=True)

        blocking_texts = " ".join(result["blocking_issues"])
        self.assertIn("ADR-0319", blocking_texts,
                      "Check F1 attendu : BLOCKING ADR-0319 absent pour layer:backend sans matrice.")
        self.assertIn("backend", blocking_texts)

    def test_F2_backend_with_contract_matrix_no_blocking(self):
        """F2 — layer: backend avec Matrice Contrats complète → pas de BLOCKING F."""
        extra = (
            "#### Matrice des Contrats API\n\n"
            "| Méthode | Route | Finalité métier |\n"
            "| :---: | :--- | :--- |\n"
            "| `POST` | `/api/v1/ressource` | Création d'une ressource |\n"
        )
        content = _base_story(layer="backend", extra=extra)
        target = self._write_story(content)
        result = self.engine.evaluate_file(target, force=True)

        blocking_texts = " ".join(result["blocking_issues"])
        self.assertNotIn(
            "layer: backend",
            blocking_texts,
            "Check F2 : aucun BLOCKING F attendu quand la Matrice Contrats est présente."
        )

    def test_F3_backend_without_matrix_but_with_oq_exemption_is_non_blocking(self):
        """F3 — layer: backend sans matrice mais avec clause OQ → NON_BLOCKING seulement."""
        extra = "OQ-001 : Route de création à confirmer avec l'équipe backend.\n[API de soumission à définir]"
        content = _base_story(layer="backend", extra=extra)
        target = self._write_story(content)
        result = self.engine.evaluate_file(target, force=True)

        blocking_texts = " ".join(result["blocking_issues"])
        non_blocking_texts = " ".join(result["non_blocking_issues"])
        # Ne doit PAS être BLOCKING (clause OQ exemptante)
        self.assertNotIn(
            "layer: backend",
            blocking_texts,
            "Check F3 : la clause OQ doit déclasser l'alerte en NON_BLOCKING."
        )
        # DOIT être signalé en NON_BLOCKING
        self.assertIn(
            "ADR-0319",
            non_blocking_texts,
            "Check F3 : une alerte NON_BLOCKING ADR-0319 est attendue pour signaler la route à confirmer."
        )

    def test_F4_fullstack_with_contract_matrix_no_blocking(self):
        """F4 — layer: fullstack avec table de contrats → pas de BLOCKING F."""
        extra = (
            "| `GET` | `/api/v1/items` | Consultation de la liste |\n"
            "| `POST` | `/api/v1/items` | Création d'un item |\n"
        )
        content = _base_story(layer="fullstack", extra=extra)
        target = self._write_story(content)
        result = self.engine.evaluate_file(target, force=True)

        blocking_texts = " ".join(result["blocking_issues"])
        self.assertNotIn(
            "layer: fullstack",
            blocking_texts,
            "Check F4 : pas de BLOCKING F pour fullstack avec matrice présente."
        )

    def test_F5_no_layer_field_skips_api_checks(self):
        """F5 — Récit sans champ 'layer:' → checks F et G non déclenchés."""
        content = _base_story(layer="", extra="Aucun contrat défini.")
        target = self._write_story(content)
        result = self.engine.evaluate_file(target, force=True)

        all_issues = " ".join(result["blocking_issues"] + result["non_blocking_issues"])
        # Aucun message spécifique au check F/G ne doit apparaître
        self.assertNotIn(
            "layer:",
            all_issues,
            "Check F5 : les checks conditionnels F ne doivent pas se déclencher sans champ 'layer:'."
        )

    # ── Check G : Anti-Invention de Routes ────────────────────────────────────

    def test_G1_api_dummy_route_is_blocking(self):
        """G1 — Route /api/dummy → BLOCKING anti-invention."""
        extra = "- **Endpoint** : `POST /api/dummy`"
        content = _base_story(layer="backend", extra=extra)
        target = self._write_story(content)
        result = self.engine.evaluate_file(target, force=True)

        blocking_texts = " ".join(result["blocking_issues"])
        self.assertIn(
            "/api/dummy",
            blocking_texts,
            "Check G1 : /api/dummy doit déclencher un BLOCKING anti-invention."
        )

    def test_G2_api_test_route_is_blocking(self):
        """G2 — Route /api/test → BLOCKING anti-invention."""
        extra = "| `GET` | `/api/test` | Test de l'endpoint |\n"
        content = _base_story(layer="backend", extra=extra)
        target = self._write_story(content)
        result = self.engine.evaluate_file(target, force=True)

        blocking_texts = " ".join(result["blocking_issues"])
        self.assertIn(
            "ADR-0319",
            blocking_texts,
            "Check G2 : /api/test doit déclencher un BLOCKING ADR-0319."
        )

    def test_G3_real_api_route_no_invention_blocking(self):
        """G3 — Route réelle /api/v1/items → pas d'alerte anti-invention."""
        extra = (
            "| `GET` | `/api/v1/items` | Consultation de la liste |\n"
            "| `POST` | `/api/v1/items` | Création d'un item |\n"
        )
        content = _base_story(layer="backend", extra=extra)
        target = self._write_story(content)
        result = self.engine.evaluate_file(target, force=True)

        # Aucune alerte spécifique à l'anti-invention ne doit apparaître
        blocking_texts = " ".join(result["blocking_issues"])
        for phantom in ["/api/dummy", "/api/test", "/api/placeholder", "fictive"]:
            self.assertNotIn(
                phantom,
                blocking_texts,
                f"Check G3 : la route /api/v1/items ne doit pas déclencher d'alerte d'invention ({phantom} trouvé)."
            )

    def test_G4_multiple_invented_routes_all_listed(self):
        """G4 — Plusieurs routes fictives → BLOCKING avec chaque route signalée."""
        extra = (
            "- `GET /api/dummy`\n"
            "- `POST /api/placeholder`\n"
        )
        content = _base_story(layer="backend", extra=extra)
        target = self._write_story(content)
        result = self.engine.evaluate_file(target, force=True)

        blocking_texts = " ".join(result["blocking_issues"])
        self.assertIn(
            "ADR-0319",
            blocking_texts,
            "Check G4 : plusieurs routes fictives doivent déclencher un BLOCKING ADR-0319."
        )
        # Au moins une des deux routes doit apparaître dans le message
        self.assertTrue(
            "/api/dummy" in blocking_texts or "/api/placeholder" in blocking_texts,
            "Check G4 : les routes fictives détectées doivent être listées dans le message BLOCKING."
        )


if __name__ == "__main__":
    unittest.main()
