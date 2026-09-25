---
id: MLOOP-390-BE
jira_key: ''
epic_key: EPIC-36-HERDR-WORKER-PERMISSIONS-AND-RUNTIME-GOVERNANCE
type: Feature
title: Migration & Synchronisation Idempotente des Permissions opencode.json Multi-Projets
tags:
- opencode
- permissions
- migration
- multi-projets
- external-directory
- idempotent
status: READY_FOR_QA
layer: backend
invest_score: 6/6
macrostructure: workbench
validated_by: Marco
validated_at: '2026-09-25T19:37:18.000000+00:00'
ttl_cycles: 2
---
# Migration & Synchronisation Idempotente des Permissions opencode.json Multi-Projets

---

## Description
**En tant qu'** Orchestrateur mLoop ou développeur intervenant sur un sous-projet existant (`Projects/<projet>`),  
**je veux** disposer d'un mécanisme de synchronisation automatique et idempotent mettant à jour les configurations `opencode.json` locales avec la politique de permissions sans blocage,  
**afin que** les workers exécutant des commandes transverses (`src/swarm.py`) depuis le dossier de travail du sous-projet n'interrompent jamais leur flux par des invites de sécurité d'OpenCode (`external_directory: ask`).

---

## Contexte & Périmètre

### Contexte Métier
L'audit des configurations de projet existantes (`Projects/BoireFrere_Segment2`, `Projects/Metro_FOOD`, `Projects/Shopify_AI_Item_Creator`) a révélé qu'elles ont été initialisées avec d'anciennes versions du blueprint OpenCode dépourvues de la section `permission` explicite. Lorsque Herdr lance un worker dans le sous-dossier `Projects/BoireFrere_Segment2` et que ce dernier exécute des commandes mLoop transverses telles que `python src/swarm.py code-explore` ou `python src/swarm.py sync`, OpenCode identifie `src/swarm.py` comme un chemin situé en dehors du répertoire racine du projet et suspend l'exécution en attente d'une validation manuelle de l'utilisateur (`external_directory: ask`).  
La story précédente `MLOOP-389-BE` a corrigé le blueprint de référence et la configuration racine. Ce récit formalise la commande et la logique de migration par lot pour auditer, corriger et maintenir synchronisés tous les fichiers `opencode.json` de l'ensemble du parc de projets mLoop.

### In-Scope
- Développement d'un gestionnaire de synchronisation idempotent capable d'auditer et de mettre à jour un ou plusieurs fichiers `opencode.json`.
- Injection déterministe de la section `permission` conforme au standard ADR-0389 :
  - `external_directory: { "*": "allow" }`
  - `bash: "allow"`
  - `edit: "allow"`
  - `read: "allow"`
- Stratégie de fusion non destructive (*Deep Merge*) : préservation absolue des instructions, MCPs locaux existants (`loop_mem`, `graphify`, `codegraph`) et alias de commandes personnalisés définis dans les fichiers cibles sans altération de structure.
- Périmètre de détection : balayage de tous les sous-dossiers actifs sous `Projects/` par défaut, avec exclusion du dossier `Projects/_archive/` sauf activation du drapeau explicite `--include-archive`.
- Double point d'entrée CLI mLoop :
  - Sous-commande dédiée autonome : `python src/swarm.py opencode-sync [--project <nom>] [--all] [--dry-run] [--include-archive]`.
  - Intégration transparente : exécution automatique comme sous-étape idempotente lors de l'appel à `python src/swarm.py sync --project <nom>`.
- Mode dry-run permettant d'inspecter les modifications prévues avant application physique sur le disque.
- Tests unitaires et d'intégration couvrant les cas nominaux, les configurations partiellement migrées et la détection d'idempotence.

### Out-of-Scope
- Modification des drapeaux de lancement du CLI OpenCode dans Herdr (déjà scellé dans `MLOOP-389-BE`).
- Audit dynamique en continu lors du pré-vol Vibe-Check (couvert par `MLOOP-391-BE`).
- Gestion de runtimes tiers autres qu'OpenCode (couvert par `MLOOP-392-BE`).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Audit et Détection des Écarts de Configuration
* **Entrée Métier** : Chemin d'un projet spécifique ou balayage global de l'arborescence `Projects/`.
* **Règles d'admissibilité & Validation** :
  - Tout fichier `opencode.json` valide sur le plan syntaxique JSON est analysé.
  - La présence et la structure du nœud `permission` sont vérifiées contre le schéma normatif mLoop.
  - Si `permission.external_directory` est manquant ou ne contient pas la règle générique `allow`, le projet est marqué comme non-conforme.
  - Les projets situés dans `Projects/_archive/` sont ignorés par défaut sauf si `--include-archive` est spécifié.
* **Résultat Métier** : Un rapport d'audit exhaustif liste l'état de chaque projet (Conforme / Non-conforme / Erreur syntaxique).
* **Cas de Rejet** : Tout fichier JSON corrompu ou illisible lève une alerte explicite sans interrompre le traitement des autres projets.

#### 2. Application Idempotente des Permissions par Deep Merge
* **Entrée Métier** : Fichier `opencode.json` nécessitant une mise à niveau, avec option de sauvegarde de sécurité.
* **Règles d'admissibilité & Validation** :
  - Les nœuds existants (`instructions`, `mcp`, `commands`, `watcher`) doivent être conservés intacts.
  - Le bloc `permission` est fusionné de façon non destructive, en appliquant les règles d'auto-approbation tout en respectant d'éventuelles permissions plus fines préexistantes.
  - Une exécution répétée sur un fichier déjà conforme ne produit aucune écriture disque ni modification d'horodatage.
