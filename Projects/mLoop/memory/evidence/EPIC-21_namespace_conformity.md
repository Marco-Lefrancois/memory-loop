# EPIC-21 — Falsification des espaces de noms MCP 2026-07-28

- **Épopée** : `EPIC-21-MCP-MODERN-SUITE` (MCP Modern Suite 2026Q4)
- **Récit porteur** : `MLOOP-210-BE` (Socle Protocolaire MCP 2026-07-28)
- **Décision cadrante** : ADR-004 / Q5 — *falsification externe des namespaces avant construction ; tout écart est consigné comme question ouverte **sans bloquer** le socle.*
- **Date de falsification** : 2026-09-24
- **Méthode** : recherche documentaire externe (spécification publique, dépôt GitHub `modelcontextprotocol/modelcontextprotocol`, SEPs) confrontée au récit SSOT interne — **porte de falsification poppérienne** : on cherche la *rupture* entre ce que la spec officielle exige et ce que le récit impose, jamais la confirmation.
- **Statut** : `OPEN_QUESTIONS_LOGGED` — 2 questions ouvertes consignées (`OQ-210-01`, `OQ-210-02`), aucune ne bloque la livraison du socle (cadrage macro ADR-004).

---

## 1. Sources externes consultées

| # | Source | URL (HTTPS) | Réf. |
| :-- | :--- | :--- | :--- |
| S1 | Specification MCP — version courante `2026-07-28` | https://modelcontextprotocol.io/specification/2026-07-28 | Spec |
| S2 | Versioning — négociation de version | https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning | Spec |
| S3 | Transports — Streamable HTTP | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http | Spec |
| S4 | **SEP-2243** — HTTP Header Standardization | https://modelcontextprotocol.io/seps/2243-http-standardization | SEP |
| S5 | Commit SEP-2243 (« Collapse `Mcp-Tool-Name`, `Mcp-Resource`, `Mcp-Prompt-Name` into `Mcp-Name` ») | https://github.com/modelcontextprotocol/modelcontextprotocol/commit/b51b39da764f148ad13b4bb27be6e51f2a8b209d | Commit |
| S6 | **SEP-2575** — code d'erreur dédié `UnsupportedProtocolVersionError` | https://github.com/modelcontextprotocol/modelcontextprotocol/commit/6d4a06f487275fa4607508d3fd58b98aa650cd06 | Commit |
| S7 | **SEP-2640** — Skills Extension (`io.modelcontextprotocol/skills`, **Status: Draft**) | https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2640 | SEP (PR ouverte) |
| S8 | Spec 2026-07-28 — élicitation (capacité **cœur** client) | https://modelcontextprotocol.io/specification/draft/client/elicitation | Spec |
| S9 | Spec 2025-11-25 — élicitation (`capabilities.elicitation`) | https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation | Spec |

