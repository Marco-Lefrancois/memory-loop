# 🏗️ Plan d'Implémentation : Simplification des READMEs & Intégration d'un Binôme `AGENTS.md` + `opencode.json` par Projet

## 🎯 Objectif
Éliminer la prolifération de fichiers `README.md` dispersés dans chaque sous-répertoire (qui créent du bruit, de la redondance et de la charge mentale inutile) pour adopter une structure épurée et hautement efficace :
1. **Un seul `README.md` canonique** à la racine de chaque projet (axé sur la compréhension humaine et la documentation d'équipe).
2. **Un fichier `AGENTS.md` dédié** à la racine du projet (contenant les règles métier spécifiques, les guardrails et la gouvernance d'état pour les agents IA).
3. **Un fichier `opencode.json` dédié** à la racine du projet (permettant d'ouvrir le projet de manière 100% autonome dans `opencode` avec ses serveurs MCP et ses raccourcis d'action).
4. **Nettoyage chirurgical** de tous les sous-fichiers `README.md` redondants dans les sous-dossiers (`backlog/`, `docs/`, `memory/`, `reference/`).

---

## 🧐 Analyse de la Conception : Pourquoi c'est une excellente décision ?

| Approche Précédente (1 README par dossier) | Nouvelle Approche Proposée (1 README + AGENTS.md + opencode.json) |
| :--- | :--- |
| ❌ **Pollution de jetons** : Les outils de recherche et agents lisent 10 READMEs partiels au lieu de trouver l'information utile. | ✅ **Économie de contexte** : Un seul README humain + un seul `AGENTS.md` pour l'amorçage IA. |
| ❌ **Dette de synchronisation** : Mettre à jour 10 READMEs lors d'une évolution de standard engendre inévitablement des désalignements (drift). | ✅ **Source de Vérité Unique (SSOT)** : Une seule référence racine pour l'équipe, une seule pour les agents. |
| ❌ **Projet non-autonome dans OpenCode** : Nécessite d'ouvrir la racine globale `C:\Memory Loop` pour avoir les serveurs MCP et commandes. | ✅ **Autonomie Multi-Clients** : N'importe quel projet (`Metro_OneTrust`, `Metro_Food`) peut être ouvert directement dans OpenCode / Antigravity / Cursor avec son propre contexte isolé. |

---

## 🚨 User Review Required

> [!IMPORTANT]
> **Cas pilote prioritaire : `Projects/Metro_OneTrust`**
> Nous appliquerons cette nouvelle architecture d'abord sur `Projects/Metro_OneTrust` (qui possède actuellement 10 sous-READMEs redondants), puis nous fournirons le gabarit reproductible pour tous les projets mLoop.
> Aucun document métier (`docs/`), récit (`backlog/stories/`) ou fichier de scan (`reference/`) ne sera supprimé ou altéré : seuls les 10 fichiers `README.md` parasites des sous-répertoires seront purgés.

---

## 🛠️ Proposed Changes

### 1. Projet Pilote : `Projects/Metro_OneTrust`

#### [DELETE] [Sous-fichiers README redondants](file:///c:/Memory%20Loop/Projects/Metro_OneTrust)
Suppression des 10 sous-fichiers `README.md` parasites :
- `Projects/Metro_OneTrust/backlog/README.md`
- `Projects/Metro_OneTrust/backlog/reviews/README.md`
- `Projects/Metro_OneTrust/docs/README.md`
- `Projects/Metro_OneTrust/docs/00-ingested/README.md`
- `Projects/Metro_OneTrust/docs/01-architecture/README.md`
- `Projects/Metro_OneTrust/docs/02-business-rules/README.md`
- `Projects/Metro_OneTrust/docs/04-transverse/README.md`
- `Projects/Metro_OneTrust/memory/README.md`
- `Projects/Metro_OneTrust/reference/README.md`
- `Projects/Metro_OneTrust/reference/OneTrust_Apps_Scans/README.md`

#### [MODIFY] [Projects/Metro_OneTrust/README.md](file:///c:/Memory%20Loop/Projects/Metro_OneTrust/README.md)
- Consolider le `README.md` racine pour présenter l'ensemble de la cartographie du projet, la Loi 25, les applications couvertes (Food, Santé), les classeurs de scans consolidés et le mode d'emploi humain.

#### [NEW] [Projects/Metro_OneTrust/AGENTS.md](file:///c:/Memory%20Loop/Projects/Metro_OneTrust/AGENTS.md)
- Créer le guide d'orchestration propre à `Metro_OneTrust` :
  - Boot Sequence du projet (`swarm.py resume --project Metro_OneTrust`).
  - Règles d'or Loi 25 & OneTrust MAUI (Mode Basic, Zero-Leak).
  - Directive Lead Dev Renaud (ADR-0319 : Zéro code physique dans les récits, contrats déclaratifs).
  - Séparation stricte des 3 piliers (`reference/`, `docs/`, `backlog/`).

#### [NEW] [Projects/Metro_OneTrust/opencode.json](file:///c:/Memory%20Loop/Projects/Metro_OneTrust/opencode.json)
- Configurer l'environnement OpenCode dédié au projet :
  - Déclaration des serveurs MCP (`loop_mem`, `graphify`, `codegraph`).
  - Déclaration des raccourcis CLI spécifiques (`loop-explore`, `loop-grill`, `loop-sync`).
  - Déclaration des règles d'exclusion du watcher (`memory/cache/**`, `.codegraph/**`).

---

### 2. Standardisation Globale mLoop Framework (`standards/`)

#### [NEW] [standards/blueprints/project_agents_template.md](file:///c:/Memory%20Loop/standards/blueprints/project_agents_template.md)
- Gabarit officiel pour générer automatiquement le `AGENTS.md` et `opencode.json` lors de la création d'un nouveau projet (`swarm.py code-init`).

---

## 🧪 Verification Plan

### Automated Tests
1. Exécution de la suite complète de tests mLoop :
   ```powershell
   pytest tests/ -v
   ```
2. Validation de la conformité Agent Plugins 1.0 :
   ```powershell
   python src/swarm.py plugin-validate --project mLoop
   ```

### Validation Manuelle & Git
1. Vérification de l'arborescence épurée de `Metro_OneTrust` :
   ```powershell
   Get-ChildItem -Path "c:\Memory Loop\Projects\Metro_OneTrust" -Filter "README.md" -Recurse
   ```
   *(Devra retourner uniquement le `README.md` racine).*
2. Audit Sentinel / Rubber Duck pour valider la non-régression documentaire.
