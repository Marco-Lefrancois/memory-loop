---
story_id: MLOOP-263-BE
dossier_status: VALIDATED
created_at: 2026-09-24T14:45:00Z
updated_at: 2026-09-24T14:45:00Z
sources_hashes:
  source_cline_doc: (voir memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md)
  source_adr_0346: (voir standards/adr-system/0346-multi-runtime-worker-registry.md)
  source_adr_0377: (voir standards/adr-system/0377-sonde-runtimes-agents-aval-inspiration-agentmgr.md)
---

# 🐣 Dossier de Preuves Documentaires & Cadrage — `MLOOP-263-BE` (Adaptateur Cline Agent Teams)

> **Titre Fonctionnel Pur** : Adaptateur Worker Cline Agent Teams (`--team-name`) pour Swarm Multitâches  
> **Epic** : `EPIC-26-CLINE-ECOSYSTEM-HARNESS` (Intégration Avancée & Exploitation des Innovations Cline)  
> **Couche** : `backend`  
> **Dépendances** : ADR-0346 (Multi-runtime) · ADR-0377 (Runtimes aval) · ADR-0202 (<=300L)

---

### 📂 1. Sources Physiques & Vérité Terrain (Liens Directs Cliquables)

| Source SSOT | Nature du Document | Lien Repo Local (`file:///...`) |
| :--- | :--- | :--- |
| **Documentation Officielle Cline** | Aspiration crawler `docs.cline.bot` (Agent Teams) | [crawl_docs_cline_bot_4b90c820c342.md](file:///C:/Memory%20Loop/memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md) |
| **Multi-Runtime Worker Registry** | Registre des workers Swarm | [ADR-0346](file:///C:/Memory%20Loop/standards/adr-system/0346-multi-runtime-worker-registry.md) |
| **Sonde Runtimes d'Agents Aval** | Détection et gestion des shims CLI | [ADR-0377](file:///C:/Memory%20Loop/standards/adr-system/0377-sonde-runtimes-agents-aval-inspiration-agentmgr.md) |
| **Code — Implémentation Circuit-Breaker** | Repli déterministe vers OpenCode | [herdr_worker_core.py](file:///C:/Memory%20Loop/src/core/herdr_worker_core.py) |
| **Revue Sentinel Rubber Duck** | Rapport d'audit sémantique (100/100) | [rubber_duck_MLOOP-263-BE.md](file:///C:/Memory%20Loop/backlog/reviews/rubber_duck_MLOOP-263-BE.md) |

---

### ⚖️ 1.1 Matrice des Décisions Validées en Session Grill-Me 1:1

| Décision Grill-Me | Option A (Retenue) | Option B | Justification & Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q1 : Plafond de Sous-Agents** | **Plafond strict à 3 sous-agents** | Quota budgétaire sans plafond rigide | Évite toute prolifération incontrôlée de tokens ou boucles récursives ; contrôlé par Herdr et `.clinerules/mloop.md`. |
| **Q2 : Rétention Dossiers d'Équipes** | **Moissonnage EvidencePack puis purge propre** | Conservation disque sans purge | Assure l'auditabilité légale centralisée dans `memory/evidence/` et maintient une hygiène disque parfaite sous `~/.cline/data/teams/`. |

---

### 🎙️ 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> [!NOTE]
> **Extrait 1 — Documentation Officielle Cline sur Agent Teams**  
> **Source** : [`crawl_docs_cline_bot_4b90c820c342.md`](file:///C:/Memory%20Loop/memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md)  
> *« Agent Teams coordinate multiple instances through a shared task board and inter-agent mailbox under ~/.cline/data/teams/. A lead agent delegates sub-tasks to teammate instances based on their specialized instructions. »*  
> ➔ **Fait établi** : Mécanique officielle de coordination inter-agents via `--team-name`.

> [!NOTE]
> **Extrait 2 — Registre Multi-Runtime et Circuit-Breaker (ADR-0346 & ADR-0377)**  
> **Source** : [`standards/adr-system/0346-multi-runtime-worker-registry.md`](file:///C:/Memory%20Loop/standards/adr-system/0346-multi-runtime-worker-registry.md)  
> *« Tout runtime externe doit être encadré par un disjoncteur (Circuit-Breaker) capable de basculer de manière transparente et déterministe vers le runtime de référence par défaut (OpenCode) sans suspendre l'ordonnanceur d'équipe. »*  
> ➔ **Fait établi** : Le Circuit-Breaker déterministe vers OpenCode (`opencode --yolo`) est obligatoire.
