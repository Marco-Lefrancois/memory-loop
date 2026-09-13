# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère aux principes de [Semantic Versioning](https://semver.org/lang/fr/).

---

## [2.22.0] - 2026-09-13

### Added
- **Standardisation OpenSpec & Verticalité Fonctionnelle Pure (`ADR-0366` Bonifié)** :
  - Sanctuarisation de la sous-section `### 3. Paquet OpenSpec (Handoff Développeur)` reprenant la triade native d'OpenSpec (`proposal.md`, `specs/api.md`, `tasks.md`) et la Definition of Done (`definition-of-done.md`).
  - Intégration du pattern Dual-Link distant Azure DevOps Git (`Wiki_AF_Segment2`) + chemin relatif Markdown au sein du dépôt Git, avec proscription formelle des liens absolus `file:///C:/...` non portables.

### Changed
- **Épure Fonctionnelle Pure des Récits Utilisateurs** :
  - Retrait intégral de la table « Matrice des Réponses HTTP » dans les critères d'acceptation des récits fonctionnels au profit de règles d'admissibilité et cas de rejet purement métier (zéro fuite de plomberie HTTP dans le récit).
  - Tous les codes de transport HTTP (200, 400, 409), schémas JSON et erreurs RFC 7807 sont isolés dans `specs/api.md` d'OpenSpec.
  - Zéro-bruit de gouvernance : retrait de la revue interne Sentinel / Rubber Duck du corps de la User Story (archivée sous `backlog/reviews/`).
- **Linter Structurel (`src/pipelines/struct_checker.py`)** :
  - Support natif des titres canoniques OpenSpec (`paquet openspec`, `paquet openspec (handoff développeur)`).

---

## [2.21.0] - 2026-09-13

### Added
- **Standard Constitutionnel Story 2.0 & Handoff Tripartite (`ADR-0366`)** :
  - Établissement de la chaîne de valeur à 4 étages : *Amont (Preuves Fact-Search) ➔ Cœur (Story 2.0 Fonctionnelle No-Code) ➔ Aval (Handoff Tripartite Déclaratif) ➔ Exécution (TDD & DoD)*.
  - Standardisation de l'arborescence du handoff technique sous `backlog/handoff/<STORY_ID>/` dans les projets clients mLoop, préservant strictement la Loi des 3 Piliers (ADR-0100) et projetable 1:1 vers `openspec/changes/<STORY_ID>/` dans le dépôt applicatif du développeur.
  - Gabarit normatif [`standards/blueprints/handoff_tripartite_template.md`](standards/blueprints/handoff_tripartite_template.md) formalisant la triade souveraine :
    - `proposal.md` : Rationale technique, impact sur les tables de données et sécurité.
    - `specs/api.md` : Schémas JSON typés, contrats d'échange et codes HTTP.
    - `tasks.md` : Découpage en micro-tâches atomiques (< 5 fichiers) suivant le cycle Red-Green-Refactor et la Règle de Beyoncé.
  - Normalisation de la section `## Références` en 3 sous-blocs étanches avec pattern **Dual-Link** systématique (Lien distant Web Azure DevOps / GitHub + Lien workspace local `file:///...`).
  - Clause anti-fuite de pagination (calculs globaux de priorité et minima côté serveur) et typage strict des dates en ISO 8601 (`YYYY-MM-DD`).

### Changed
- **Gabarit Maître des Récits (`standards/blueprints/story_template.md`)** :
  - Intégration harmonieuse des titres canoniques pour récits `layer: backend` (`Opérations Métier & Logique Backend`, `Matrice des Réponses HTTP & Filtres Métier`, `Contrats d'échange API`) et `layer: frontend` (`Spécifications de l'Interface`, `Liste Call to Actions`).
  - Normalisation complète du bloc `## Références` à 3 sous-blocs et du 4e pilier Gherkin (Empty State obligatoire).
- **Checklist Qualité INVEST (`.agents/references/invest-story-checklist.md`)** :
  - Ajout des points de contrôle d'intégrité référentielle (Dual-Link, handoff aval `tasks.md`), anti-fuite de pagination et gestion de l'Empty State.

### Fixed
- **Pipeline de Contrôle Structurel (`src/pipelines/struct_checker.py`)** :
  - Élimination des faux positifs C4 Gold Standard Diff : normalisation des titres H3/H4 et tolérance des sections canoniques backend (`layer: backend`).
  - Résolution déterministe de `gold_standard_ref` en mode `--strict` : reconnaissance des chemins directs et du dossier `standards/blueprints/`.
