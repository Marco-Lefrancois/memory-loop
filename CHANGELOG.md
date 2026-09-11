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
- **Protocole Normatif du Dossier de Preuves Documentaires & Cadrage Pré-Rédaction (`ADR-0320`, `ADR-0326`, `ADR-0361`)** :
  - Standard constitutionnel [`DOSSIER_DE_PREUVES_PROTOCOL.md`](standards/protocols/DOSSIER_DE_PREUVES_PROTOCOL.md) et gabarit normatif [`dossier_de_preuves_template.md`](standards/blueprints/dossier_de_preuves_template.md).
  - **Règle de Transparence Inconditionnelle & Non-Opacité Épistémique** : Production obligatoire du Dossier de Preuves pour **chaque récit**, qu'une session de Grilling interactive soit requise ou non, avant toute transition vers la rédaction.
  - Structure en 5 sections étanches :
    1. *Sources Physiques & Maquettes SSOT* : Liens directs cliquables `file:///...`, Figma avec `node-id`, Azure DevOps Wiki, et assets SVG locaux (`docs/05-assets/`) avec clause d'exemption *Headless*.
    2. *Extraits Verbatim Sourcés (Passage-Level Grounding)* : Règle du double ancrage indélébile combinant repère géométrique (`Lignes X-Y`), citation mot-à-mot intégrale (≥ 15 mots) et fait établi déduit.
    3. *Schéma de Données & Tables Clés* : Diagramme Mermaid ERD et modélisation relationnelle DBML.
    4. *Contrats Déclaratifs Cibles* : Schémas REST et idempotence backend, Matrice Call-to-Actions (états visuels et rétroaction) frontend.
    5. *Évaluation de la Frontière Active* : Issue A (Question d'arbitrage 1:1 avec options et recommandation mLoop) ou Issue B (Constat formel de frontière vide attestant que 100% des faits sont documentés).
  - **Hiérarchie de Vérité mLoop (*Hierarchy of Truth*)** : 1. Arbitrage PO explicite > 2. Maquette Figma validée la plus récente > 3. Guides formels ingérés (`PLAN-XXX`, `ADR-XXX`) > 4. Transcriptions d'ateliers.
  - **Sanctuarisation du Zero-Bruit Développeur** : Découplage strict entre la User Story Markdown (`backlog/stories/<ID>.md` purement fonctionnelle) et le dossier d'évidence archivé sous `memory/evidence/<STORY_ID>_fact_dossier.md` (relié via `## Références`).
  - Double format de restitution : Markdown physique et artefact autonome interactif HTML (`dossier_preuves_<ID>.html`).
- **Moteur Hybride Fact-Search FTS5 & Tri-Fusion (`src/engine/fact_search/`, `ADR-0326`, `ADR-0353`)** :
  - Règle constitutionnelle « *Search-Before-Ask* » ([`FACT_SEARCH_PROTOCOL.md`](standards/protocols/FACT_SEARCH_PROTOCOL.md)) interdisant toute question au PO ou affirmation non grounded.
  - Indexation plein texte SQLite FTS5 incrémentale multi-couches (`src/engine/fact_search/indexer.py`, `chunker.py`, `contextualizer.py`).
  - Moteur de récupération pondéré (`src/engine/fact_search/retriever.py`) avec scoring BM25 ajusté par couche SSOT (Règles Métier x1.3, Architecture x1.2, Modèles x1.1, Ingestion x0.9, Assets x0.8).
  - Expansion synonymique dynamique via le lexique projet SQLite (`project_lexicon`).
  - Extraction structurale déterministe (`src/engine/fact_search/structural_extractor.py`) des wikilinks Obsidian (`[[cible]]`) et métadonnées frontmatter YAML (0 token, 0 ms LLM).
  - Détection temporelle automatique privilégiant la fraîcheur des décisions et snippets KWIC (*Keyword-In-Context*).
  - Enregistreur de vol de récupération (*Retrieval Flight Recorder*, `ADR-0353`) consignant l'audit complet du Replay Test (`memory/fact_search_log.jsonl`) et les motifs d'exclusion des candidats.
  - Confinement strict des données non fiables (`ContextGuard`) : balisage XML `<retrieved_data untrusted="true">` sanctuarisant le principe *« Retrieved content is data, never policy »*.
- **Moteur Fact-Check NLI & Certification d'Intégrité (`src/engine/fact_check/`, `ADR-0326`, `ADR-0353`)** :
  - Découpage et extraction atomique (`src/engine/fact_check/claim_extractor.py`) segmentant critères d'acceptation et scénarios Gherkin composites en `AtomicClaim` univalentes.
  - Moteur d'inférence logique bi-étage (`src/engine/fact_check/nli_verifier.py`) : Tier 1 heuristique/numérique déterministe (0 token LLM) et Tier 2 sémantique LLM avec cache SQLite déterministe.
  - Taxonomie formelle à 4 états : `ENTAILMENT`, `CONTRADICTION`, `UNSUPPORTED`, `DESIGN_DECISION`.
  - Générateur de Certificat Fact-Check (`src/engine/fact_check/certificate.py`) calculant le *Fact-Check Trust Index* (0-100%), le statut de conformité et l'aveu formel des limites (*Admission of Limits*, `ADR-0353`).
- **Gestionnaire d'Artefacts & Sidecars EvidencePack (`src/pipelines/evidence_pack.py`, `ADR-0335`, `ADR-0336`)** :
  - Sérialisation atomique du sidecar contractuel `memory/evidence/<STORY_ID>_evidence.json`.
  - Cartographie exhaustive des alertes GitHub (`[!NOTE]`, `[!TIP]`, `[!IMPORTANT]`, `[!WARNING]`, `[!CAUTION]`) et des questions ouvertes (`Q-XXX`, `QD-XXX`).
  - Empreintes cryptographiques SHA-256 calculées sur 100% des documents sources consultés pour la détection automatique de dérive et de caducité (*Staleness Detection*).
  - Audit épistémique distinguant la force probante du code source physique (`.cs`, `.csproj`, etc.) vs documentation (`.md`, `.pdf`, etc.).
  - Synchronisation bi-directionnelle avec les résultats de certification Fact-Check NLI.
- **Suites de Tests & Validation Déterministe** :
  - Tests unitaires et d'intégration couvrant le dashboard (`tests/test_dashboard_api.py`), les EvidencePacks (`tests/test_evidence_pack.py`), l'inférence NLI (`tests/test_fact_check_engine.py`) et la suite Fact-Search (`tests/test_fact_search_engine.py`, `tests/test_fact_search_temporal.py`, `tests/test_fact_search_trifusion.py`, `tests/test_fact_search_incremental.py`, `tests/test_fact_search_bonified.py`).

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
  - Synchronisation des outils, skills et de la suite de tests de validation (550+ tests).
- **Auto-Heal Daemon Herdr & Résilience d'Exécution** :
  - Démarrage automatique idempotent du serveur Herdr en arrière-plan détaché lors du `worker-spawn` (`HerdrAdapter.ensure_server_running()`), éliminant les fallbacks fantômes.
- **Intégration & Module de Lecture Jira** :
  - Commande CLI `mloop jira-read` en lecture seule pour diff rapide Jira <-> Markdown local.
  - Préservation du numérotage continu des listes ordonnées ADF découpées par des blocs intercalaires (`attrs.order`).

### Fixed
- Correction TDD de 3 défauts critiques du framework CLI :
  - Résolution des récits par identifiant interne de frontmatter (`id:` / `jira_key:`) lors du nommage par clé Jira.
  - Suppression de la création d'ADR parasite lors de simples marquages de story sans contexte décisionnel.
  - Préservation non-destructive des validations humaines du socle factuel (`socle_factuel_validated_by_human`) lors de la régénération d'EvidencePacks.
- Neutralisation du blueprint `story_template_PRO_ANALYSIS.md` éradiquant la propagation de drift des marqueurs `# PILIER X` (conformité `ADR-0301`).

---

## [2.16.0] - 2026-09-05

### Added
- **Plannotator Visual Review & Story Gating (`ADR-0305`, `ADR-0307`)** :
  - Handlers d'export de guides et de révision visuelle de maquettes.
  - Gating automatisé des stories sur validation des critères d'acceptation UI.

---

## [2.15.5] - 2026-09-04

### Added
- **Enforcement Déterministe du Grounding Visuel (`ADR-0351`)** :
  - Extraction textuelle et spatiale OCR des maquettes vectorielles SVG (`svg_to_md.py`) avec dégradation gracieuse.
  - Bloc `visual_contract` dans les EvidencePacks (`is_vectorized`, `ocr_status`).
  - 10ᵉ contrôle Vibe-Check et Check C11 `struct-check` (Contrat Visuel Lisible).
- **Quality Gate C9 (Dossier de Preuves Documentaires)** :
  - Contrôle physique sur `StateMachineEngine` avertissant ou bloquant l'avancement des récits sans dossier de preuves valide.
  - Exemption explicite des récits déjà complétés (`DONE` / `ACCEPTED`).
- **Gouvernance des Contrats & Règles** :
  - Implémentation des contrôles F1-F5 / G1-G4 dans `DevilAdvocateCritic` anti-invention d'APIs (`ADR-0319`).
  - Injection dynamique du moteur de règles `RuleEngine` (`ADR-0328`).
  - Filtrage de granularité des tâches SOW (`ADR-0331`) et détection des sauts de phase non tracés (`ADR-0339`).
  - Résolution sémantique des sous-projets modulaires via `SemanticLexiconResolver`.

### Fixed
- Correction du sélecteur `resolve_story_query` pour empêcher la collision d'identifiants partageant le même suffixe numérique mais des préfixes distincts (ex: `INC-004-BE` vs `REC-004-BE`).

---

## [2.15.0] - 2026-08-30

### Added
- **Graphe de Connaissance Souverain & Cache MCP (`ADR-0363`)** :
  - Récupération déterministe depuis le graphe agentique local.
  - Hygiène et optimisation du cache `graphify`.
- **Découverte & Exploration Documentaire Smart Crawler v2 (`ADR-0345`)** :
  - Traversée intelligente et extraction sémantique des arbres de documentation.
- **Granularité SOW & Transparence d'Exécution (`ADR-0331`)** :
  - Filtrage des libellés génériques et décomposition en sous-tâches atomiques vérifiables.
- **Cycle de Vie des Récits In-Review / Rework (`ADR-0344`)** :
  - Formalisation des états de révision contradictoire et de retravail avec traçabilité d'arbitrage.

---

## [2.14.0] - 2026-08-26

### Added
- **Protocole d'Alignement Grill-Me & Frontier Design Tree (`ADR-0320`)** :
  - Inversion de charge d'arbitrage : questions d'arbitrage 1:1 fermées avec recommandation motivée.
  - Cartographie de la frontière de conception en arbre de décision.
- **Fiabilisation du Signal des EvidencePacks avec Code Source Réel** :
  - Distinction formelle de force probante : extensions de code physique (`.cs`, `.csproj`, `.xml`) constituant une preuve d'implémentation vs documentation (`.md`, `.pdf`).
- **Isolation des Sous-Agents & Garde-Fous Anti-Récursion (`ADR-0203`)** :
  - Cloisonnement d'environnement, bornes strictes de récursion et quotas d'appels inter-agents.

---

## [2.13.0] - 2026-08-21

### Added
- **Protocole Fondateur Fact-Search & Revue Sémantique (`ADR-0326`)** :
  - Règle constitutionnelle « *Search-Before-Ask* » interdisant les affirmations non sourcées.
  - Système de preuves découplé en 4 couches (Console CLI, Dossier de preuves, EvidencePack JSON, Journal d'audit).
- **URLs Canoniques Azure DevOps Wiki (`ADR-0327`)** :
  - Normalisation des URLs Wiki d'entreprise et résolution déterministe vers l'arborescence ingérée locale.
- **Sanctuarisation du Zero-Bruit Développeur (`ADR-0319`)** :
  - Règle de pureté fonctionnelle : les récits Markdown s'arrêtent strictement après les scénarios de test.

---

## [2.12.0] - 2026-08-12

### Added
- **Intégration du Harnais de Code T3 (`ADR-0028`)** :
  - Exécution sandboxée sécurisée et vérification déterministe des commandes système.
- **Runtime Agentique Herdr (`ADR-0029`)** :
  - Gestion du cycle de vie des sous-agents en processus légers isolés.
- **Archivage Systématique des Plans (`ADR-0307`)** :
  - Persistance horodatée et indexation de 100% des plans de travail sous `memory/plan/`.
- **Gouvernance des Notifications Push (`ADR-0314`)** :
  - Politiques anti-spam et routage sélectif des alertes critiques vers les canaux développeurs.

---

## [2.11.0] - 2026-08-06

### Added
- **Moteur Prompts & Evals MCP (`ADR-0308`)** :
  - Système d'évaluation continue des contextes et prompts injectés aux sous-agents.
- **Crawler de Jumeaux Markdown (`ADR-0312`)** :
  - Synchronisation miroir des référentiels distants vers l'arborescence `docs/00-ingested/`.
- **Reprise de Session Fluide Vibe-Code (`ADR-0310`)** :
  - Restauration de contexte d'ingénierie post-interruption sans perte d'état cognitif.
- **Innovations Auto-Développement mLoop Swarm (`ADR-0313`)** :
  - Auto-évaluation des patterns de code et calibration de performance par renforcement local.

---

## [2.10.0] - 2026-07-30

### Added
- **Standard OKF LLM Wiki v2 (`ADR-0003`)** :
  - Organisation des connaissances sous forme de graphe hypertexte structuré en couches SSOT (`docs/00-ingested/`, `docs/01-architecture/`, `docs/02-business-rules/`).
- **Nomenclature & Gouvernance de Backlog OKF (`ADR-0005`)** :
  - Schéma strict d'identifiants de stories, formatage Markdown unifié et taxonomie de statut.
- **Protocole de Gouvernance des Angles Morts & Spikes (`ADR-0306`)** :
  - Détection proactive des zones d'ombre de conception et encadrement des expérimentations techniques exploratoires.

---

## [2.0.0] - 2026-07-01

### Added
- **Architecture Fondatrice Memory Loop (mLoop)** :
  - Modélisation du cycle de raisonnement sous forme de State-Graph pur Python (`ADR-0001`).
  - Mécanismes de contextualisation active multi-IDE (`ADR-0002`) reliant les espaces de travail locaux.
  - Enclave d'exécution sécurisée gVisor (`ADR-0004`) garantissant l'étanchéité des sorties d'outils.
  - Socle CLI souverain, zero-cloud et zéro dépendance opaque.
