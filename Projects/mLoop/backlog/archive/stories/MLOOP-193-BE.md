---
id: MLOOP-193-BE
jira_key: ''
epic_key: EPIC-19-CLICK-CLI-ENGINE
type: Feature
title: Structuration de l'Aide par Phases Souveraines & Typage click.Path
origin: DIRECT_REQUIREMENT
source_ref: epic_click_cli_engine.md
macro_size: M
status: DONE
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-191-BE
created_at: '2026-09-23'
ttl_cycles: 2
---

# 📖 MLOOP-193-BE : Structuration de l'Aide par Phases Souveraines & Typage click.Path

## 1. Intention Métier (User Story)
**En tant qu'** Ingénieur et Utilisateur du framework mLoop,  
**je veux** que l'aide en ligne `--help` soit structurée et mise en page selon les 6 phases souveraines de mLoop et que les paramètres de fichiers soient validés via `click.Path`,  
**afin de** disposer d'une visibilité claire sur le cycle de vie du projet directement dans le terminal et d'éliminer les erreurs de chemins de fichiers inexistants avant l'exécution du code métier.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : [`epic_click_cli_engine.md`](../epics/epic_click_cli_engine.md) (Réf : Alignement sur le Guide CLI mLoop)
- **Références d'Architecture** : ADR-0202 (Modularité < 300L), ADR-0369 (Standards Python Senior)
- **Enveloppe Macro Estimée** : M (1 à 2 jours)

---

## 3. Périmètre Sommaire

### In-Scope (Macro)
- Création de `src/cli/click_engine/formatter.py` (≤ 300 lignes, conforme `RULE-AST-01`).
- Sous-classe `PhaseHelpFormatter(click.HelpFormatter)` et surcharge de `format_commands()` sur le groupe racine :
  - Phase 0 — Inception & SOW (`init`, `estimate`, `scope`)
  - Phase 1 — Spec & Ingestion (`ingest`, `crawl`, `deep-search`, `spec-lint`)
  - Phase 2 — Plan & Architecture (`drill`, `grill`, `adr-create`, `story-map`)
  - Phase 3 — Build & Stories (`focus`, `build`, `story-create`, `harness`)
  - Phase 4 — Validate & QA (`vibe-check`, `sentinel`, `rubber-duck`, `wikifix`)
  - Phase 5 — Ship & Sync (`sync`, `jira-sync`, `git-hook`, `release`)
  - Utilitaires transverses (`drawdb`, `budget`, `completion-setup`)
- Définition d'assistants de typage réutilisables :
  - `path_exists(file_okay=True, dir_okay=False)` retournant un objet `pathlib.Path`.
  - `dir_exists()` validant l'existence d'un répertoire.
  - `choice_param(enum_or_list)` encapsulant `click.Choice` avec insensible à la casse.

### Out-of-Scope (Macro)
- Logique de dispatch et de chargement paresseux (couvert par MLOOP-191-BE).
- Modification des signatures des handlers existants (couvert par l'adaptateur `ArgsShim`).

---

## 4. Contexte Métier & Architecture

L'aide générée par `argparse` produit une liste alphabétique brute de 58 commandes dans laquelle il est très difficile de comprendre l'enchaînement chronologique des actions (de l'ingestion à la synchronisation finale).

En surchargeant `format_commands()` de Click, le terminal affiche une cartographie alignée sur `standards/protocols/CLI_PIPELINE_GUIDE.md` :
```
Usage: loop [OPTIONS] COMMAND [ARGS]...

Phase 1 — Spec & Ingestion:
  ingest            Ingestion de documents MarkItDown
  crawl             Crawl intelligent d'URLs ou de dépôts GitHub
  deep-search       Session de recherche autonome multi-sources

Phase 4 — Validate & QA:
  vibe-check        Exécution des 9 contrôles déterministes pré-vol
  sentinel          Audit de cohérence contradictoire
  wikifix           Audit et réparation sémantique
```

De surcroît, les arguments de fichiers passés avec `click.Path(exists=True, path_type=Path)` sont validés et castés nativement dès le parsing, évitant aux handlers d'avoir à vérifier manuellement `if not Path(f).exists(): ...`.

---

## Critères d'Acceptation

- [ ] **CA-1** : L'affichage de `loop --help` regroupe distinctement les commandes sous les 6 phases souveraines mLoop.
- [ ] **CA-2** : Les commandes ne figurant pas dans une phase officielle sont regroupées sous la section "Utilitaires transverses".
- [ ] **CA-3** : Les paramètres utilisant `path_exists()` lèvent une erreur Click immédiate (avec indication claire de fichier introuvable) si le chemin spécifié n'existe pas sur disque.
- [ ] **CA-4** : Les paramètres convertis par `path_exists()` sont reçus sous forme d'instances natives de `pathlib.Path`.
- [ ] **CA-5** : Les options de choix bornés (`click.Choice`) affichent les options autorisées dans l'aide et rejettent toute valeur invalide avec le code de sortie `2`.
- [ ] **CA-6** : `src/cli/click_engine/formatter.py` ne dépasse pas 300 lignes (conforme `RULE-AST-01`).

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : ce récit est un composant interne du formateur d'aide CLI — **aucune route API HTTP n'est consommée ni exposée**.

---

## 5. Piliers Gherkin

### Pilier 1 : Nominal
```gherkin
Scénario: Affichage structuré de l'aide par phase
  Quand l'utilisateur lance "loop --help"
  Alors la sortie console contient les en-têtes des 6 phases souveraines
  Et "vibe-check" apparaît sous la section "Phase 4 — Validate & QA"
  Et "ingest" apparaît sous la section "Phase 1 — Spec & Ingestion"
```

### Pilier 2 : Exceptions
```gherkin
Scénario: Fourniture d'un fichier inexistant pour une option typée Path
  Étant donné une option déclarée avec path_exists(file_okay=True)
  Quand l'utilisateur passe "--input /chemin/inexistant/document.pdf"
  Alors Click interrompt la commande avant l'appel du handler
  Et un message "Invalid value for '--input': Path '/chemin/inexistant/document.pdf' does not exist." est émis
  Et le code de sortie est 2
```

### Pilier 3 : Résilience & Mode Dégradé
```gherkin
Scénario: Commande non classifiée dans la matrice des phases
  Étant donné une commande personnalisée récemment ajoutée sans tag de phase
  Quand format_commands() est exécuté
  Alors la commande est automatiquement placée sous "Utilitaires transverses"
  Et aucune exception n'est levée
```

### Pilier 4 : UX (Retour Utilisateur / Observabilité)
```gherkin
Scénario: Alignement visuel et coloration du terminal
  Étant donné une console moderne supportant les séquences ANSI
  Quand l'utilisateur consulte l'aide
  Alors les noms de commandes et descriptions sont parfaitement alignés en colonnes
  Et les en-têtes de phase sont mis en valeur graphiquement
```
