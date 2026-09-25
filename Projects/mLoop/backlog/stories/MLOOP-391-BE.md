---
id: MLOOP-391-BE
jira_key: ''
epic_key: EPIC-36-HERDR-WORKER-PERMISSIONS-AND-RUNTIME-GOVERNANCE
type: Feature
title: 'Sonde Vibe-Check Check 31 : Audit Dynamique de Santé des Permissions & Runtimes Workers'
tags:
- vibe-check
- quality-gate
- herdr
- worker-runtimes
- permissions
- anti-regression
status: DRAFT
layer: backend
invest_score: 6/6
macrostructure: workbench
validated_by: ''
validated_at: ''
ttl_cycles: 3
---
# Sonde Vibe-Check Check 31 : Audit Dynamique de Santé des Permissions & Runtimes Workers

---

## Description
**En tant que** Gardien de la qualité mLoop et exécutant du contrôle de conformité pré-vol `vibe-check`,  
**je veux** que la sonde dynamique Check 31 audite en continu les drapeaux de démarrage des workers, la cohérence du registre des runtimes et les permissions des configurations de projet,  
**afin d'** interdire tout démarrage de worker susceptible de se figer dans un sous-panneau Herdr et d'empêcher toute réintroduction de drapeaux obsolètes ou bannis.

---

## Contexte & Périmètre

### Contexte Métier
Le protocole Vibe-Check constitue la barrière d'intégrité déterministe pré-vol de mLoop. Auparavant, aucun check ne validait spécifiquement l'admissibilité des drapeaux de lancement des sous-agents ni la présence des sections de permissions débloquantes dans les fichiers de configuration. Cette absence de contrôle proactif a permis à des drapeaux obsolètes (`--yolo`) de subsister silencieusement dans plusieurs pipelines de délégation, et aux workers d'être instanciés sans auto-approbation en environnement PTY. La mise en place de la sonde Check 31 institutionnalise un garde-fou automatisé empêchant toute régression future sur la gouvernance des permissions.

### In-Scope
- Implémentation de la fonction d'audit `check_31_worker_permissions(project_dir: Path) -> CheckResult` au sein du module d'agents de Vibe-Check.
- Validation statique et dynamique des drapeaux d'auto-approbation déclarés dans `src/core/worker_runtimes.py` :
  - OpenCode : présence impérative de `--auto` et de `--agent worker` ; interdiction absolue de `--yolo`.
  - Cline : présence impérative de `--auto-approve true`.
- Balayage anti-régression des scripts de pipelines de délégation (`src/pipelines/delegation/`) pour interdire la résurgence de chaînes ou drapeaux dépréciés.
- Contrôle de la présence de la permission `external_directory: { "*": "allow" }` dans le fichier `opencode.json` du projet analysé et dans le blueprint de référence.
- Restitution d'un verdict tri-état conforme au standard ADR-0384 (`PASS`, `WARNING`, `FAIL`).
- Respect strict du plafond de modularité ≤ 300 lignes pour chaque module de Vibe-Check (ADR-0202).
- Suite de tests unitaires dédiée dans `tests/test_vibe_check_31.py`.

### Out-of-Scope
- Modification des logiques de démarrage ou de PTY de `herdr.exe` (périmètre `MLOOP-389-BE`).
- Réécriture automatique des fichiers sur le disque lors du check (délégué à `MLOOP-390-BE`).
- Définition de nouveaux runtimes tiers (couvert par `MLOOP-392-BE`).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Audit Tri-État du Registre et des Configurations
* **Entrée Métier** : Répertoire du projet cible en cours d'audit et arborescence mLoop globale.
* **Règles d'admissibilité & Validation** :
  - **Règle FAIL** : La présence de tout drapeau interdit (`--yolo`) dans les fichiers du périmètre d'exécution, ou l'absence des drapeaux d'auto-approbation dans `WORKER_RUNTIMES`, entraîne un blocage immédiat du contrôle (`status=FAIL`).
  - **Règle WARNING** : L'absence de la section `external_directory` dans le fichier `opencode.json` d'un sous-projet déclenche un avertissement explicite orientant vers la commande de synchronisation (`status=WARNING`).
  - **Règle PASS** : Le registre des runtimes est conforme, aucun flag banni n'est détecté, et la configuration du projet courant valide toutes les permissions requises (`status=PASS`).