**Sources internes confrontées (SSOT)** :
- [`MLOOP-210-BE.md` (Lignes 88-96)](file:///c:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-210-BE.md) — contrats d'échange & OQ-210-01.
- [`ADR-005_micro-grill_mloop-210-be__2_decisions.md` (Lignes 8-11)](file:///c:/Memory%20Loop/Projects/mLoop/docs/01-architecture/ADR-005_micro-grill_mloop-210-be__2_decisions.md) — registre d'en-têtes, inventaire transports.
- [`_mcp_protocol_core.py` (Lignes 23-56)](file:///c:/Memory%20Loop/src/bridges/_mcp_protocol_core.py) — registre unique, alias d'interop, `COVERED_BRIDGES`.

---

## 2. Matrice de conformité (claim externe vs récit vs code)

| # | Claim externe vérifié | Décision du récit SSOT | Verdict | Écart |
| :-- | :--- | :--- | :--- | :--- |
| C1 | Les en-têtes HTTP officiels sont `Mcp-Method` (toutes requêtes **et notifications**) et `Mcp-Name` (`tools/call`, `resources/read`, `prompts/get`) ; `Mcp-Tool-Name` a été **fusionné** dans `Mcp-Name` (S4, S5) | En-têtes `MCP-Protocol-Version`, `MCP-Method`, **`MCP-Tool-Name`** (conditionnel `tools/call`) | 🟡 Écart de nommage | **OQ-210-02** |
| C2 | Le serveur qui refuse une version **MUST** répondre `400 Bad Request` + `UnsupportedProtocolVersionError` listant les versions supportées (S2, S3) ; SEP-2575 introduit un code dédié (S6) | Refus **-32600** (`Invalid Request`) avec `data: {supported, requested}` | 🟡 Écart de code JSON-RPC, **statut HTTP aligné** (400) | **OQ-210-02** |
| C3 | Divergence en-tête/corps et en-tête requis manquant → `400` + erreur `-32001` / `HeaderMismatch` (S3, S4) | Toute divergence en-tête/corps = **non-conformité journalisée, jamais un rejet** (seule une version inconnue rejette) | 🟡 Écart volontaire (rétrocompatibilité non négociable) | **OQ-210-02** |
| C4 | La version par requête vit dans `_meta.io.modelcontextprotocol/protocolVersion` (+ en-tête `MCP-Protocol-Version` sur Streamable HTTP) (S1, S2) | `META_PROTOCOL_VERSION_KEY = "io.modelcontextprotocol/protocolVersion"` utilisé comme source **meta** de la version déclarée (priorité : en-tête → meta → params) | ✅ Conforme | — |
| C5 | `io.modelcontextprotocol/skills` — SEP-2640, **Status: Draft**, Extensions Track, PR #2640 toujours ouverte (S7) ; la spec 2026-07-28 présente *Skills over MCP* comme **extension** (S1) | Namespace de l'épopée traité comme extension **opt-in**, pas comme contrat cœur | ✅ Conforme (statut Draft reconnu) | — |
| C6 | L'élicitation est une **capacité cœur** du client : `capabilities.elicitation` (2025-11-25) / `_meta.io.modelcontextprotocol/clientCapabilities.elicitation` (draft) — **jamais** un identifiant `io.modelcontextprotocol/*` (S8, S9) | Élicitation classée capacité cœur, non namespace d'extension | ✅ Conforme | — |
| C7 | `io.modelcontextprotocol/tasks` (SEP-2663) et `io.modelcontextprotocol/ui` (MCP Apps) = extensions officielles identifiées (S1) | Namespaces reconnus par l'épopée (211-214) | ✅ Conforme | — |
| C8 | L'ADR-005 déclare « Transports HTTP : `mcp_sse_server`, `mcp_proxy_router` » ([ADR-005 (Ligne 8)](file:///c:/Memory%20Loop/Projects/mLoop/docs/01-architecture/ADR-005_micro-grill_mloop-210-be__2_decisions.md)) | Or `mcp_proxy_router.main()` et `mcp_resilience_guard.main()` lisent **`sys.stdin`** : ce sont des boucles **stdio** ; seul `mcp_sse_server` expose HTTP/SSE | 🔴 Écart d'inventaire interne | **OQ-210-01** |
| C9 | Aucune source externe ne certifie l'exhaustivité de l'inventaire des ponts mLoop exposés en réseau | Récit *Out-of-Scope* : « l'inventaire n'est pas clôturé … aucun pont supplémentaire n'est présumé couvert » | ✅ Frontière active assumée | **OQ-210-01** |

---

## 3. Questions ouvertes consignées

### OQ-210-01 — Inventaire des transports HTTP non clôturé
- **Constat (Niveau 1 : lexicale)** : `mcp_proxy_router.main()` (L203-208) et `mcp_resilience_guard.main()` (L172-174) consomment `sys.stdin` → boucles **stdio** ; `mcp_sse_server.run_server()` (L261-273) est le seul serveur uvicorn/HTTP du périmètre.
- **Conflit** : l'ADR-005 (Ligne 8) classe `mcp_proxy_router` parmi les « Transports HTTP ».
- **Décision** : aucune réécriture hors périmètre 210. Le routage par en-têtes a été appliqué **aux 4 ponts nommés par ADR-005** (`COVERED_BRIDGES`), avec la matrice de propriété du repli distinguant le transport réel (`http_sse` vs `stdio`) : l'application est correcte quel que soit le classement documentaire.
- **Impact** : purement documentaire ; à trancher avant le build de 211 (`inventory_close`).
- **Statut** : `OPEN` — ne bloque pas.

### OQ-210-02 — Conformité SEP-2243 (nommage, codes d'erreur, tolérance aux divergences)
Trois sous-écarts, tous tranchés **au profit du récit SSOT** (ADR-005 / 210-Q2) :

1. **Nom de l'en-tête d'outil** — la SEP-2243 impose `Mcp-Name` (fusion de `Mcp-Tool-Name`) (S4, S5) ; le récit impose `MCP-Tool-Name`.
   *Implémentation* : `MCP-Tool-Name` reste le nom canonique, `Mcp-Name` est accepté comme **alias d'interopérabilité** (`HEADER_TOOL_NAME_ALIAS`, [_mcp_protocol_core.py (Lignes 31-39)](file:///c:/Memory%20Loop/src/bridges/_mcp_protocol_core.py)). HTTP étant insensible à la casse, `MCP-Method` coïncide déjà avec `Mcp-Method`.
2. **Code d'erreur de version non supportée** — la spec impose `UnsupportedProtocolVersionError` (SEP-2575) avec HTTP 400 (S2, S3, S6) ; le récit impose `-32600`.
   *Implémentation* : `-32600` + `data.supported` / `data.requested` (SSOT récit) **et** statut HTTP `400` aligné sur la spec. Le passage au code dédié est réservé à 211 si le récit l'ouvre.
3. **Divergences en-tête/corps** — la spec exige `400` + `-32001` / `HeaderMismatch` (S3, S4) ; le récit interdit tout rejet hors version inconnue.
   *Implémentation* : non-conformités (`protocol_version_header_body_mismatch`, `method_header_body_mismatch`, `tool_name_out_of_scope`, …) **journalisées, jamais fatales** — conformément au critère « aucune requête portant une version connue ne peut échouer ».
- **Statut** : `OPEN` — ne bloque pas (ADR-004 Q5 : *écart → OQ sans bloquer*).

---

## 4. Audit épistémique

### `what_it_actually_proves`
- L'**existence et le statut** des artefacts externes cités : SEP-2243 (headers `Mcp-Method`/`Mcp-Name`, fusion de `Mcp-Tool-Name`), SEP-2575 (code dédié de version non supportée), SEP-2640 (**Draft**, `io.modelcontextprotocol/skills`), statut *extension* de `tasks`/`ui`, statut *capacité cœur* de l'élicitation — chacun vérifié sur son URL HTTPS officiel.
- La **détection de 2 écarts réels** (OQ-210-01 inventaire interne, OQ-210-02 conformité SEP-2243) — preuves Niveau 1 (lexicale/CLI) et Niveau 2 (arêtes de code : `sys.stdin` dans `main()`, `HEADER_TOOL_NAME_ALIAS`).
- Le **alignement** de l'implémentation sur le récit SSOT : registre unique, en-tête/meta/params, refus `-32600` réservé aux versions inconnues, HTTP 400, alias `Mcp-Name`, `COVERED_BRIDGES` = 4 ponts ADR-005.
- Que **aucun écart n'est masqué** : les 2 OQ sont portées dans l'EvidencePack du récit et dans ce dossier.

### `what_it_does_not_prove`
- **Ne prouve pas** que les 3 autres ponts de `COVERED_BRIDGES` soient effectivement exposés en HTTP : l'inventaire reste ouvert (OQ-210-01) et seuls `mcp_sse_server` (HTTP) et les boucles `sys.stdin` (stdio) ont été vérifiés lexicalement.
- **Ne prouve pas** la conformité d'interop opérationnelle avec un client MCP tiers conforme SEP-2243 (aucun client tiers exécuté — validation **Niveau 1/2**, pas Niveau 3 runtime).
- **Ne prouve pas** que `-32600` soit acceptable pour un client conforme à la spec 2026-07-28 : c'est un **choix délibéré du récit**, non une conformité démontrée (OQ-210-02).
- **Ne prouve pas** le statut définitif des SEP : SEP-2640 est *Draft* et son PR est ouvert — le statut peut changer après la date de falsification.
- **Ne couvre pas** les namespaces `211`-`214` (tasks, ui, skills, elicitation) au-delà de leur existence : leur implémentation n'est pas engagée par ce socle.

---

## 5. Décision de clôture

Le socle `MLOOP-210-BE` est livrable : les 2 écarts sont **consignés sans blocage** (cadrage ADR-004 Q5), l'implémentation suit strictement le récit SSOT, et la frontière active (`COVERED_BRIDGES`, inventaire ouvert) est testée par `tests/test_mcp_protocol_routage.py::TestFrontiereActivePonts`.