- **Moteur d'EvidencePack (`src/pipelines/evidence_pack.py`)** :
  - Résolution des sources sous `memory/evidence/`, `memory/`, `backlog/handoff/`, `standards/` et `.agents/`.
  - Calcul direct de l'empreinte SHA-256 pour 100% des fichiers trouvés sur disque (élimination des statuts dégradés `NOT_CALCULATED_LOCAL_ONLY` et des alertes "introuvable sur disque").
  - Décodage URL préalable (`urllib.parse.unquote`) et support des caractères accentués dans l'extraction des sources.

---

## [2.20.0] - 2026-09-13

### Added
- **Harmonisation Symbiotique des Compétences & Standard Agent-Skills (`ADR-0365`)** :
  - Adoption de la norme **Skill Anatomy 2.0** pour l'ensemble du catalogue `.agents/skills/` (frontmatter typé avec clause explicite `Use when...`, déroulé opérationnel, tables anti-rationalisation inviolables, signaux d'alerte et vérification de sortie par preuves factuelles).
  - Intégration de 15 compétences d'ingénierie logicielle d'état de l'art issues d'Addy Osmani (`addyosmani/agent-skills`) :
    - `test-driven-development` : TDD Red-Green-Refactor, Règle de Beyoncé, pyramide de tests, DAMP vs DRY.
    - `source-driven-development` : Grounding officiel sur SDKs et documentations en ligne versionnées, inspection read-only des dépendances réelles sans génération de code physique dans les projets clients.
    - `doubt-driven-development` : Vérification contradictoire in-flight en contexte vierge et traque systématique des hypothèses tacites.
    - `spec-driven-development` : Rédaction de spécifications formelles, PRDs et contrats d'interfaces avant tout code.
    - `constraint-driven-development` : Bornes de qualité non négociables, budgets de performance et gardiens d'intégrité.
    - `planning-and-task-breakdown` : Graphe de sous-tâches physiques atomiques ordonnées par dépendance (< 5 fichiers, handoff OpenSpec ready).
    - `incremental-implementation` : Implémentation par tranches verticales minces commitées avec validation continue.
    - `context-engineering` : Gestion du budget de contexte (< 75%), compression d'historique et élimination du lost-in-the-middle.
    - `code-simplification` : Refactoring chirurgical sans changement de comportement (principe de la barrière de Chesterton).
    - `security-and-hardening` : Prévention OWASP Top 10, détection de secrets, audits de dépendances et moindre privilège.
    - `performance-optimization` : Profiling, détection de requêtes N+1, budgétisation de latence et Core Web Vitals.
    - `shipping-and-launch` : Déploiement progressif (Canary), feature flags, observabilité active et seuils de rollback.
    - `api-and-interface-design` : Conception de contrats d'API déclaratifs, schémas REST / gRPC et gestion d'erreurs typées.
    - `browser-testing-with-devtools` : Vérification visuelle, inspection DOM et capture de traces console via Chrome DevTools MCP.
    - `debugging-and-error-recovery` : Diagnostic systématique des causes racines d'anomalies et procédures de rétablissement.
  - Hub de Checklists Partagées (`.agents/references/`) :
    - 7 checklists d'ingénierie Addy : `definition-of-done.md`, `security-checklist.md`, `performance-checklist.md`, `accessibility-checklist.md`, `observability-checklist.md`, `orchestration-patterns.md`, `testing-patterns.md`.
    - 5 checklists souveraines mLoop couvrant 100% des phases : `invest-story-checklist.md`, `fact-search-grounding-checklist.md`, `adr-decision-checklist.md`, `herdr-worker-checklist.md`, `sync-and-release-checklist.md`.
- **Améliorations du Pipeline Python `src/` & Métrologie** :
  - `src/pipelines/crawler.py` : Revalidation conditionnelle HTTP 304 (RFC 9110) via en-têtes `If-None-Match` (ETag) et `If-Modified-Since` avec réutilisation instantanée du cache Markdown.
  - `src/pipelines/skill_doctor.py` : Détection de collisions lexicales de routing (similarité cosinus TF-IDF > 75%), vérification de la syntaxe des déclencheurs (`Use when...`), et distinction formelle entre le budget de démarrage (descriptions boot < 15 000 jetons) et le volume de référence à la demande.
  - `src/pipelines/calibrate.py` : Validation de l'exhaustivité de l'index du routeur (`[3/8]`) et audit d'hygiène mémorielle (`[3/8-bis]`).
