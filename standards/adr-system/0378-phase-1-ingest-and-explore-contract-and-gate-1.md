---
id: "ADR-0378"
title: "Standardisation de la Phase 1 INGEST & EXPLORE, Contrat d'Ingestion Documentaire et Gate 1"
status: "Accepté"
date: "2026-09-18"
type: "Type 1 — Architecture & Gouvernance Système"
authority: "mLoop Senior Architecture Board"
validation_rules:
  - check_id: "phase_1_no_premature_stories"
    severity: "BLOCKING"
    description: "Interdiction formelle de récits utilisateur sous backlog/stories/ avant Gate 1 (Check 13 / Anti-Ghost-Bias)."
    params:
      forbidden_path: "backlog/stories/*.md"
      exceptions: ["README.md"]
  - check_id: "phase_1_assets_isolation"
    severity: "BLOCKING"
    description: "Les maquettes vectorielles et schémas doivent résider sous docs/05-assets/ (ADR-0332)."
    params:
      target_dir: "docs/05-assets"
  - check_id: "phase_1_docs_ingested_required"
    severity: "BLOCKING"
    description: "Le dossier docs/00-ingested/ doit contenir les documents Markdown normalisés avant Gate 1."
    params:
      target_dir: "docs/00-ingested"
---

# ADR-0378 : Standardisation de la Phase 1 INGEST & EXPLORE, Contrat d'Ingestion Documentaire et Gate 1

## Statut
**Accepté (SSOT Normatif)** — 18 Septembre 2026

---

## 1. Contexte & Problématique

Dans l'écosystème **Memory Loop (mLoop)**, l'amorçage de nouveaux projets clients était historiquement sujet à plusieurs dérives méthodologiques et cognitives :
1. **Le Piège du Ghost Bias (Saut de Phase Prématuré)** : L'IA ou les opérateurs humains commençaient à rédiger des User Stories dans `backlog/stories/` ou des macro-chiffrages d'architecture dans `docs/01-architecture/` avant même que la matière première brute du client n'ait été formellement ingérée et comprise. Cette anticipation parasitait la neutralité cognitive des modèles LLM.
2. **La Confusion du Dossier de Staging (`reference/`)** : Le répertoire `reference/` manquait de clarté sur son statut de zone de dépôt temporaire locale non versionnée, risquant d'embarquer des sous-fichiers internes parasites ou d'être ignoré par l'utilisateur.
3. **La Dispersion des Actifs Graphiques** : Les maquettes UI vectorielles (SVG) et captures d'écran étaient parfois laissées dans `reference/` (non versionné) ou dispersées, empêchant les développeurs avals d'accéder au contrat visuel (ADR-0332).
4. **Le Hardcoding de Directives dans le Code Python** : Les libellés d'étapes et de portes étaient figés dans des chaînes de caractères littérales Python, entraînant des risques de désynchronisation (*drift*) avec les ADRs constitutionnelles.

---

## 2. Décisions d'Architecture

### 2.1 Périmètre Strict & Inviolable de la Phase 1 (`STAGE_1_INGEST`)
La Phase 1 est formellement baptisée **`INGEST & EXPLORE`**. Ses frontières sont hermétiques :
- **Entrées Autorisées** : Matière première brute déposée manuellement par l'humain dans `Projects/<nom>/reference/` (PDF, Word, Excel, PowerPoint, CSV, Audio VTT, Maquettes SVG).
- **Sorties Autorisées** :
  - Markdown normalisé sous `docs/00-ingested/` (avec `source_manifest.json` et sidecars LOD `.overview.md`).
  - Actifs visuels et maquettes vectorielles sous `docs/05-assets/` (ADR-0332).
  - Lexique métier auto-consolidé sous `docs/04-transverse/lexique_domaine.md`.
  - Index SQLite FTS5 et hypergraphe Graphify synchronisés (`python src/swarm.py sync`).
- **Interdictions Absolues (Check 13 / Anti-Ghost-Bias)** : Aucune story sous `backlog/stories/`, aucun document d'architecture sous `docs/01-architecture/`.

### 2.2 Séquence Déterministe en 4 Temps avec Pause Humaine
L'amorçage d'un projet suit une séquence universelle :
1. **Temps 1 (Machine)** : `python src/swarm.py init --project <Nom>` échafaude l'arborescence complète des 3 Piliers (sans sub-readme dans `reference/`, conformément à `"forbidden_subreadmes": true` de l'ADR-0100) et affiche le panneau console guidé.
2. **Temps 2 (Humain — PAUSE OBLIGATOIRE)** : L'utilisateur dépose ses documents bruts dans `Projects/<Nom>/reference/`.
3. **Temps 3 (Machine)** : `python src/swarm.py ingest --project <Nom>` convertit les fichiers, optimise les SVG, génère le `source_manifest.json` et synchronise FTS5/Graphify. Si `reference/` est vide, `ingest` affiche un avertissement clair et s'arrête sans créer de manifestes vides erronés.
4. **Temps 4 (Gouvernance)** : Validation de la **Gate 1** via `python src/swarm.py gate-approve --gate 1`.

### 2.3 Contrat des 5 Critères Bloquants de Gate 1 (Definition of Ingested)
L'approbation de Gate 1 est programmée dans `ProjectLifecycleManager.approve_gate(gate_number=1)` et vérifie automatiquement :
1. **G1** : Tous les fichiers de `reference/` sont convertis en Markdown sous `docs/00-ingested/`.
2. **G2** : Les maquettes vectorielles SVG sont optimisées sous `docs/05-assets/`.
3. **G3** : SQLite FTS5 et l'hypergraphe Graphify sont synchronisés.
4. **G4** : Le `source_manifest.json` et les sidecars LOD sont présents et intègres.
5. **G5 (Check 13)** : Zéro story sous `backlog/stories/`. Si des stories sont détectées, Gate 1 est bloquée avec consigne d'exécuter `lifecycle-clean --confirm`.

### 2.4 Calcul d'Empreinte Cryptographique Dédié à la Phase 1
Lors de l'approbation de Gate 1, le `checksum` consigné dans `lifecycle_state.json` est calculé sur les livrables réels de Phase 1 :
- `docs/00-ingested/source_manifest.json`
- `docs/00-ingested/index.md`
- Tous les fichiers `.md` sous `docs/00-ingested/`
- Tous les fichiers `.svg` sous `docs/05-assets/`

### 2.5 Architecture « ADR-as-SSOT » & Découplage du Code Python
- Les métadonnées textuelles des étapes et des portes sont externalisées dans `standards/adr-contracts.json`.
- Le code Python (`src/core/lifecycle.py`, `src/commands/handlers/project.py`) lit dynamiquement ces contrats.
- Les règles de validation sont chargées dynamiquement depuis les frontmatters YAML des ADRs par `RuleEngine`.

---

## 3. Conséquences & Bénéfices

- **Zéro Ghost Bias** : Impossibilité matérielle d'amorcer l'architecture ou le backlog avant que la matière première ne soit ingérée et validée.
- **Ergonomie et Fluidité Supérieures** : L'utilisateur est guidé pas à pas lors de la création de projet.
- **Zero-Drift Documentaire** : Alignement dynamique garanti entre le code Python, les ADRs et les contrats machine.
- **Conformité Senior Python (ADR-0369)** : Typage strict, gestion des ressources par context managers, et observabilité enrichie.
