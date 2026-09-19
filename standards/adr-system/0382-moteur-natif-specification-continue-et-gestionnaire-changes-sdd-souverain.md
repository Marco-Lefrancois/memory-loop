---
id: "ADR-0382"
title: "Moteur Natif de Spécification Continue et Gestionnaire de Changes SDD Souverain"
status: "Accepté"
date: "2026-09-19"
type: "Type 1 — Architecture & Gouvernance Système"
authority: "mLoop Senior Architecture Board"
validation_rules:
  - check_id: "native_spec_generation"
    severity: "BLOCKING"
    description: "Génération déterministe du paquet de change tripartite (proposal, specs, tasks) en pur Python sans binaire externe."
    params:
      required_files: ["proposal.md", "specs/api.md", "tasks.md"]
      zero_external_cli: true
  - check_id: "spec_driven_tdd_binding"
    severity: "BLOCKING"
    description: "Liaison bidirectionnelle entre les micro-tâches de tasks.md et les preuves cryptographiques TDD Red-Green (ADR-0381)."
    params:
      sync_with_tdd_enforcer: true
      require_beyonce_rule: true
  - check_id: "living_spec_continuity"
    severity: "BLOCKING"
    description: "Fusion obligatoire des deltas de spécification dans les specs vivantes du projet lors de l'archivage post-Gate 3."
    params:
      living_specs_root: "specs"
      archive_directory: "specs/archive"
---

# ADR-0382 : Moteur Natif de Spécification Continue et Gestionnaire de Changes SDD Souverain

## Statut
**Accepté (SSOT Normatif)** — 19 Septembre 2026  
**Complète et amende** : [ADR-0103](0103-segmentation-memory-loop-openspec.md) et [ADR-0366](0366-standard-story-2.0-handoff-tripartite-et-maillage-referentiel.md).  
**Consolide** : [ADR-0100](0100-structure-repertoire-projet-client.md), [ADR-0319](0319-dual-agent-handoff-openspec-ready.md), [ADR-0365](0365-harmonisation-symbiotique-skills-et-standard-agent-skills.md), [ADR-0381](0381-standard-harnais-phase-3-linter-ast-tournoi-tdd-red-green.md).

---

## 1. Contexte & Problématique

Jusqu'alors, Memory Loop adoptait une posture défensive vis-à-vis d'OpenSpec ([ADR-0103](0103-segmentation-memory-loop-openspec.md)) :
1. **L'outillage externe npm `openspec` était proscrit** au sein de l'arborescence SSOT des projets clients pour éviter toute pollution d'environnement, binaire lourd ou dérive de spécification (*spec-drift*).
2. **Le format était imité de façon passive** sous `backlog/handoff/<ID>/` ([ADR-0366](0366-standard-story-2.0-handoff-tripartite-et-maillage-referentiel.md)) avec des fichiers Markdown statiques (`proposal.md`, `specs/api.md`, `tasks.md`).
3. **Absence de Moteur Actif de Cycle de Vie** : Aucun composant mLoop n'orchestrait automatiquement la génération des propositions de changement, la synchronisation des tâches TDD physiques pendant la Phase 3 (Build), ni la fusion des deltas dans une documentation vivante (*Living Specs*).

Cette approche passive créait une rupture opérationnelle entre la spécification validée en Phase 2 (Gate 2 DoR) et l'exécution physique en Phase 3 (Build).

---

## 2. Décision d'Architecture

Nous officialisons l'**intégration native et souveraine du modèle de Specification-Driven Development (SDD) au sein du moteur mLoop** :

### 2.1 Internalisation Pure Python (Zéro Binaire Tiers)
Le mécanisme de gestion de spécifications est implémenté nativement en pur Python standard (stdlib + Pydantic v2).  
Aucun binaire Node.js, aucun CLI npm ni dépendance externe n'est requis. Le moteur opère de façon souveraine, déterministe et ultra-rapide (<15 ms).