- **Standard d'Inspiration OpenSpec sans Dépendance Externe** :
  - Formalisation de l'export de sous-tâches atomiques au format tripartite Markdown (`proposal.md`, `specs/`, `tasks.md`) dans `plan` et `planning-and-task-breakdown`, sans aucune installation de binaire ni dépendance npm/Node.js.

### Changed
- **Refonte et Condensation Majeure des 4 Compétences Maîtresses mLoop** :
  - `grill` : Allégé de 3 672 à ~600 tokens. Déport des gabarits vers `standards/blueprints/dossier_de_preuves_template.md`, intégration de la mécanique *interview-me* (hypothèse initiale, confidence score %, questions 1:1 avec guess attaché, question brise-glace *Want vs Should Want*).
  - `plan` : Allégé de 4 280 à ~700 tokens. Recentrage sur le découpage vertical INVEST, la symétrie FE/BE (Profil B), le filtrage des ADRs Type 1 et la délégation du graphe de sous-tâches physiques à `planning-and-task-breakdown`.
  - `sentinel` : Allégé de 2 604 à ~650 tokens. Intégration du cycle du doute en 5 étapes (`CLAIM` ➔ `EXTRACT` ➔ `DOUBT` ➔ `RECONCILE` ➔ `VERDICT`) et des 4 axes d'attaque non-négociables.
  - `herdr-orchestration` : Allégé de 2 557 à ~550 tokens. Matrice stricte des 4 critères de déclenchement Fork & Harvest, prompts isolés par fichier scratch et Teardown Gate anti-zombies.
- `impeccable` : Condensé sous 1 500 tokens avec intégration de la clause `Use when...` et des 16 règles anti-slop IA.
- `router/SKILL.md` : Mise à jour intégrale de la cartographie thématique des 36 compétences actives.
- Synchronisation des directives d'amorçage de 11 compétences mLoop avec l'adjonction de la clause normalisée `Use when...` (`archify`, `blindspot-scan`, `calibrate`, `design-taste`, `graph-engineering`, `markitdown`, `rubber-duck`, `svg-ocr`, `svg-optimize`, `triage`, `wait-what`).

### Deprecated & Archived
- **Archivage Propre dans `memory/archive-skills/`** :
  - Retrait du catalogue actif et archivage documenté de 14 compétences redondantes ou sur-spécifiées :
    - `tdd` (remplacé par `test-driven-development`).
    - 6 compétences de réflexion abstraite (`thinking-cynefin`, `thinking-kepner-tregoe`, `thinking-reversibility`, `thinking-theory-of-constraints`, `thinking-triz`, `thinking-via-negativa`).
    - 7 compétences doublons (`teach`, `office`, `analyze`, `research`, `research-and-develop`, `validate`, `sop`).
  - Création de `memory/archive-skills/README.md` avec la table de correspondance exhaustive.

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
- **Moteur d'Isolation Physique & Bac à Sable (`SandboxRunner`)** :
  - Exécution sécurisée des commandes avec restrictions mémoires et CPU (Job Objects sous Windows, Bubblewrap & Landlock sous Linux).
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
- **Architecture Fondatrice Memory Loop (mLoop v2.0)** :
  - Unification majeure du cycle de raisonnement sous forme de State-Graph pur Python 3.12+ (`ADR-0001`).
  - Mécanismes avancés de contextualisation active multi-IDE (`ADR-0002`) reliant les espaces de travail locaux.
  - Enclave d'exécution sécurisée gVisor (`ADR-0004`) garantissant l'étanchéité des sorties d'outils.
  - Socle CLI souverain, zero-cloud et consolidation complète du runtime mLoop v2.

---

## [1.9.0] - 2026-06-30

### Added
- **Segmentation Cognitive Memory Loop vs OpenSpec (`ADR-0103`)** :
  - Établissement de la frontière hermétique entre l'espace d'analyse mLoop (`backlog/`, `docs/`, `memory/`) et l'espace d'implémentation applicative physique (`openspec/`, `src/`).
  - Proscription formelle des répertoires `src/` et `openspec/` au sein des projets en mode `ProjectMode.CLIENT`.
- **Prémices de l'Orchestrateur Multi-Agents Herdr (`ADR-0029`)** :
  - Évaluation et premiers tests d'intégration du daemon d'exécution d'agents `herdr` (`herdrdev/herdr`) pour la gestion du cycle de vie de processus légers isolés.

### Changed
- **Homogénéisation de l'Arborescence Projet (`standards/adr-contracts.json`)** :
  - Intégration machine-readable des contrats de layout client et de layout framework pour l'outillage de validation.

---

