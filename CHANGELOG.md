# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère aux principes de [Semantic Versioning](https://semver.org/lang/fr/).

---

## [2.19.0] - 2026-09-11

### Added
- **Tableau de Bord d'Observabilité & Supervision Souverain (`mloop dashboard`)** :
  - Serveur FastAPI & Uvicorn local autonome (*Zero-Docker*, 100% Python pur, données locales).
  - Commandes CLI `mloop dashboard` (alias : `mloop ui`, `mloop supervision`) avec support des drapeaux `--port` (défaut : 8080) et `--no-browser`.
  - Hub d'observabilité en temps réel avec endpoints REST dédiés :
    - `GET /api/health` : État de santé, flags souverains et projet actif.
    - `GET /api/projects` & `POST /api/project/select` : Liste et bascule dynamique entre projets (avec résolution canonique des alias).
    - `GET /api/metrics` : Agrégation des tokens consommés, coûts USD, modèles d'IA et répartition par actions.
    - `GET /api/events` : Flux d'événements et télémétrie en direct.
    - `GET /api/stories` : État d'avancement des User Stories du backlog et EvidencePacks associés.
    - `GET /api/graph` : Métriques du graphe de connaissances souverain (nœuds, arêtes, statut graphify).
    - `GET /api/state` : Statut du pipeline et progression des 6 phases du cycle de vie cognitif.
  - Interface utilisateur moderne embarquée (`src/dashboard/static/index.html`) :
    - Thème sombre épuré, responsive, cartes métriques en direct et barre d'avancement du cycle en 6 étapes.
    - Tableau de bord des stories avec badges de statut et preuves contractuelles.
    - Journal des événements live et sélecteur interactif de projet.
- **Suite de tests d'intégration** :
  - Validation exhaustive de l'API de supervision via `TestClient` (`tests/test_dashboard_api.py`, 9 tests validés à 100 %).

### Changed
- Ajout du `$schema` officiel OpenCode dans `.opencode/opencode.json`.
- Déclaration et routage du sous-système de dashboard dans le registre central des commandes CLI (`src/commands/_registry.py`).

---

## [2.18.0] - 2026-09-11

### Added
- **Protocole de Pré-Compaction Déterministe (`ADR-0364`)** :
  - Handler d'interception `PreCompactionHandler` (`src/engine/hooks/compaction.py`) se déclenchant avant la compaction du LLM ou au seuil critique de contexte (15 tours).
  - Sérialisation atomique du point de contrôle dans `memory/compaction/latest_checkpoint.json` avec validation d'intégrité par empreinte cryptographique SHA-256.
  - Schéma Pydantic strict `CompactionCheckpoint` capturant l'état Git actif, la story cible, les 4 Piliers Gherkin contractuels, les réservations de fichiers et les preuves de tests.
- **Triple Filet de Récupération (*Fail-Safe Recovery*)** :
  - Niveau 1 : Restauration atomique depuis `latest_checkpoint.json` vérifiée par hash SHA-256.
  - Niveau 2 : Bascule automatique sur l'historique archivé (`memory/compaction/history/checkpoint_<timestamp>.json`).
  - Niveau 3 : Reconstruction d'urgence de la vérité terrain depuis `memory/SESSION_MEMORY_HEALTH.md` et `backlog/sprint_backlog.md`.
- **Résolveur d'Alias & Micro-URIs Canoniques (`PathAliasResolver`)** :
  - Gain de **-75 % de tokens** sur les chemins physiques en remplaçant les chemins absolus par des micro-URIs : `assets://`, `evidence://`, `story://`, `model://`, `source://`.
  - Résolution synchrone en mémoire vive (0 ms, 0 I/O disque).
- **Garde-Fou Contextuel & Anti-Drift (`ContextGuard`)** :
  - Module `src/utils/context_guard.py` pour surveiller l'état du contexte et bloquer les commandes d'exploration aveugle (`ls -R`, `find`) post-compaction avec réinjection immédiate de l'invariant LOD-0 (≤ 400 tokens).
- **Commande CLI Dédiée** :
  - Nouvelle commande `mloop hook pre-compact` via `src/commands/handlers/hook.py` et intégrée au registre central `src/commands/_registry.py`.
- **Intégration Multi-Harnais (IDE & Agents)** :
  - Plugin OpenCode (`.opencode/plugins/mloop-compaction.js`) interceptant la commande `/compact` native de l'IDE.
  - Pont Google Antigravity (`src/bridges/antigravity_hook.py`) et contrat d'agents `.agents/hooks.json`.
- **Spécifications & Tests** :
  - Décision d'architecture formelle [`ADR-0364`](standards/adr-system/0364-hooks-pre-compaction-et-checkpoint-boundaries.md).
  - Suite de 10 tests unitaires et d'intégration validés à 100 % (`tests/test_pre_compaction_hooks.py`).

### Changed
- Mise à jour des chartes d'instructions agents (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) intégrant les nouvelles directives de pré-compaction et de résolution d'URIs.
- Enregistrement des nouveaux composants dans l'index des ADRs (`standards/adr-system/README.md`) et le guide de pipeline (`standards/protocols/CLI_PIPELINE_GUIDE.md`).
- Déclaration des hooks d'exécution dans `src/engine/hooks/__init__.py` et `src/engine/hooks/registry.py`.
- Mise à jour et renforcement de `.gitignore` : exclusion de `opencode.json` au profit d'un template `opencode.example.json`, déblocage des modèles `.env.example`, et couverture exhaustive des logs, bases SQLite WAL, caches Python et artefacts OS/IDE (JetBrains, etc.).

---

## [2.17.0] - 2026-09-09

### Added
- **Synchronisation Globale du Framework mLoop (`ADR-0339`)** :
  - Mise à jour du runner de cycle de vie en version v2.17.
  - Support de 5 types natifs dans le compilateur de cycle de vie.
  - Synchronisation des outils, skills et de la suite de tests de validation.

---

## [2.16.0] - 2026-09-05

### Added
- **Plannotator Visual Review & Story Gating (`ADR-0305`, `ADR-0307`)** :
  - Handlers d'export de guides et de révision visuelle de maquettes.
  - Gating automatisé des stories sur validation des critères d'acceptation UI.

---

## [2.15.0] - 2026-08-30

### Added
- **Graphe de Connaissance Souverain & Cache MCP (`ADR-0363`)** :
  - Récupération déterministe depuis le graphe agentique local.
  - Hygiène et optimisation du cache `graphify`.
