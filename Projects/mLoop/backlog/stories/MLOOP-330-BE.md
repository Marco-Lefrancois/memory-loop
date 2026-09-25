---
id: MLOOP-330-BE
jira_key: ''
epic_key: EPIC-33-REQUIREMENT-TO-CODE-TRACEABILITY-AND-CODE-EVIDENCE
type: Feature
title: Normalisation des Gabarits de Traçabilité Code ↔ Exigences & Schéma EvidencePack
  2.0
tags:
- standards
- blueprints
- evidencepack
- openspec
- ast
status: READY_FOR_DEV
layer: backend
invest_score: 6/6
macrostructure: workbench
validated_by: Marco
validated_at: '2026-09-25T17:18:38.646725+00:00'
ttl_cycles: 4
---
# Normalisation des Gabarits de Traçabilité Code ↔ Exigences & Schéma EvidencePack 2.0

---

## Description
**En tant qu'** Architecte ou Développeur mLoop utilisant un agent de pair-programming IA (OpenSpec),  
**je veux** disposer de sections normées dans les plans d'implémentation et d'un schéma d'EvidencePack enrichi pour sceller la traçabilité au niveau symbole AST,  
**afin de** justifier chaque fonction ou bloc de code physique en lien avec une règle métier ou un critère Gherkin, sans polluer le récit fonctionnel no-code.

---

## Contexte & Périmètre

### Contexte Métier
Dans l'écosystème mLoop, le Dossier de Preuves Documentaires prouve la légitimité des exigences métier en amont. En aval (Phase 3 BUILD), les architectes ont retenu OpenSpec comme standard de pair-programming IA. Ce récit normalise le format de la matrice de traçabilité Code ↔ Exigences dans les plans d'implémentation et définit le schéma formel `code_traceability_matrix` dans l'EvidencePack JSON, garantissant que tout symbole de code physique créé ou modifié dispose d'une justification vérifiable.

### In-Scope
- Formalisation de la section `Matrice de Traçabilité Code ↔ Exigences` dans `standards/blueprints/plan_template.md`.
- Définition du schéma typé `CodeTraceabilityEntry` dans `src/pipelines/evidence_pack.py` avec validation stricte.
- Prise en charge des règles métier pures (`RM-XXX`) et des balises techniques autorisées (`INFRA`, `TECH-FOUNDATION`).
- Compatibilité native avec le triptyque OpenSpec (`requirements`, `scenarios`, `tasks`).

### Out-of-Scope
- Moteur d'analyse statique et extraction automatique AST depuis les fichiers physiques (couvert par `MLOOP-331-BE`).
- Sonde d'audit déterministe Vibe-Check Check 29 (couvert par `MLOOP-333-BE`).
- Injection de snippets de code dans les User Stories Markdown (strictement proscrite par Gate G4).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Validation Déterministe d'une Entrée de Traçabilité
* **Entrée Métier** : Dictionnaire ou structure représentant une entrée de traçabilité (`ast_symbol`, `requirement_ref`, `gherkin_scenario`, `rationale`, `test_symbol`).
* **Règles d'admissibilité & Validation** : 
  - Le symbole AST doit respecter le format qualifié `chemin/fichier.ext::Symbole`.
  - La référence d'exigence doit être un identifiant de règle métier valide ou une catégorie technique autorisée (`INFRA`, `TECH-FOUNDATION`).
  - La justification (`rationale`) doit contenir au moins 10 caractères non vides.
* **Traitement & Algorithme Métier** : 
  - Contrôle des champs obligatoires via `TypedDict` et validation stricte sans interception silencieuse.
  - Calcul de conformité à la structure OpenSpec (`capability`, `requirement`, `task`).
* **Résultat Métier & Mutations** : Entrée validée prête pour sérialisation dans `memory/evidence/<STORY_ID>_evidence.json`.
* **Cas de Rejet Métier** : Rejet explicite avec message normé si le symbole AST est absent, si la justification est vide ou si la règle est non sourcée.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
* **Validation de la Matrice EvidencePack** : `EvidencePackEngine.validate_code_traceability(entries: List[CodeTraceabilityEntry]) -> bool`
* **Sérialisation JSON Sidecar** : `EvidencePackEngine.set_code_traceability(story_id: str, entries: List[CodeTraceabilityEntry]) -> Path`

