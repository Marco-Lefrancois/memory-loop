---
id: MLOOP-190-BE
jira_key: ''
epic_key: EPIC-19-CLICK-CLI-ENGINE
type: Feature
title: Infrastructure de Contexte Click & Middleware d'Enforcement des Lifecycle Gates
origin: DIRECT_REQUIREMENT
source_ref: epic_click_cli_engine.md
macro_size: M
status: DONE
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by: []
created_at: '2026-09-23'
ttl_cycles: 2
---

# 📖 MLOOP-190-BE : Infrastructure de Contexte Click & Middleware d'Enforcement des Lifecycle Gates

## 1. Intention Métier (User Story)
**En tant qu'** Architecte du framework mLoop,  
**je veux** encapsuler l'état d'exécution mLoop (`LoopState`, `project_path`, `active_project`) dans un objet `MLoopContext` passé via `click.Context` et intercepter l'exécution par un middleware de contrôle de cycle de vie,  
**afin de** garantir que les règles de gouvernance souveraines (Lifecycle Gates - ADR-0339) sont auditées de façon unifiée et infaillible avant le dispatch de chaque commande.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : [`epic_click_cli_engine.md`](../epics/epic_click_cli_engine.md) (Réf : Modernisation du moteur d'exécution CLI)
- **Références d'Architecture** : ADR-0202 (Modularité < 300L), ADR-0339 (Quality Gate Enforcement), ADR-0369 (Standards Python Senior)
- **Enveloppe Macro Estimée** : M (1 à 2 jours)

---

## 3. Périmètre Sommaire

### In-Scope (Macro)
- Création du module `src/cli/click_engine/context.py` (≤ 300 lignes, conforme `RULE-AST-01`).
- Classe `MLoopContext` instanciée dans `ctx.obj` :
  - Résolution de projet canonique via `SemanticLexiconResolver`.
  - Chargement paresseux ou immédiat de `LoopState` et `project_path`.
  - Métadonnées de traçabilité d'exécution (timestamp, commande, durée).
- Décorateur `@pass_mloop_context` assurant l'injection de type sécurisée dans les commandes.
- Middleware / intercepteur `lifecycle_gate_guard(ctx, cmd_name)` invoquant `ProjectLifecycleManager.can_execute_command()` et arrêtant immédiatement l'exécution avec exit code `1` et message standardisé en cas de violation.
- Gestion propre de l'exception `ClickException` et des logs structurés (ADR-0369).

### Out-of-Scope (Macro)
- Résolution dynamique de sous-commandes (couvert par MLOOP-191-BE).
- Compléteurs shell dynamiques (couvert par MLOOP-192-BE).
- Formatage personnalisé de l'aide `--help` (couvert par MLOOP-193-BE).

---

## 4. Contexte Métier & Architecture

Dans l'architecture historique `argparse` (`src/commands/router.py`), l'interception de sécurité est réalisée au sein d'une fonction procédurale globale `_run_cli()`. Si un nouveau point d'entrée ou une nouvelle commande est ajoutée hors de ce flux, le garde-fou de cycle de vie risque d'être contourné.

En exploitant le cycle de vie natif de Click :
1. Le groupe racine initialise le `MLoopContext`.
2. Le hook d'invocation valide le projet et interroge `ProjectLifecycleManager`.
3. Si la commande n'est pas autorisée pour la phase active du projet (ex: exécuter `vibe-check` avant `build`), Click court-circuite l'appel proprement sans charger le code métier du handler.

---

## Critères d'Acceptation

- [ ] **CA-1** : La classe `MLoopContext` expose `project_name`, `project_path`, `state`, et `timing_start`.
- [ ] **CA-2** : Le décorateur `@pass_mloop_context` extrait `ctx.obj` et le passe en premier argument du callable annoté.
- [ ] **CA-3** : Toute commande nécessitant un projet (`no_project=False`) échoue avec le code de sortie `1` et un message explicite `ZeroFluffConsole.error` si `--project` est manquant et qu'aucun projet actif n'est configuré.
- [ ] **CA-4** : En cas de violation de Lifecycle Gate détectée par `ProjectLifecycleManager`, l'exécution est stoppée net (exit code `1`) avec journalisation d'erreur structurée (champs : `command`, `project`, `phase`, `reason`, `exit_code`).
- [ ] **CA-5** : Les commandes exemptées de projet (`no_project=True`, ex: `drawdb`) s'exécutent sans exiger de paramètre `--project`.
- [ ] **CA-6** : Le fichier `src/cli/click_engine/context.py` ne dépasse pas 300 lignes (conforme `RULE-AST-01`).

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : ce récit est un composant interne du moteur CLI mLoop (`src/cli/click_engine/`) — **aucune route API HTTP n'est consommée ni exposée**.

---

## 5. Piliers Gherkin

### Pilier 1 : Nominal
```gherkin
Scénario: Exécution d'une commande valide avec contexte résolu
  Étant donné un projet "mLoop" valide et conforme aux Lifecycle Gates
  Quand la commande est invoquée via Click avec "--project mLoop"
  Alors MLoopContext est injecté avec le state chargé
  Et le handler reçoit le contexte prêt à l'emploi
  Et l'exécution retourne le code de sortie 0
```

### Pilier 2 : Exceptions
```gherkin
Scénario: Violation d'une Lifecycle Gate
  Étant donné un projet dont la phase active interdit la commande demandée
  Quand la commande est exécutée
  Alors le middleware Click intercepte l'appel
  Et un message "[LIFECYCLE GATE VIOLATION]" est affiché sur stderr
  Et le processus se termine immédiatement avec l'exit code 1
  Et le handler métier n'est jamais appelé
```

### Pilier 3 : Résilience & Mode Dégradé
```gherkin
Scénario: Nom de projet sous forme d'alias non canonique
  Étant donné un alias de projet "Metro_Food" au lieu du nom canonique
  Quand la commande est invoquée avec "--project Metro_Food"
  Alors SemanticLexiconResolver résout automatiquement le nom canonique
  Et le contexte est initialisé sur le projet résolu avec un message d'information
```

### Pilier 4 : UX (Retour Utilisateur / Observabilité)
```gherkin
Scénario: Omission du paramètre projet requis
  Étant donné une commande nécessitant un contexte projet
  Quand l'utilisateur lance la commande sans "--project"
  Alors un message d'erreur clair liste les projets connus disponibles sous Projects/
  Et l'exécution retourne le code 1 sans trace d'exception Python (traceback)
```