* **Résultat Métier** : Le fichier est mis à jour selon l'encodage UTF-8 standard avec indentation normalisée à 2 espaces.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
* **Service de Synchronisation** : `OpencodeMigrator.audit_project(project_dir: Path) -> MigrationStatus`
* **Application des Modifications** : `OpencodeMigrator.migrate_project(project_dir: Path, dry_run: bool = False) -> MigrationResult`
* **Synchronisation par Lot** : `OpencodeMigrator.sync_all_projects(projects_root: Path, include_archive: bool = False, dry_run: bool = False) -> List[MigrationResult]`
* **Commandes CLI** :
  - `python src/swarm.py opencode-sync [--all] [--project <nom>] [--dry-run] [--include-archive]`
  - Sous-étape automatique dans `python src/swarm.py sync --project <nom>`

### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `audit_project` | `OpencodeMigrator.audit_project` | Audit des écarts de configuration | `(project_dir: Path) -> MigrationStatus` |
| `migrate_project` | `OpencodeMigrator.migrate_project` | Migration idempotente des permissions | `(project_dir: Path, dry_run: bool) -> MigrationResult` |
| `sync_all_projects` | `OpencodeMigrator.sync_all_projects` | Synchronisation par lot | `(projects_root: Path, include_archive: bool, dry_run: bool) -> List[MigrationResult]` |

> OQ-390-1 : Ce récit définit des méthodes Python internes (module `src.pipelines.opencode_migrator`), pas des endpoints HTTP/REST. La "Route / Point d'Entrée" référence le chemin de module Python qualifié (`module:function`), conforme au standard Zéro Fausse Route (ADR-0319) pour les APIs internes. **[API de soumission à définir]** — Aucune route HTTP/REST n'est exposée par ce module.

## Règles d'affaires

- **Idempotence Stricte** : La commande doit pouvoir être exécutée N fois sans modifier le comportement ou corrompre les métadonnées des projets conformes.
- **Principe du Moindre Impact** : Aucune configuration spécifique au projet (outils MCP locaux, descriptions de commandes) ne doit être écrasée ou réordonnée inutilement.
- **Conservation du Format Valide** : Les fichiers mis à jour doivent valider le schéma officiel d'OpenCode sans générer d'avertissement de parsing au démarrage du worker.
- **Sanctuarisation des Archives** : Le dossier `Projects/_archive/` demeure immuable sauf demande explicite de l'utilisateur.

---

## Scénarios de test (4 Piliers Gherkin)

### Pilier 1 : Scénario Nominal (Mise à Jour d'un Projet Hérité sans Section Permission)
* **GIVEN** Un projet existant `Projects/BoireFrere_Segment2` dont le fichier `opencode.json` ne comporte aucune section `permission`.
* **WHEN** L'opérateur exécute `python src/swarm.py opencode-sync --project BoireFrere_Segment2`.
* **THEN** Le fichier `opencode.json` est mis à jour avec le nœud `permission` contenant `external_directory: { "*": "allow" }`.
* **AND** Les sections `commands` et `mcp` préexistantes restent strictement identiques.

### Pilier 2 : Scénario d'Exception (Fichier JSON Malformé ou en Lecture Seule)
* **GIVEN** Un sous-dossier de projet contenant un fichier `opencode.json` invalide sur le plan syntaxique.
* **WHEN** La commande de migration globale analyse le répertoire.
* **THEN** L'anomalie est consignée dans le rapport avec le diagnostic d'erreur précis.
* **AND** Le processus poursuit la synchronisation des projets suivants sans planter.

### Pilier 3 : Scénario de Résilience (Vérification de l'Idempotence Absolue)
* **GIVEN** Un fichier `opencode.json` déjà migré et pleinement conforme aux spécifications ADR-0389.
* **WHEN** Le migreur est exécuté une seconde fois avec ou sans drapeau dry-run.
* **THEN** Aucun octet n'est réécrit sur le disque et le statut retourné indique explicitement `ALREADY_COMPLIANT`.
* **AND** L'empreinte de hachage SHA-256 du fichier demeure inchangée.

### Pilier 4 : Scénario UX & Observabilité (Rapport Synthétique CLI & Dry-Run)
* **GIVEN** Un parc hétérogène de projets comprenant des configurations à jour et des configurations obsolètes.
* **WHEN** L'utilisateur lance `python src/swarm.py opencode-sync --all --dry-run`.
* **THEN** La console affiche un tableau récapitulatif colorisé présentant le nom du projet, l'état actuel et le diff projeté.
* **AND** Aucun fichier n'est modifié sur le système de fichiers.

---

## Références

### 1. Décisions d'Architecture SSOT
- 🏛️ **ADR Fondateur** : [`standards/adr-system/0389-worker-permissions-zero-blindspot.md`](../../../../standards/adr-system/0389-worker-permissions-zero-blindspot.md)
- 🏛️ **ADR Modularité** : [`ADR-0202`](../../../../standards/adr-system/0202-modularite-interne-agents.md)
- 🏛️ **Protocole Rigueur Écosystème** : [`standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md`](../../../../standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md)
- 📐 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-390-BE_fact_dossier.md`](../../memory/evidence/MLOOP-390-BE_fact_dossier.md)
- 📐 **Blueprint Référence** : [`standards/blueprints/project_opencode_template.json`](../../../../standards/blueprints/project_opencode_template.json)
