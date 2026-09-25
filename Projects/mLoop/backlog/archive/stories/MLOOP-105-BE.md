---
id: MLOOP-105-BE
jira_key: '-'
epic_key: EPIC-10-SOVEREIGN-EXCELLENCE
type: Feature
title: Garde-Fou Cryptographique et Hook Pre-Commit Déterministe
tags: [git-hook, pre-commit, gatekeeper, code-check, struct-check, determinism]
status: SHIPPED
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---

> ✅ **Livré (2026-09-20)** — Commit `bc9a5c6`. Hook pre-commit déterministe installé sur la racine framework (`C:\Memory Loop\.git\hooks\pre-commit`) : dispatch `code-check` (AST ADR-0202/0369) sur `src/*.py` indexés + `struct-check` (C1-C9) sur récits indexés, bypass souverain `MLOOP_SKIP_HOOKS`, idempotence, désinstallation `--uninstall`, protection des hooks étrangers. Suite TDD `tests/test_install_hooks.py` (7 tests, 100% PASS). Bug latent corrigé : `ZeroFluffConsole.warn` → `warning`. Note : `_registry.py` (1993L) et `project.py` (462L) dépassent le plafond 300L — dette préexistante ciblée par MLOOP-100/101 (bypass souverain requis jusqu'à leur rénovation).
# [EPIC-10-SOVEREIGN-EXCELLENCE] Garde-Fou Cryptographique et Hook Pre-Commit Déterministe (MLOOP-105-BE)

---

## Description
**En tant que** Responsable Qualité & Sécurité du Code,  
**je veux** installer et automatiser un hook Git pre-commit local exécutant les vérificateurs déterministes `code-check` et `struct-check` sur chaque fichier indexé,  
**afin d'** interdire mathématiquement toute régression architecturale, fichier monolithique ou story malformée d'intégrer l'historique Git du projet.

---

## Contexte & Périmètre

### Contexte Métier
Bien que les commandes `code-check` et `struct-check` valident efficacement l'intégrité du code et des récits lorsqu'elles sont exécutées manuellement, l'erreur humaine ou l'oubli reste possible lors des opérations de validation Git. L'installation d'un hook natif `.git/hooks/pre-commit`, orchestrable par une commande simple du CLI mLoop, garantit que chaque commit est systématiquement audité à la volée avant son enregistrement dans le journal Git.

### In-Scope
- Commande CLI dédiée `python src/swarm.py install-hooks` et son pendant de désinstallation.
- Script de hook shell natif autonome sous `.git/hooks/pre-commit` (compatible Windows PowerShell et bash).
- Détection fine des fichiers indexés dans l'index Git (`git diff --cached --name-only`).
- Déclenchement sélectif :
  - Sur les fichiers Python modifiés : audit AST déterministe via `src/core/ast_checker.py` ($\le 300$ lignes, zéro pass silencieux, gestion de ressources).
  - Sur les fichiers Markdown de stories modifiés : audit structurel via `src/pipelines/struct_checker.py` (C1 à C9 et 4 Piliers Gherkin).
- Blocage automatique du commit avec code de sortie non nul (1) et affichage du rapport d'erreurs en cas de violation.
- Suite de tests unitaire dédiée validant l'installation, l'exécution et l'interception du hook.

### Out-of-Scope
- Recours à des outils externes lourds de type framework `pre-commit` Python nécessitant des environnements virtuels séparés.
- Blocage des opérations de lecture ou des commits d'urgence explicitement flaggés par variable d'environnement souveraine.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Installation et Exécution du Hook Git Pre-Commit Déterministe
* **Entrée Métier** : Commande CLI d'installation ou tentative de `git commit` par un contributeur ou un agent autonome.
* **Règles d'admissibilité & Validation** : Le dépôt Git local doit être initialisé et le hook doit s'exécuter en moins de 3 secondes sur l'ensemble des fichiers indexés.
* **Traitement & Algorithme Métier** : Extraction de la liste des fichiers en staging, exécution en sous-processus sécurisé des vérifications AST et de conformité de récits, compilation du bilan et autorisation du commit uniquement si zéro anomalie bloquante n'est détectée.
* **Résultat Métier & Mutations** : Création du script de hook exécutable dans le dossier `.git/hooks/` ou rejet formel du commit avec instructions de remédiation en console.
* **Cas de Rejet Métier** : Commit interrompu immédiatement si au moins un fichier dépasse 300 lignes, contient un `pass` aveugle ou omet l'un des piliers Gherkin.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Garde-Fou Cryptographique et Hook Pre-Commit Déterministe

  # CHEMIN NOMINAL
  Scénario: Validation réussie d'un commit conforme aux standards
    Étant donné un contributeur indexant des fichiers Python et Markdown conformes
    Quand la commande de validation de commit git commit est déclenchée
    Alors le hook pré-commit exécute les vérifications AST et structurelles
    Et le commit est formellement créé sans encombre

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Rejet strict d'un commit contenant un fichier Python dépassant 300 lignes
    Étant donné un contributeur indexant un fichier source de 350 lignes
    Quand la validation du commit est initiée
    Alors le hook pré-commit bloque l'enregistrement du commit
    Et la console affiche la violation RULE-AST-01 avec indication de découpage

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Exécution rapide sans blocage lors de commits ne touchant pas au code
    Étant donné un commit modifiant uniquement des fichiers de documentation texte
    Quand le hook pré-commit filtre les fichiers modifiés
    Alors l'analyse ciblée s'exécute en moins de 500 millisecondes
    Et le commit est validé instantanément sans faux positif

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Installation idempotente des hooks via la commande swarm CLI
    Étant donné un projet mLoop actif
    Quand la commande python src/swarm.py install-hooks est exécutée deux fois de suite
    Alors le hook est correctement configuré et exécutable
    Et un message de confirmation rassurant confirme l'état opérationnel du garde-fou
```
