---
id: MLOOP-192-BE
jira_key: ''
epic_key: EPIC-19-CLICK-CLI-ENGINE
type: Feature
title: Complétion Shell Native (PowerShell 5.1+ / pwsh / Bash) & Compléteurs Dynamiques
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

# 📖 MLOOP-192-BE : Complétion Shell Native (PowerShell 5.1+ / pwsh / Bash) & Compléteurs Dynamiques

## 1. Intention Métier (User Story)
**En tant qu'** Développeur et Agent intervenant sous Windows (PowerShell / pwsh) ou Linux (Bash / Zsh),  
**je veux** disposer de l'autocomplétion native Click pour les commandes, les options et les valeurs dynamiques (projets, récits de sprint),  
**afin de** fluidifier l'utilisation du CLI, éliminer les erreurs de saisie et naviguer instantanément dans les entités du projet via la touche `<TAB>`.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : [`epic_click_cli_engine.md`](../epics/epic_click_cli_engine.md) (Réf : Complétion native Click 8.5+)
- **Références d'Architecture** : ADR-0202 (Modularité < 300L), ADR-0369 (Standards Python Senior)
- **Enveloppe Macro Estimée** : M (1 à 2 jours)

---

## 3. Périmètre Sommaire

### In-Scope (Macro)
- Création de `src/cli/click_engine/completion.py` (≤ 300 lignes, conforme `RULE-AST-01`).
- Compléteurs dynamiques Click (`shell_complete`) :
  - `complete_projects(ctx, param, incomplete)` : liste dynamiquement les projets valides sous `Projects/` (en excluant les dossiers commençant par `.` ou `_` et `_DEPRECATED`).
  - `complete_stories(ctx, param, incomplete)` : extrait les identifiants de récits du backlog actif (`Projects/<project>/backlog/stories/` et `sprint_backlog.md`).
  - `complete_task_types(ctx, param, incomplete)` : propose les types de tâches autorisés pour les commandes de gating.
- Prise en charge officielle de l'instruction d'activation Click :
  - PowerShell : `$env:_LOOP_COMPLETE = 'powershell_source'`
  - Bash : `eval "$(_LOOP_COMPLETE=bash_source loop)"`
  - Zsh : `eval "$(_LOOP_COMPLETE=zsh_source loop)"`
- Commande utilitaire d'aide : `loop completion-setup` affichant la ligne exacte à coller dans son `$PROFILE` selon le shell détecté.

### Out-of-Scope (Macro)
- Modification de l'architecture du routeur (couvert par MLOOP-191-BE).
- Génération de complétion manuelle pour des shells non supportés par Click (ex: tcsh).

---

## 4. Contexte Métier & Architecture

Sous Windows, les développeurs mLoop utilisent PowerShell 5.1 ou PowerShell Core (`pwsh 7+`). `argparse` n'a jamais proposé de complétion native sans bibliothèques tierces complexes et instables sous Windows.

Grâce aux ajouts majeurs de Click 8.5 (commit PR #3637 validé dans notre analyse du dépôt Pallets Click), la complétion PowerShell est désormais native. En y adjoignant des fonctions de complétion contextuelle, l'utilisateur tape :
```powershell
loop vibe-check --project Met<TAB>
# Complète immédiatement en :
loop vibe-check --project Metro_FOOD
```
Cette capacité divise par 3 le temps de saisie et évite les erreurs de casse sur les noms de projets.

---

## Critères d'Acceptation

- [ ] **CA-1** : L'autocomplétion des noms de sous-commandes et des options globales fonctionne sous PowerShell (`pwsh`) et Bash.
- [ ] **CA-2** : La fonction `complete_projects` renvoie tous les répertoires éligibles de `Projects/` correspondant au préfixe `incomplete`, sans renvoyer les dossiers système ou archivés (`_archive`, `.git`).
- [ ] **CA-3** : La fonction `complete_stories` résout les identifiants de récits du projet ciblé si `--project` a été passé dans la ligne de commande courante.
- [ ] **CA-4** : La complétion dynamique s'exécute en < 15ms sur le système de fichiers pour ne provoquer aucun lag à la touche Tabulation.
- [ ] **CA-5** : Une commande `completion-setup` documente et fournit le script d'installation immédiat pour le profil shell actif.
- [ ] **CA-6** : `src/cli/click_engine/completion.py` ne dépasse pas 300 lignes (conforme `RULE-AST-01`).

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : ce récit est un composant interne du CLI mLoop — **aucune route API HTTP n'est consommée ni exposée**.

---

## 5. Piliers Gherkin

### Pilier 1 : Nominal
```gherkin
Scénario: Autocomplétion dynamique d'un nom de projet
  Étant donné les dossiers "Metro_FOOD", "Metro_COMMERCE" et "Metro_SANTE" sous Projects/
  Quand l'utilisateur tape "loop vibe-check --project Metro_F" suivi de <TAB>
  Alors Click complète automatiquement la valeur en "Metro_FOOD"
```

### Pilier 2 : Exceptions
```gherkin
Scénario: Projet introuvable lors de la complétion de story
  Étant donné une commande où l'option "--project" est omise ou invalide
  Quand la complétion sur "--story" est déclenchée
  Alors la fonction renvoie une liste vide sans lever d'exception ni casser la complétion shell
```

### Pilier 3 : Résilience & Mode Dégradé
```gherkin
Scénario: Échec de lecture du dossier Projects/
  Étant donné une permission restreinte ou un dossier Projects inexistant
  Quand complete_projects est invoqué
  Alors l'exception I/O est interceptée silencieusement en DEBUG
  Et la complétion retourne une liste vide sans bloquer le shell
```

### Pilier 4 : UX (Retour Utilisateur / Observabilité)
```gherkin
Scénario: Affichage des instructions d'installation du profil shell
  Étant donné un utilisateur sur machine Windows sous PowerShell
  Quand il exécute "loop completion-setup"
  Alors la sortie affiche la ligne exacte `$env:_LOOP_COMPLETE = 'powershell_source'`
  Et indique l'emplacement de son fichier `$PROFILE`
```
