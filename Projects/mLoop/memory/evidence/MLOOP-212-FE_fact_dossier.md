---
story_id: MLOOP-212-FE
dossier_status: VALIDATED
created_at: 2026-09-24T00:00:00Z
updated_at: 2026-09-24T00:00:00Z
sources_hashes:
  source_adr_0387: (voir standards/adr-system/0387-mcp-modern-spec-2026-07-28-tasks-ui-elicitation-architecture.md)
  source_macro_adr_004: (voir Projects/mLoop/docs/01-architecture/ADR-004_epic-21-mcp-modern-suite_-_cadrage_macro_grill__6_decisions.md)
---

# 🐣 Dossier de Preuves Documentaires & Cadrage — `MLOOP-212-FE` (Extension MCP Apps `ui://`)

> **Titre Fonctionnel Pur** : Extension MCP Apps — Exposition `ui://` pour Archify Cockpit & DrawDB ERD  
> **Epic** : `EPIC-21-MCP-MODERN-SUITE`  
> **Couche** : `frontend`  
> **Dépendances** : `MLOOP-210-BE` (registre + fallback) · ADR-0387 Pilier 2

---

### 📂 1. Sources Physiques & Maquettes SSOT

| Source SSOT | Nature | Lien Repo Local (`file:///...`) |
| :--- | :--- | :--- |
| **Architecture / ADR** | Pilier 2, URIs `ui://`, sandbox | [ADR-0387 §Pilier2](file:///C:/Memory%20Loop/standards/adr-system/0387-mcp-modern-spec-2026-07-28-tasks-ui-elicitation-architecture.md) (L64-66) |
| **Code — DrawDB live** | Serveur HTTP 8081 + CSP | [tools/drawdb/runner.py](file:///C:/Memory%20Loop/tools/drawdb/runner.py) |
| **Code — Archify statique** | HTML standalone | [tools/archify/showcase/](file:///C:/Memory%20Loop/tools/archify/showcase/) · [routers/archify.py](file:///C:/Memory%20Loop/src/dashboard/routers/archify.py) |
| **Code — état projet** | `stateHandle` / `_SESSION_PROJECT` | [mcp_loop_mem.py](file:///C:/Memory%20Loop/src/bridges/mcp_loop_mem.py) (L174-176) |
| **Maquette** | N/A — iframe rendue par l'IDE hôte | N/A |

---

### ⚖️ 1.1 Matrice de Résolution des Conflits

| Conflit | Source A | Source B | Décision |
| :--- | :--- | :--- | :--- |
| Deux modèles de livraison (DrawDB live vs Archify statique) | Draft 212 (« payloads HTML auto-contenus » L40) | Code : DrawDB = sous-process HTTP | **Unification via pont** : proxy snapshot ou URL fallback selon 212-Q2 ; pas de double mode non tranché. |
| Synchro projet chat↔iframe | Draft 212 §5 (question ouverte) | `stateHandle` déjà codé | **postMessage + stateHandle** (212-Q1) ; zero nouvelle source de vérité. |
| Dimensions iframe = spec vs arbitrage | Draft 212 §5.2 (question PO) | Search-Before-Ask / macro Q5 | **Fact-quest 210**, pas PO (212-Q2) ; politique de repli actée. |

---

### 🎙️ 2. Extraits Verbatim Sourcés

> [!NOTE]
> **Extrait 1 — URIs officielles (ADR-0387)**  
> **Source** : [`0387...md#L65`](file:///C:/Memory%20Loop/standards/adr-system/0387-mcp-modern-spec-2026-07-28-tasks-ui-elicitation-architecture.md#L65)  
> *« Les visualisateurs Archify Cockpit et DrawDB ERD sont exposés sous forme de ressources ui://archify/cockpit et ui://drawdb/schema. »*  
> ➔ **Fait établi** : 2 ressources cibles (le draft 212 utilise un préfixe `mloop/` — divergence mineure à réaligner en build sur la spec).

> [!NOTE]
> **Extrait 2 — CSP souveraine DrawDB**  
> **Source** : [`tools/drawdb/runner.py#L60-L62`](file:///C:/Memory%20Loop/tools/drawdb/runner.py#L60-L62)  
> *« Content-Security-Policy: default-src 'self' 'unsafe-inline'; connect-src 'none' »*  
> ➔ **Fait établi** : l'iframe ne doit PAS appeler d'API réseau (valide 212-Q1 contre Option B).

> [!NOTE]
> **Extrait 3 — Repli URL promis**  
> **Source** : [`MLOOP-212-FE.md#L50`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-212-FE.md#L50)  
> *« Dégradation gracieuse : Si le client ne supporte pas l'extension UI, une URL locale HTTP est retournée comme solution de secours. »*  
> ➔ **Fait établi** : fallback déjà contractualisé → 212-Q2 l'étend au cas « iframe trop petite ».

> [!NOTE]
> **Extrait 4 — `stateHandle` existant**  
> **Source** : [`mcp_loop_mem.py#L174-L176`](file:///C:/Memory%20Loop/src/bridges/mcp_loop_mem.py#L174-L176)  
> *« _meta = params.get("_meta", {}) … if … _meta.get("stateHandle"): _SESSION_PROJECT = … »*  
> ➔ **Fait établi** : le canal d'état projet côté bridge existe — 212 ne le duplique pas.

---

### 🗄️ 3. Schéma de Données & Contrats UI (Matrice CTA)

| Déclencheur | État visuel iframe | Action / Feedback |
| :--- | :--- | :--- |
| `show_architecture` / `show_database_schema` OK | Ressource `ui://` rendue, zoom/pan actifs | — |
| `postMessage {project_changed}` | Mise à jour in-place (sans reload) | Conservation zoom/pan |
| Resize < `UI_MIN_WIDTH_PX` (320) | Bannière « ouvrir dans le navigateur » | Clic → URL localhost |
| Client sans extension `ui://` | — | Retour URL localhost (L50) |

---

### 🏁 5. Évaluation de la Frontière Active

#### [CAS B — Zéro Arbitrage Restant] ✅ Constat Formel de Frontière Vide
*Les 2 questions du §5 arbitrées (212-Q1 / 212-Q2).*  
👉 **Validation formelle du socle factuel avant conversion Palier 2.**

---

### 📎 Frontière active & Admission of Limits
- Contrat de livraison `ui://` (inline HTML vs URL) : **non vérifié** en spec externe (macro Q5).
- Dimensions IDE exactes : **fact-quest**, pas encore exécutée.
- Choix proxy-8081 vs snapshot HTML pour DrawDB live : **reste un point d'implémentation** à trancher en plan (2 options documentées, non arbitrées ici car dépendantes du contrat `ui://`).