## [1.8.0] - 2026-06-25

### Added
- **Gouvernance HITL, Phase 1 & Plan-First (`ADR-0305`)** :
  - Matrice de criticité à 3 niveaux : Niveau 1 Trivial (Zero-Gate), Niveau 2 Moyen (Micro-Plan chat), Niveau 3 Critique/Architecture (Plan Formel Bloquant).
  - Obligation du blueprint normatif [`standards/blueprints/plan_template.md`] avant toute modification structurelle ($\ge 3$ fichiers ou impact architectural).
  - Support de revue humaine unifiée entre Antigravity IDE (`implementation_plan.md`) et Plannotator CLI.
- **Modularité Interne des Agents & Seuils de Complexité (`ADR-0202`)** :
  - Règles de découpage granulaire des compétences pour prévenir l'agent drift et le dépassement des seuils de contexte par requête.

### Changed
- **Workflow de Cadrage Initial** :
  - Interdiction pour l'agent de présumer des intrants avant le dépôt physique préalable par l'humain dans `reference/`.

---

## [1.7.0] - 2026-06-18

### Added
- **Protocole Story-as-State & Machine à États FSM (`ADR-0302`)** :
  - Le champ `status` du Frontmatter YAML des récits devient la source unique de vérité de leur cycle de vie (`OPEN` $\rightarrow$ `IN_ANALYZE` $\rightarrow$ `READY_FOR_GROOMING` $\rightarrow$ `READY_FOR_DEV`).
  - Standardisation de l'interview `/grill-me` avec contrainte stricte d'une question recommandée à la fois pour éliminer la surcharge cognitive.
- **Gouvernance de Synchronisation Jira Anti-Drift (`ADR-0304`)** :
  - Séparation stricte des autorités : le Markdown local dans `backlog/` détient l'autorité de conception, Jira détient l'autorité de planification temporelle.
  - Proscription absolue des scripts jetables ou appels `curl` directs ; centralisation exclusive via `python src/swarm.py jira_sync`.

### Fixed
- **Conflits de Statuts Jira ↔ Markdown** :
  - Élimination des écrasements d'états et préservation de l'intégrité bidirectionnelle lors des synchronisations.

---

## [1.6.0] - 2026-06-09

### Added
- **Graph Loop Architecture & SSOT NetworkX (`ADR-0200`)** :
  - Exploitation du graphe de connaissances persistant sous `graphify-out/` généré lors des synchronisations.
  - Protocoles d'interrogation sémantique obligatoires (`graphify path`, `graphify query`, `graphify explain`) en amont de toute exploration documentaire linéaire.
- **Orchestration DAG Multi-Agents & Evidence Packs (`ADR-0201`)** :
  - Moteur d'exécution par graphe acyclique direct (`python src/swarm.py graph-run`) avec topologie en diamant (Fan-out $\rightarrow$ Barrier $\rightarrow$ Reducer $\rightarrow$ Evaluator).
  - Routage par le risque (*Risk-Based Routing*) : Fast-track pour risque `LOW`, revue contradictoire approfondie par `evaluator_node.py` pour risque `HIGH`/`CRITICAL`.
- **Compétences Cognitives Documentaires** :
  - Déploiement des compétences initiales de recherche et d'assimilation documentaire approfondie (`research`, `teach`).

---

## [1.5.0] - 2026-05-31

### Added
- **Standard Gherkin des 4 Piliers Obligatoires (`ADR-0301`)** :
  - Exigence non négociable de 4 scénarios distincts dans chaque récit : *Pilier 1 : Chemin Nominal (Happy Path)*, *Pilier 2 : Exceptions & Rejets Métier*, *Pilier 3 : Résilience Technique & Mode Dégradé*, *Pilier 4 : UX & Observabilité / Empty State*.
  - Proscription formelle des commentaires d'échafaudage (`# PILIER X`) dans le livrable final validé.
  - Règle de pureté absolue du titre `Fonctionnalité:` sans préfixes ou identifiants parasites.
- **Harnachement des Blueprints Markdown Zero-Drift (`ADR-0303`)** :
  - Centralisation du gabarit unique inviolable sous [`standards/blueprints/story_template.md`].
  - Interdiction stricte de paraphraser ou d'altérer la hiérarchie des sections H1/H2/H3.

---

## [1.4.0] - 2026-05-28

