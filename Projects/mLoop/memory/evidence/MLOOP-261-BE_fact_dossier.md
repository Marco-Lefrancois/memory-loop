---
story_id: MLOOP-261-BE
dossier_status: VALIDATED
created_at: 2026-09-24T14:35:00Z
updated_at: 2026-09-24T14:39:00Z
sources_hashes:
  source_cline_rules_doc: (voir memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md)
  source_adr_0376: (voir standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md)
  source_adr_0202: (voir standards/adr-system/0202-modularite-interne-agents.md)
---

# 🐣 Dossier de Preuves Documentaires & Cadrage — `MLOOP-261-BE` (Parité .clinerules)

> **Titre Fonctionnel Pur** : Génération Automatique de la Parité .clinerules depuis CONSTRAINTS.md & AGENTS.md  
> **Epic** : `EPIC-26-CLINE-ECOSYSTEM-HARNESS` (Intégration Avancée & Exploitation des Innovations Cline)  
> **Couche** : `backend`  
> **Dépendances** : ADR-0376 (Rigueur 360°) · ADR-0202 (<=300L) · ADR-0375 (Cycle 5 phases)

---

### 📂 1. Sources Physiques & Vérité Terrain (Liens Directs Cliquables)

| Source SSOT | Nature du Document | Lien Repo Local (`file:///...`) |
| :--- | :--- | :--- |
| **Documentation Officielle Cline** | Support de `.clinerules/*.md` | [crawl_docs_cline_bot_4b90c820c342.md](file:///C:/Memory%20Loop/memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md) |
| **Règles Constitutionnelles mLoop** | Directives suprêmes d'ingénierie | [AGENTS.md](file:///C:/Memory%20Loop/AGENTS.md) · [ecosystem_rigor_zero_blindspot.md](file:///C:/Memory%20Loop/.agents/rules/ecosystem_rigor_zero_blindspot.md) |
| **Code — Module Règles Miroir** | Générateur déterministe modulaire | [rules_mirror.py](file:///C:/Memory%20Loop/src/bridges/cline/rules_mirror.py) |
| **Code — Pipeline Vibe-Check** | Contrôle pré-vol de parité | [_vc_agents.py](file:///C:/Memory%20Loop/src/pipelines/vibe_check/_vc_agents.py) |
| **Maquette** | N/A — Composant Headless Backend | N/A |

---

### ⚖️ 1.1 Matrice des Décisions Validées en Session Grill-Me 1:1

| Décision Grill-Me | Option A (Retenue) | Option B | Justification & Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q1 : Format de Règle** | **Modulaire `.clinerules/mloop.md`** | Monolithique `.clinerules` | Préserve les règles personnelles de l'utilisateur sans écrasement au `sync`. |
| **Q2 : Contrôle Vibe-Check** | **Contrôle Actif dans Vibe-Check** | Génération passive sans contrôle | Garantie qu'aucune session Cline n'opère sans ses garde-fous constitutionnels. |

---

### 🎙️ 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> [!NOTE]
> **Extrait 1 — Spécification Modulaire `.clinerules/` de Cline**  
> **Source** : [`crawl_docs_cline_bot_4b90c820c342.md`](file:///C:/Memory%20Loop/memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md)  
> *« Instructions can be defined at the workspace level in .clinerules/ directory. Each .md file in this directory is concatenated and injected into the prompt. »*  
> ➔ **Fait établi** : L'utilisation de fichiers modulaires `.clinerules/*.md` est la norme officielle moderne de Cline.

> [!NOTE]
> **Extrait 2 — Rigueur 360° et Triangulation Normative (ADR-0376)**  
> **Source** : [`standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md`](file:///C:/Memory%20Loop/standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md)  
> *« Les contraintes doivent être inviolables par leur présence simultanée dans les points d'entrée des LLMs : AGENTS.md, .agents/rules/, et règles spécifiques aux environnements tiers. »*  
> ➔ **Fait établi** : `.clinerules/mloop.md` constitue le point d'ancrage obligatoire pour le runtime Cline.
