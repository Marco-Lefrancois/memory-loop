# 🏛️ Épopée — `EPIC-26-CLINE-ECOSYSTEM-HARNESS` : Intégration Avancée & Exploitation des Innovations Cline (Agent Teams, Memory Bank & Plan/Act)

---

> **Référence d'Architecture** : [ADR-0377](../../../../standards/adr-system/0377-runtimes-agents-aval-et-herdr-operationnels.md) (Runtimes d'Agents Aval & Herdr) · [ADR-0346](../../../../standards/adr-system/0346-multi-runtime-worker-registry.md) (Registre Multi-Runtimes) · [ADR-0202](../../../../standards/adr-system/0202-modularite-interne-agents.md) (Modularité ≤ 300L) · [ADR-0375](../../../../standards/adr-system/0375-standard-preuve-epistemique-et-tracabilite-radicale.md) (Traçabilité Radicale) · [ADR-0376](../../../../standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md) (Rigueur 360° Zéro Blindspot)  
> **Composant(s)** : `Bridges/Cline` · `Core/MemoryBankBridge` · `Core/HerdrWorkerCore` · `CLI/Cline` · `Pipelines/Sync`  
> **Origine / Déclencheur** : Aspiration et analyse documentaire (WebCrawlerAgent) de `cline.bot` et `docs.cline.bot` : émergence des **Agent Teams** coordonnés par tableau de tâches partagé (`cline --team-name`), méthodologie **Memory Bank** (`memory-bank/`), séparation étanche **Plan & Act**, et règles `.clinerules`.  
> **Statut** : `READY_FOR_DEV` — 5/5 Récits Palier 2 Certifiés (`status: READY_FOR_DEV`, `grill_me: DONE`, DoR 6/6, Fact Dossiers C9 Validés)  
> **Décideurs** : PO mLoop / Architecte Agentique  

---

## 🎯 1. Contexte & Intention Stratégique

La veille technologique menée via le crawler asynchrone mLoop sur l'écosystème **Cline** ([cline.bot](https://cline.bot) et [docs.cline.bot](https://docs.cline.bot)) met en lumière plusieurs innovations structurantes :
1. **Agent Teams & Task Board Partagé (`cline --team-name`)** :
   Cline introduit un mode d'équipe où un agent coordinateur orchestre des agents spécialistes via une boîte aux lettres inter-agents et un tableau de tâches persistant sous `~/.cline/data/teams/[team-name]/`.
2. **Le Standard Memory Bank (`memory-bank/`)** :
   Une structure hiérarchique documentaire standardisée (`projectbrief.md`, `productContext.md`, `activeContext.md`, `systemPatterns.md`, `techContext.md`, `progress.md`) qui confère aux agents une mémoire durable sans amnésie entre les sessions.
3. **Le Paradigme Plan & Act (`cline -p / --plan`)** :
   Un cloisonnement strict interdisant toute modification de fichier en mode planification (lecture seule), réservant l'action (`Act mode`) aux étapes explicitement validées.
4. **Gouvernance `.clinerules`** :
   Fichiers d'instructions modulaires sous `.clinerules/` contrôlés par version.

L'objectif de cette épopée est de doter **mLoop** d'une interopérabilité bilatérale complète avec Cline :
* Projeter l'état épistémique de mLoop (Stories, EvidencePacks, CONSTRAINTS) dans le format **Memory Bank** et **`.clinerules`**.
* Enrôler Cline comme runtime de travail de première classe dans notre Swarm Core via son mode **Agent Teams** et son garde-fou **Plan Mode**.

---

## 🧭 2. Vérité Terrain & Ancrage Normatif

> En application de l'**ADR-0375** (Traçabilité Radicale) et de l'**ADR-0376** (Zéro Blindspot), cette épopée s'ancre sur les sources vérifiées suivantes :

* **Source Aspiration Crawler** : `memory/crawler/cache/crawl_cline_bot_bb99da86024a.md` (llms.txt) et `memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md` (llms-full.txt, 707 Ko de documentation officielle Cline).
* **Spécification Officielle** : Documentation Cline CLI, Agent Teams SDK (`https://docs.cline.bot/cli/agent-teams`) et Memory Bank (`https://docs.cline.bot/best-practices/memory-bank`).
* **Dossier de Preuves Local** : `tests/test_worker_runtimes.py`, `src/core/herdr_worker_core.py`, `standards/adr-system/0377-runtimes-agents-aval-et-herdr-operationnels.md`.

---

## 🗂️ 3. Décomposition des Récits (Backlog Slicing)

L'épopée est découpée en 5 récits verticaux indépendants (INVEST) :

| Identifiant | Type | Titre | Scope & Valeur Produite | Macro-Taille |
| :--- | :---: | :--- | :--- | :---: |
| **`MLOOP-260-BE`** | Feature | **Bridge de Mémoire Bidirectionnel mLoop $\leftrightarrow$ Cline Memory Bank (`memory-bank/`)** | Projette le contexte actif de sprint et les EvidencePacks mLoop dans les fichiers `activeContext.md` et `progress.md` de Cline. | **M** |
| **`MLOOP-261-BE`** | Feature | **Génération Automatique de la Parité `.clinerules` depuis `CONSTRAINTS.md` & `AGENTS.md`** | Synchronise les garde-fous constitutionnels (interdictions de suppression, typage strict) dans `.clinerules/mloop.md`. | **S** |
| **`MLOOP-262-BE`** | Feature | **Intégration du Mode Plan/Act de Cline (`--plan`) avec les Gates de Cycle de Vie mLoop** | Force le démarrage de Cline en `--plan` (lecture seule) tant qu'une story n'est pas passée à `READY_FOR_DEV` (Phase 2 Grill-Me). | **M** |
| **`MLOOP-263-BE`** | Enabler | **Adaptateur Worker Cline Agent Teams (`--team-name`) pour Swarm Multitâches** | Permet à Herdr de déléguer des tâches à une escouade Cline coordonnée par taskboard, avec **Circuit-Breaker & Fallback Déterministe vers OpenCode** en cas d'anomalie. | **L** |
| **`MLOOP-264-FULL`** | Feature | **Commandes CLI `mloop cline-sync` & Harnais de Validation Pré-Vol Vibe-Check** | Ajoute les commandes d'orchestration CLI pour Cline et un contrôle de conformité automatisé dans `vibe-check`. | **M** |

---

## 🛡️ 4. Matrice d'Impact en 7 Couches (ADR-0376)

1. **Blueprints / Standards** : Alignement du modèle de mémoire mLoop avec le standard Memory Bank (ADR-0377 mis à jour).
2. **Protocols** : Formalisation du protocole de projection `memory-bank/` et du cycle Plan/Act.
3. **ADR System** : Référencement croisé avec ADR-0346 (Runtimes aval) et ADR-0375 (Traçabilité épistémique).
4. **Agents** : Capacité de déléguer à des coordinateurs Cline d'équipe (`Agent Teams`).
5. **Skills** : Accès transparent des compétences mLoop via les règles `.clinerules`.
6. **Code (`src/`)** : Création du package `src/bridges/cline/` (< 300L par module selon ADR-0202).
7. **Tests & Vibe-Check** : Couverture unitaire et intégration dans la suite `pytest tests/`.