### Added
- **Structure Canonique et SSOT du Répertoire `docs/` (`ADR-0102`)** :
  - Découpage normé en 5 sous-dossiers : `00-ingested/` (matière première), `01-architecture/` (ADRs & synthèses), `02-business-rules/` (règles métier vivantes `RM-*`), `03-models/` (schémas), `04-transverse/` (questions ouvertes, glossaire).
  - Indexation sémantique globale via `docs/index.md` servant de point d'ancrage pour le graphe de connaissances.
- **Story Constraint Contract & Score INVEST Déterministe (`ADR-0300`)** :
  - Verrouillage de la frontière d'analyse avant transition vers `READY_FOR_GROOMING`.
  - Calcul automatique de conformité INVEST via `wikifix` avec seuil bloquant à 80%.
- **Premières Compétences Cognitives mLoop** :
  - Déploiement des compétences initiales d'analyse d'affaires et de contrôle qualité : `analyze`, `validate`, `sop`.

---

## [1.3.0] - 2026-05-12

### Added
- **Structure Canonique Projet Client (Loi des 3 Piliers) (`ADR-0100`)** :
  - Partitionnement étanche de l'espace de travail client : `reference/` (matière première humaine), `docs/` (SSOT architecture & règles), `backlog/` (spécifications & exécution), `memory/` (persistance & traces d'exécution), `graphify-out/` (graphe de connaissances).
- **Pipeline d'Ingestion MarkItDown Local (`ADR-0101`)** :
  - Abandon définitif des dépendances de serveurs RAG distants opaques.
  - Conversion locale et autonome des formats Office/PDF (DOCX, XLSX, PDF, PPTX) en Markdown pur sous `docs/00-ingested/`.
  - Registre persistant `memory/ingest_registry.json` et déduplication systématique par empreintes SHA-256.

---

## [1.2.0] - 2026-04-30

### Added
- **Harnais d'Exécution Sécurisée gVisor (`ADR-0004`)** :
  - Spécification de l'isolation d'exécution Système 1 (Kernel User-Space Sentry) pour interdire toute évasion de conteneur, *process fork* ou falsification de l'hôte.
  - Canaux de communication hors-bande (`:8888`) pour la télémétrie de sandboxing.
- **Gouvernance & Nomenclature de Backlog OKF (`ADR-0005`)** :
  - Standardisation de la taxonomie des récits (`ST-XXX`, `INC-XXX-BE`, `INC-XXX-FE`).
  - Règles de structuration sémantique du `sprint_backlog.md` et du `STORY_MAPPING.md`.

---

## [1.1.0] - 2026-04-15

### Added
- **Architecture de Contextualisation Active Multi-IDE (`ADR-0002`)** :
  - Découplage complet entre le moteur Python agnostique (`src/`) et les adaptateurs d'environnements de développement (`.agents/skills/` pour Antigravity, `opencode.json` pour OpenCode, `CLAUDE.md` pour Claude Code, `.vscode/tasks.json` pour VS Code).
  - Pipeline de réalignement et synchronisation automatique `python src/swarm.py calibrate`.
- **Moteur d'Ingestion AST Statique Graphify v1.1** :
  - Transition de Graphify d'un agent autonome vers un outil d'ingestion AST statique et lexical avec cache incrémental SHA-256 (`ingest_cache.json`).
- **Fondations de l'Open Knowledge Format v0.1 (`ADR-0003`)** :
  - Spécification initiale des métadonnées Frontmatter YAML pour documents d'architecture et règles métier.

---

## [1.0.0] - 2026-04-01

### Added
- **Agentic Coworker Framework & Loi Fondamentale (`ADR-0000`)** :
  - Établissement de la Constitution mLoop : séparation entre l'Ontologie (L'Être : Memory, Skills, Soul, Handoff, Self-Healing) et le Protocole (Le Faire : Délégation asymétrique, Backend d'État strict, Graph Loop, Cycle Plan-Analyze-Validate).
  - Sanctuarisation de la frontière étanche : mLoop est un backend d'analyse, d'état et de validation déterministe ; le code applicatif physique réside dans les dépôts clients dédiés.
- **Architecture par Graphe d'États Déterministe Python 3.12+ (`ADR-0001`)** :
  - Orchestration par State Graph typé avec validation Pydantic v2 (`src/state.py`).
  - Implémentation du CLI unifié `src/swarm.py` avec console Rich Zero-Fluff.
  - Mécanismes de garde-fous : plafonnement budgétaire de tokens (`TokenBudget`) et disjoncteurs anti-emballement (`MaxRevisionsReached`).
- **Socle de Persistance Locale SQLite FTS5** :
  - Stockage local déterministe sous `memory/cache/` pour la recherche textuelle plein texte sans dépendance cloud.
