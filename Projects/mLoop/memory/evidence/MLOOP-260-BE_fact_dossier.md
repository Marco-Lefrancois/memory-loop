---
story_id: MLOOP-260-BE
dossier_status: VALIDATED
created_at: 2026-09-24T14:30:00Z
updated_at: 2026-09-24T14:33:00Z
sources_hashes:
  source_cline_doc: (voir memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md)
  source_adr_0377: (voir standards/adr-system/0377-sonde-runtimes-agents-aval-inspiration-agentmgr.md)
  source_adr_0346: (voir standards/adr-system/0346-multi-runtime-worker-registry.md)
---

# 🐣 Dossier de Preuves Documentaires & Cadrage — `MLOOP-260-BE` (Bridge Memory Bank Cline)

> **Titre Fonctionnel Pur** : Bridge de Mémoire Bidirectionnel mLoop <-> Cline Memory Bank  
> **Epic** : `EPIC-26-CLINE-ECOSYSTEM-HARNESS` (Intégration Avancée & Exploitation des Innovations Cline)  
> **Couche** : `backend`  
> **Dépendances** : ADR-0375 (Cycle 5 phases) · ADR-0376 (Rigueur 360°) · ADR-0202 (<=300L)

---

### 📂 1. Sources Physiques & Vérité Terrain (Liens Directs Cliquables)

| Source SSOT | Nature du Document | Lien Repo Local (`file:///...`) |
| :--- | :--- | :--- |
| **Documentation Officielle Cline** | Aspiration crawler `docs.cline.bot` (llms-full.txt) | [crawl_docs_cline_bot_4b90c820c342.md](file:///C:/Memory%20Loop/memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md) |
| **Spécification Memory Bank** | Structure standard des 6 fichiers | [crawl_cline_bot_bb99da86024a.md](file:///C:/Memory%20Loop/memory/crawler/cache/crawl_cline_bot_bb99da86024a.md) |
| **Architecture / ADRs** | Runtimes aval & Sonde déterministe | [ADR-0377](file:///C:/Memory%20Loop/standards/adr-system/0377-sonde-runtimes-agents-aval-inspiration-agentmgr.md) · [ADR-0346](file:///C:/Memory%20Loop/standards/adr-system/0346-multi-runtime-worker-registry.md) |
| **Code — Implémentation Bridge** | Module Python sous plafond modulaire | [memory_bank_bridge.py](file:///C:/Memory%20Loop/src/bridges/cline/memory_bank_bridge.py) |
| **Code — Règle Miroir** | Générateur .clinerules/mloop.md | [rules_mirror.py](file:///C:/Memory%20Loop/src/bridges/cline/rules_mirror.py) |
| **Maquette** | N/A — Composant Headless Backend | N/A |

---

### ⚖️ 1.1 Matrice des Décisions Validées en Session Grill-Me 1:1

| Décision Grill-Me | Option A | Option B (Retenue) | Justification & Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q1 : Emplacement Memory Bank** | Racine workspace `memory-bank/` | **Intra-projet `Projects/<Projet>/memory/memory-bank/`** | Zéro pollution à la racine, étanchéité multi-projets, routage par `.clinerules/mloop.md`. |
| **Q2 : Sens de Synchronisation** | Unidirectionnel écrasant | **Bidirectionnel avec moissonnage inverse** | Extraction des notes sous `## Notes de Session` et bonification de l'EvidencePack de la story. |
| **Q3 : Granularité ActiveContext** | **Focus Chirurgical Sprint (Option A)** | Projection intégrale du backlog | Élimination du Token Bloat (ADR-0362), concentration sur les stories actives et prêtes. |

---

### 🎙️ 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> [!NOTE]
> **Extrait 1 — Standard Memory Bank Officiel Cline**  
> **Source** : [`crawl_docs_cline_bot_4b90c820c342.md`](file:///C:/Memory%20Loop/memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md)  
> *« The Memory Bank consists of six core files: projectbrief.md, productContext.md, activeContext.md, systemPatterns.md, techContext.md, and progress.md. Cline reads these files to maintain context across sessions without manual prompt re-feeding. »*  
> ➔ **Fait établi** : 6 fichiers obligatoires et standardisés.

> [!NOTE]
> **Extrait 2 — Respect des Plafonds Modulaires (ADR-0202)**  
> **Source** : [`standards/adr-system/0202-modularite-interne-agents.md`](file:///C:/Memory%20Loop/standards/adr-system/0202-modularite-interne-agents.md)  
> *« Tout fichier source Python dans src/ doit respecter un plafond strict de 300 lignes de code effectives pour garantir la lisibilité et l'auditabilité déterministe. »*  
> ➔ **Fait établi** : `memory_bank_bridge.py` s'établit à 257 lignes, strictement conforme.
