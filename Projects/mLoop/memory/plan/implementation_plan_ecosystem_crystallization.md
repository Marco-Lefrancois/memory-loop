# 🏗️ Plan d'Action : Verrouillage & Cristallisation Systémique de l'Architecture Projet

## 🎯 Objectif
Verrouiller l'architecture canonique des projets mLoop (**1 `README.md` racine + `AGENTS.md` + `opencode.json` + `.gitignore` avec `reference/` exclu**) au niveau du moteur Python (`src/`), des contrats ADR (`standards/adr-contracts.json`) et de l'ensemble des projets existants (`Projects/`), tout en garantissant le principe **Zero-Drift / DRY** (une seule source de vérité sans dédoublement d'information).

---

## 🧠 Réponse d'Architecture : Comment le code Python puise ses configurations ?

Pour éviter tout dédoublement d'information (*DRY Architecture*) :
1. **Les ADRs (`standards/adr-system/` & `docs/01-architecture/`)** sont la Source de Vérité Conceptuelle (SSOT humain & IA).
2. **Le Registre de Contrats Machine (`standards/adr-contracts.json`) & les Blueprints (`standards/blueprints/`)** traduisent ces ADRs en schémas et gabarits machine déclaratifs.
3. **Le code Python (`src/`)** lit directement ces gabarits et contrats machine pour exécuter le scaffolding et les validations au lieu de coder des chaînes de caractères en dur.
4. **Le moteur Calibrate (`src/pipelines/calibrate.py`)** compare en temps réel le code, les contrats machine et les fichiers sur disque pour certifier qu'aucun écart (*drift*) n'apparaît.

---

## 🚨 User Review Required

> [!IMPORTANT]
> **Périmètre des Changements Systémiques** :
> 1. **Moteur `src/pipelines/sync.py`** : Suppression définitive de la régénération furtive de `memory/README.md`.
> 2. **Scaffolding `src/commands/handlers/project.py`** : Création automatique du quatuor racine dès `swarm.py init` / `code-init`.
> 3. **Auto-Réparation `src/pipelines/calibrate.py`** : Ajout d'une étape de détection et purge automatique de tout sous-README orphelin.
> 4. **Alignement des Projets Existants** : Nettoyage et équipement de `Metro_Food`, `BoireFrere_Reception`, `rbc-avion-metro`, `commerce-react`, `htc-small-business`.

---

## 🛠️ Proposed Changes

### 1. Moteur & Pipelines Python (`src/`)

#### [MODIFY] [src/pipelines/sync.py](file:///c:/Memory%20Loop/src/pipelines/sync.py)
- Supprimer les lignes 35-48 qui recréaient automatiquement `memory/README.md`.

#### [MODIFY] [src/commands/handlers/project.py](file:///c:/Memory%20Loop/src/commands/handlers/project.py)
- Enrichir `handle_init` pour générer automatiquement :
  - `README.md` (racine)
  - `AGENTS.md` (racine, à partir du blueprint `project_agents_template.md`)
  - `opencode.json` (racine, configuré pour le projet avec serveurs MCP et watcher ignores)
  - `.gitignore` (racine, avec exclusion de `reference/` et `.codegraph/`)

#### [MODIFY] [src/pipelines/calibrate.py](file:///c:/Memory%20Loop/src/pipelines/calibrate.py)
- Ajouter l'étape `_audit_project_root_and_subreadmes()` :
  - Valide la présence des 4 fichiers racines obligatoires.
  - Détecte et purge automatiquement tout sous-fichier `README.md` dans les sous-dossiers (`backlog/`, `docs/`, `memory/`, `reference/`).

---

### 2. Contrats Machine & Standards (`standards/`)

#### [MODIFY] [standards/adr-contracts.json](file:///c:/Memory%20Loop/standards/adr-contracts.json)
- Mettre à jour `ADR-0100` avec :
  - `required_root_files`: `["README.md", "AGENTS.md", "opencode.json", ".gitignore"]`
  - `forbidden_subreadmes`: `true`
  - `git_ignored_dirs`: `["reference", "graphify-out", ".codegraph"]`

---

### 3. Alignement des Projets Existants (`Projects/`)

#### [MODIFY] [Projects/Metro_Food/](file:///c:/Memory%20Loop/Projects/Metro_Food)
- Supprimer `memory/README.md`.
- Créer `Projects/Metro_Food/AGENTS.md`.
- Créer `Projects/Metro_Food/opencode.json`.
- Créer/Mettre à jour `Projects/Metro_Food/.gitignore` (avec exclusion de `reference/`).

#### [MODIFY] [Projects/BoireFrere_Reception/](file:///c:/Memory%20Loop/Projects/BoireFrere_Reception)
- Supprimer les 5 sous-READMEs (`docs/00-ingested/README.md`, `docs/01-architecture/README.md`, `docs/02-business-rules/README.md`, `docs/03-models/README.md`, `memory/README.md`).
- Créer `AGENTS.md`, `opencode.json` et `.gitignore`.

#### [MODIFY] [Projects/rbc-avion-metro/](file:///c:/Memory%20Loop/Projects/rbc-avion-metro)
- Créer `AGENTS.md`, `opencode.json` et `.gitignore`.

---

## 🧪 Verification Plan

### Automated Tests
1. Exécution de la suite complète de tests mLoop :
   ```powershell
   pytest tests/ -v
   ```
2. Validation de l'Auto-Calibration globale :
   ```powershell
   python src/swarm.py calibrate --project Metro_OneTrust
   python src/swarm.py calibrate --project Metro_Food
   ```
3. Validation de la conformité Agent Plugins 1.0 :
   ```powershell
   python src/swarm.py plugin-validate --project mLoop
   ```

### Validation Manuelle
1. Exécution d'un test de création de projet temporaire pour vérifier le scaffolding automatique :
   ```powershell
   python src/swarm.py code-init --project TestAppScaffold
   ```
   *(Vérifier la création immédiate des 4 fichiers racines et l'absence de sous-READMEs, puis nettoyer).*
2. Vérification qu'aucun sous-README ne subsiste dans `Projects/` :
   ```powershell
   Get-ChildItem -Path "c:\Memory Loop\Projects" -Filter "README.md" -Recurse | Where-Object { $_.FullName -notmatch "node_modules|reference|\\\.git" }
   ```
