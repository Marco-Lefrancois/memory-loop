---
story_id: MLOOP-264-FULL
dossier_status: VALIDATED
created_at: 2026-09-24T14:47:00Z
updated_at: 2026-09-24T14:47:00Z
sources_hashes:
  source_cline_doc: (voir memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md)
  source_adr_0370: (voir standards/adr-system/0370-standard-documentation-cli-ssot.md)
  source_adr_0377: (voir standards/adr-system/0377-sonde-runtimes-agents-aval-inspiration-agentmgr.md)
---

# 🐣 Dossier de Preuves Documentaires & Cadrage — `MLOOP-264-FULL` (Harnais CLI & Vibe-Check Cline)

> **Titre Fonctionnel Pur** : Commandes CLI mLoop `cline-sync` & Harnais de Validation Pré-Vol Vibe-Check  
> **Epic** : `EPIC-26-CLINE-ECOSYSTEM-HARNESS` (Intégration Avancée & Exploitation des Innovations Cline)  
> **Couche** : `backend`  
> **Dépendances** : ADR-0370 (SSOT CLI) · ADR-0377 (Runtimes aval) · ADR-0202 (<=300L)

---

### 📂 1. Sources Physiques & Vérité Terrain (Liens Directs Cliquables)

| Source SSOT | Nature du Document | Lien Repo Local (`file:///...`) |
| :--- | :--- | :--- |
| **Documentation Officielle Cline** | Aspiration crawler `docs.cline.bot` (MCP & Settings) | [crawl_docs_cline_bot_4b90c820c342.md](file:///C:/Memory%20Loop/memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md) |
| **Standard Guide CLI SSOT** | Enregistrement déclaratif des commandes CLI | [ADR-0370](file:///C:/Memory%20Loop/standards/adr-system/0370-standard-documentation-cli-ssot.md) |
| **Sonde Runtimes d'Agents Aval** | Détection déterministe et diagnostic santé | [ADR-0377](file:///C:/Memory%20Loop/standards/adr-system/0377-sonde-runtimes-agents-aval-inspiration-agentmgr.md) |
| **Code — Implémentation Vibe-Check** | Règle 24 avec auto-guérison | [_vc_agents.py](file:///C:/Memory%20Loop/src/pipelines/vibe_check/_vc_agents.py) |
| **Revue Sentinel Rubber Duck** | Rapport d'audit sémantique (95.8/100) | [rubber_duck_MLOOP-264-FULL.md](file:///C:/Memory%20Loop/backlog/reviews/rubber_duck_MLOOP-264-FULL.md) |

---

### ⚖️ 1.1 Matrice des Décisions Validées en Session Grill-Me 1:1

| Décision Grill-Me | Option A (Retenue) | Option B | Justification & Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q1 : Politique d'Auto-Remédiation** | **Auto-guérison transparente déterministe** | Mode informatif strict sans correction | Réduit à zéro la friction de maintenance manuelle des fichiers miroirs (`.clinerules/mloop.md` et Memory Bank). |
| **Q2 : Parité des Serveurs MCP** | **Support parité MCP complète** | Périmètre restreint sans export MCP | Permet à Cline d'utiliser immédiatement l'outillage mLoop (fact-search, graphify, etc.) via `cline_mcp_settings.json`. |

---

### 🎙️ 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> [!NOTE]
> **Extrait 1 — Documentation Officielle Cline sur les Serveurs MCP**  
> **Source** : [`crawl_docs_cline_bot_4b90c820c342.md`](file:///C:/Memory%20Loop/memory/crawler/cache/crawl_docs_cline_bot_4b90c820c342.md)  
> *« Cline reads MCP server configurations from cline_mcp_settings.json in its application data directory. Each server specifies command, args, and optional environment variables to expose tools to the agent. »*  
> ➔ **Fait établi** : Format standardisé pour exporter l'outillage MCP de mLoop vers Cline.

> [!NOTE]
> **Extrait 2 — Standard de Documentation CLI SSOT (ADR-0370)**  
> **Source** : [`standards/adr-system/0370-standard-documentation-cli-ssot.md`](file:///C:/Memory%20Loop/standards/adr-system/0370-standard-documentation-cli-ssot.md)  
> *« Toute nouvelle commande introduite dans l'interface CLI de mLoop doit être déclarée dans le registre central, couverte par un test in-process CliRunner et synchronisée avec le guide canonique. »*  
> ➔ **Fait établi** : L'introduction de `cline-sync` s'aligne rigoureusement sur le moteur Click existant.