---

## Règles d'affaires

- **Ancrage par Symbole Qualifié Obligatoire** : Tout bloc de code tracé doit être désigné par son identifiant AST canonique (`module/fichier.py::fonction`), l'utilisation de numéros de lignes volatils étant formellement interdite.
- **Justification Obligatoire des Dépendances Techniques** : Les fonctions d'infrastructure sans règle métier directe doivent porter la mention `INFRA` ou `TECH-FOUNDATION` avec un motif explicite et un test unitaire associé.
- **Préservation Absolue du No-Code Métier** : Zéro snippet de code physique ou référence AST dans le corps de la User Story Markdown.

---

## Scénarios de test (4 Piliers Gherkin)

### Pilier 1 : Scénario Nominal (Enregistrement d'une Traçabilité Conforme)
* **GIVEN** Un plan d'implémentation contenant une matrice de traçabilité avec un symbole AST qualifié `src/core/auth.py::verify_token`, rattaché à la règle métier `RM-012` et au scénario Gherkin d'expiration.
* **WHEN** Le moteur `EvidencePackEngine` valide et sérialise la matrice pour le récit `MLOOP-330-BE`.
* **THEN** Le fichier `memory/evidence/MLOOP-330-BE_evidence.json` est mis à jour avec le bloc `code_traceability_matrix`.
* **AND** L'empreinte SHA-256 du fichier source associé est scellée dans `source_hashes`.

### Pilier 2 : Scénario d'Exception (Rejet d'une Entrée Invalide ou Orpheline)
* **GIVEN** Une entrée de traçabilité soumise avec un symbole non qualifié (ex: `verify_token` sans chemin de fichier) ou avec une justification vide.
* **WHEN** La méthode de validation `validate_code_traceability()` est invoquée.
* **THEN** Une exception `ValueError` contextualisée est levée sans écrasement silencieux.
* **AND** La sérialisation de l'EvidencePack est annulée en mode tout-ou-rien.

### Pilier 3 : Scénario de Résilience & Fonctions Techniques (Catégories INFRA & OpenSpec Ready)
* **GIVEN** Une fonction technique utilitaire `src/utils/csv_cleaner.py::sanitize_input` ne correspondant à aucune règle métier directe.
* **WHEN** L'entrée est enregistrée avec `requirement_ref: "INFRA"`, un rationale de prévention contre les injections de formules CSV, et un test unitaire `test_csv_cleaner.py::test_sanitize`.
* **THEN** La validation réussit avec le statut `CONFORME_INFRA`.
* **AND** Le bloc généré est convertible sans perte vers le format de tâche OpenSpec `tasks.md`.

### Pilier 4 : Scénario UX & Confinement Déclaratif (Zéro Pollution Markdown)
* **GIVEN** Un récit `backlog/stories/<STORY_ID>.md` en cours d'analyse.
* **WHEN** Le linter `RubberDuckEngine` ou l'audit Sentinel inspecte le corps du récit Markdown.
* **THEN** Aucun snippet de code physique n'est détecté dans le Markdown.
* **AND** La commande `python src/swarm.py vibe-check` confirme le respect de la règle No-Code (Gate G4).

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-330-BE_fact_dossier.md`](../../memory/evidence/MLOOP-330-BE_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Décision d'Architecture SSOT** : [`standards/adr-system/0394-tracabilite-bidirectionnelle-code-exigences-preuves-programmation-ast.md`](../../../../standards/adr-system/0394-tracabilite-bidirectionnelle-code-exigences-preuves-programmation-ast.md)
- 📋 **Standard Handoff Universel** : [`standards/adr-system/0319-dual-agent-handoff-openspec-ready.md`](../../../../standards/adr-system/0319-dual-agent-handoff-openspec-ready.md)
- 📐 **Gabarit de Plan Normalisé** : [`standards/blueprints/plan_template.md`](../../../../standards/blueprints/plan_template.md)