* **Résultat Métier** : Un objet de résultat normalisé contenant le statut, le score d'intégrité et la liste des anomalies actionnables.
* **Cas de Rejet** : Tout échec d'accès au système de fichiers consigne une erreur d'audit sans provoquer de crash inattendu du moteur global de Vibe-Check.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
* **Point d'Entrée Sonde** : `check_31_worker_permissions(project_dir: Path) -> dict[str, Any]`
* **Format de Résultat Normalisé** :
  - `status` : `"PASS"` | `"WARNING"` | `"FAIL"`
  - `name` : `"Check 31 - Worker Permissions & Runtime Governance"`
  - `details` : Liste descriptive des vérifications effectuées et des écarts relevés.
  - `remediation` : Commande suggérée pour résoudre l'écart constaté le cas échéant.

---

## Règles d'affaires

- **Tolérance Zéro sur les Flags Dépréciés** : Tout flag provoquant un comportement non documenté ou un avertissement CLI au niveau du runtime worker est proscrit.
- **Indépendance d'Audit** : La sonde ne doit instancier aucun sous-processus lourd ni invoquer de réseau ; l'audit repose exclusivement sur l'analyse statique déterministe et l'inspection de structures en mémoire.
- **Modularité Rigide** : L'ajout de la sonde ne doit sous aucun prétexte faire franchir le seuil des 300 lignes à `src/pipelines/vibe_check/_vc_agents.py` ou `src/pipelines/vibe_check/__init__.py`.

---

## Scénarios de test (4 Piliers Gherkin)

### Pilier 1 : Scénario Nominal (Environnement Parfaitement Conforme)
* **GIVEN** Un environnement mLoop où `WORKER_RUNTIMES` contient les flags valides et où le projet cible dispose d'un `opencode.json` à jour.
* **WHEN** La sonde `check_31_worker_permissions` est exécutée.
* **THEN** Le statut retourné est strictement `"PASS"`.
* **AND** Aucune anomalie n'est ajoutée au rapport de diagnostic.

### Pilier 2 : Scénario d'Exception (Détection d'un Drapeau Banni dans un Pipeline)
* **GIVEN** Un pipeline de délégation contenant par inadvertance l'argument déprécié `"--yolo"`.
* **WHEN** La suite Vibe-Check déclenche le Check 31.
* **THEN** Le statut retourné bascule immédiatement sur `"FAIL"`.
* **AND** Le message de remédiation identifie précisément le fichier et la ligne concernée.

### Pilier 3 : Scénario de Résilience (Absence d'Auto-Approbation dans un Nouveau Runtime)
* **GIVEN** Un runtime déclaré dans le dictionnaire sans drapeau d'auto-approbation explicite.
* **WHEN** L'audit dynamique analyse les spécifications déclaratives.
* **THEN** La sonde isole le runtime défaillant et émet une alerte de sévérité élevée.
* **AND** L'exécution des autres vérifications de la suite se poursuit sans interruption.

### Pilier 4 : Scénario UX & Observabilité (Rendu Visuel dans le Rapport Vibe-Check)
* **GIVEN** L'orchestrateur lançant la commande `python src/swarm.py vibe-check --project mLoop`.
* **WHEN** Le tableau récapitulatif des 31 checks est affiché dans la console.
* **THEN** La ligne Check 31 apparaît avec l'indicateur vert clair et la mention de conformité des permissions des workers.
* **AND** Le temps d'exécution mesuré de la sonde demeure inférieur à 50 millisecondes.

---

## Références

### 1. Décisions d'Architecture SSOT
- 🏛️ **ADR Fondateur** : [`standards/adr-system/0389-worker-permissions-zero-blindspot.md`](../../../../standards/adr-system/0389-worker-permissions-zero-blindspot.md)
- 🏛️ **ADR Vibe-Check Tri-État** : [`ADR-0384`](../../../../standards/adr-system/0384-standardisation-vibe-check-tri-etat.md)
- 🏛️ **ADR Modularité** : [`ADR-0202`](../../../../standards/adr-system/0202-modularite-interne-agents.md)
- 📐 **Protocole d'Audit 360°** : [`standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md`](../../../../standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md)