### 2.2 La Triade des Changements & Spécifications Vivantes

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                      MOTEUR OPENSPEC NATIF MLOOP (PYTHON PUR SOUVERAIN)                     │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  1. PHASE 2 : PLAN & ANALYSE (Sortie de Grill-Me ➔ Gate 2 DoR)                             │
│     Story validée (backlog/stories/<ID>.md)                                                 │
│       │                                                                                     │
│       └──> Générateur natif : python src/swarm.py spec-create --story <ID>                  │
│            Produit le paquet sous specs/changes/<ID>/ (ou backlog/handoff/<ID>/) :          │
│            ├── proposal.md  (Rationale technique, impact architectural, sécurité)           │
│            ├── specs/api.md (Contrats déclaratifs formels, schémas JSON, routes)            │
│            └── tasks.md     (Micro-tâches TDD atomiques < 5 fichiers issues du Gherkin)     │
│                                                                                             │
│  2. PHASE 3 : BUILD & DEV (Piloté par le Harnais Déterministe ADR-0381)                     │
│     Pour chaque micro-tâche de tasks.md :                                                   │
│       ├── Étape RED   : python src/swarm.py tdd-enforce --phase red --story <ID>            │
│       ├── Tournoi     : python src/swarm.py code-tournament --story <ID> (Pareto)           │
│       ├── Audit AST   : python src/swarm.py code-check --file <path>                        │
│       ├── Étape GREEN : python src/swarm.py tdd-enforce --phase green --story <ID>          │
│       └── Cochement   : Le moteur mLoop coche automatiquement [x] dans tasks.md            │
│                         et alimente le Code Evidence Ledger (CEL) ligne par ligne           │
│                                                                                             │
│  3. PHASE 4 & 5 : VALIDATE & SHIP (Clôture & Living Specs)                                  │
│     Validation Gate 3/4 ➔ Archivage et fusion : python src/swarm.py spec-archive            │
│       ├── Archive le paquet sous specs/archive/YYYY-MM-DD-<ID>/                             │
│       └── Fusionne le delta dans les spécifications vivantes :                              │
│           specs/<domaine>/spec.md (Documentation vivante 100% synchronisée avec le code)    │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Câblage Bidirectionnel avec le Harnais de Phase 3 (ADR-0381)
Le fichier `tasks.md` n'est plus une simple checklist manuelle :
1. Chaque micro-tâche correspond à un test unitaire strict (Règle de Beyoncé).
2. L'enforceur TDD (`tdd-enforce`) contrôle que chaque transition `[ ]` ➔ `[x]` repose sur une preuve cryptographique `RedSnapshot` (`exit_code=1`) suivie d'un `GreenSnapshot` (`exit_code=0`).
3. L'achèvement complet de `tasks.md` devient un prérequis physique bloquant pour franchir la **Gate 3 (Definition of Done)**.

### 2.4 Respect Strict des Règles d'Isolation (ADR-0100 & ADR-0103)
- En mode `CLIENT`, les artefacts de spécification continuent d'être isolés sous `backlog/handoff/<ID>/` (ou projetables vers `specs/`), préservant la Loi des 3 Piliers sans créer de conflit d'arborescence.
- En mode `MLOOP` (Dogfooding interne), l'espace `specs/` et `specs/changes/` constitue la SSOT vivante des spécifications fonctionnelles et techniques du framework.

---

## 3. Conséquences & Bénéfices

- **Souveraineté & Indépendance Totale** : mLoop dispose de la puissance du Specification-Driven Development sans aucune dépendance npm/Node.js.
- **Zéro Dérive Documentaire (*Zero Spec-Drift*)** : La fusion automatique dans les *Living Specs* garantit que la documentation reflète fidèlement et continuellement le code déployé.
- **Continuité Parfaite Amont ➔ Aval** : Transition fluide de la User Story déclarative (Phase 2) vers les micro-tâches d'ingénierie physique (Phase 3).
- **Conformité Constitutionnelle** : L'ADR-0103 est clarifiée sans rupture de compatibilité.
