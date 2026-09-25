---
story_id: MLOOP-262-BE
dossier_status: VALIDATED
created_at: 2026-09-24T14:43:00Z
updated_at: 2026-09-24T14:43:00Z
sources_hashes:
  source_cline_doc: (voir memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md)
  source_adr_0375: (voir standards/adr-system/0375-project-lifecycle-5-phases-and-analysis-types.md)
  source_adr_0376: (voir standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md)
---

# 🐣 Dossier de Preuves Documentaires & Cadrage — `MLOOP-262-BE` (Verrou Plan Mode Strict)

> **Titre Fonctionnel Pur** : Verrouillage Déterministe du Plan Mode Cline en Phase 2 de Cadrage  
> **Epic** : `EPIC-26-CLINE-ECOSYSTEM-HARNESS` (Intégration Avancée & Exploitation des Innovations Cline)  
> **Couche** : `backend`  
> **Dépendances** : ADR-0375 (Cycle 5 phases) · ADR-0376 (Rigueur 360°) · ADR-0202 (<=300L)

---

### 📂 1. Sources Physiques & Vérité Terrain (Liens Directs Cliquables)

| Source SSOT | Nature du Document | Lien Repo Local (`file:///...`) |
| :--- | :--- | :--- |
| **Documentation Officielle Cline** | Aspiration crawler `docs.cline.bot` (Plan/Act modes) | [crawl_docs_cline_bot_4b90c820c342.md](file:///C:/Memory%20Loop/memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md) |
| **Cycle de Vie 5 Phases** | Spécification Phase 2 vs Phase 3 | [ADR-0375](file:///C:/Memory%20Loop/standards/adr-system/0375-project-lifecycle-5-phases-and-analysis-types.md) |
| **Rigueur Zéro Blindspot** | Inviolabilité de la DoR et Fail-Closed | [ADR-0376](file:///C:/Memory%20Loop/standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md) |
| **Code — Implémentation Worker** | Injection déterministe `--plan` | [herdr_worker_core.py](file:///C:/Memory%20Loop/src/core/herdr_worker_core.py) |
| **Revue Sentinel Rubber Duck** | Rapport d'audit sémantique (87.4/100) | [rubber_duck_MLOOP-262-BE.md](file:///C:/Memory%20Loop/backlog/reviews/rubber_duck_MLOOP-262-BE.md) |

---

### ⚖️ 1.1 Matrice des Décisions Validées en Session Grill-Me 1:1

| Décision Grill-Me | Option A (Retenue) | Option B | Justification & Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q1 : Gate de Déverrouillage Act Mode** | **Validation DoR 6/6 + Palier 2 exigés** | Avertissement permissif (warning) | Principe Fail-Closed (ADR-0376) : aucun code ne doit être généré avant que la DoR ne soit certifiée à 100%. |
| **Q2 : Comportement en cas de Violation** | **Interruption immédiate & message pédagogique** | Bascule silencieuse vers OpenCode | Transparence totale pour le développeur ; guidage explicite vers `swarm grill-me` pour lever les ambiguïtés. |

---

### 🎙️ 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> [!NOTE]
> **Extrait 1 — Documentation Officielle Cline sur le Plan Mode**  
> **Source** : [`crawl_docs_cline_bot_4b90c820c342.md`](file:///C:/Memory%20Loop/memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md)  
> *« In Plan Mode, Cline focuses on understanding requirements, researching the codebase, and designing the implementation strategy without executing changes to disk or running shell commands that mutate system state. »*  
> ➔ **Fait établi** : Le mode `--plan` garantit l'immuabilité du code source pendant les phases d'exploration et de cadrage.

> [!NOTE]
> **Extrait 2 — Standard de Rigueur Zéro Blindspot (ADR-0376)**  
> **Source** : [`standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md`](file:///C:/Memory%20Loop/standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md)  
> *« Tout passage en Phase 3 (Build/Act) requiert un état strictement READY_FOR_DEV avec une Definition of Ready validée à 6/6. Tout manquement déclenche un refus fail-closed. »*  
> ➔ **Fait établi** : L'injection automatique de `--plan` pour `task_type in ("plan", "grill", "analyse")` formalise cette règle au niveau de l'orchestration Herdr.
