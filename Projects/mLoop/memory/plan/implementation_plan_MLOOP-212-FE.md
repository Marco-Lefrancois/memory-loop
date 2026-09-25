---
id: PLAN-212-FE
story_id: MLOOP-212-FE
status: COMPLETED # DRAFT | APPROVED | EXECUTING | COMPLETED
harness: opencode
created_at: 2026-09-24
---

# Extension MCP Apps — Exposition `ui://` pour Archify Cockpit & DrawDB ERD

> **Objectif** : exposer les deux visualisations mLoop (cockpit d'architecture Archify, schéma relationnel DrawDB) comme ressources `ui://` conformes à l'extension officielle **`io.modelcontextprotocol/ui`** (SEP-1865, MCP Apps 2026-01-26), rendues en iframe sandboxé dans l'IDE via les outils `show_architecture` / `show_database_schema`, avec source de vérité unique du projet actif, cadre 100% lecture-seule, isolation réseau stricte (`connect-src 'none'`) et politique de repli contractualisée (`UI_MIN_WIDTH_PX = 320` + adresse locale).

---

## 1. User Review Required (Arbitrages & Points Clés)

> [!IMPORTANT]
> **Décisions structurantes (feu vert humain déjà acté sur le récit — session Grill EPIC-21 2026-09-24, `grill_me: DONE`, statut `IN_DEV`) :**
> - **Contrat de livraison `ui://` (OQ-212-01) tranché par fact-quest externe** : SEP-1865 officielle (`modelcontextprotocol/ext-apps`, spec 2026-01-26) — ressource **pré-déclarée** `ui://` + référence **`_meta.ui.resourceUri`** sur la définition d'outil + livraison du HTML via **`resources/read`** (l'inline-embed et le `resource_link` en résultat d'outil ont été *rejetés* par la spec). L'outil retourne **toujours** un contenu texte significatif ; le texte inclut l'adresse locale de secours quand l'extension n'est pas négociée.
> - **Rendu DrawDB (OQ-212-02) tranché** : **instantané HTML autonome** généré par `tools/drawdb/_page.py::render_schema_page` (zéro CDN, `connect-src 'none'` natif) plutôt que proxy vers le serveur 8081 — un proxy est impossible en interior du cadre (CSP refusée). Le serveur `8081` reste l'**adresse locale de repli** (bannière / hôte sans extension).
> - **Détecteur de capacité strict** : l'extension compte uniquement si le client déclare `capabilities.extensions["io.modelcontextprotocol/ui"].mimeTypes` contenant `text/html;profile=mcp-app` (champ *REQUIRED* de la spec — « a client that omits it does not count »). Sans négociation → dégradation gracieuse, jamais d'échec d'appel.
> - **Nettoyage CDN imposé** : l'artefact `tools/archify/showcase/*.architecture.html` contient malgré son README **3 balises `<link>` vers Google Fonts** — le pont les supprime au service (In-Scope L38 : « zéro dépendance à un CDN externe »).
> - **Plafonds ADR-0202** : `mcp_loop_mem.py` passe de 292 → 296 lignes (≤300) ; chaque module livré reste ≤300 L / 15 Ko.

---

## 2. Questions Ouvertes (Open Questions)

> [!NOTE]
> - **OQ-212-01** : *contrat exact de livraison `ui://`* $\rightarrow$ **RÉSOLU** (SEP-1865 officielle, voir §1). Traçabilité : `memory/evidence/MLOOP-212-FE_evidence.json` → `open_questions`.
> - **OQ-212-02** : *passerelle 8081 vs instantané HTML autonome pour DrawDB* $\rightarrow$ **RÉSOLU : instantané autonome** (voir §1).
> - **Forme des réglages serveur de `capabilities.extensions`** : la SEP-1865 documente le shape **client** (`mimeTypes` REQUIRED) ; le côté serveur est documenté par le SDK (« advertise under capabilities.extensions ») sans settings figés $\rightarrow$ *choix d'implémentation : symétrie `{"mimeTypes": ["text/html;profile=mcp-app"]}` (revoyable sans changement de contrat — registre unique `ui_server_capabilities()`).*
> - **Dimensions nominales iframe OpenCode/Antigravity** : batchées avec la conformité du socle en amont (tâche 210, macro Q5) — délégation actée en micro-grill 212-Q2, aucune question triviale posée à l'humain.

---

## 3. Modifications Proposées (Proposed Changes)

### Pont MCP Apps (nouveau)

- #### `[NEW]` [`src/bridges/mcp_ui.py`](file:///c:/Memory%20Loop/src/bridges/mcp_ui.py)
  - **Intention** : registre partagé (`UI_EXTENSION_ID`, `UI_APP_MIME_TYPE`, `UI_MIN_WIDTH_PX = 320`, les 2 adresses officielles), négociation de capacité (`note_client_capabilities` / `client_supports_ui` / `ui_server_capabilities`), `list_ui_resources`, `read_ui_resource` (refus des adresses hors registre), `attach_ui_meta` (tools/list), `ui_result` (tools/call : texte significatif + `_meta.ui.resourceUri` ou repli local journalisé), `notify_ui_project_changed` (SSE `notifications/resources/updated`).
  - **Impact** : nouveau pont ~230 L ; importé par `mcp_loop_mem`, `mcp_tools`, `mcp_resources`.

- #### `[NEW]` [`src/bridges/_mcp_ui_shell.py`](file:///c:/Memory%20Loop/src/bridges/_mcp_ui_shell.py)
  - **Intention** : génération du HTML servi — chargement artefact (Archify showcase avec **strip des CDN** ; DrawDB via `render_schema_page`), injection en-tête **CSP meta stricte** (`default-src 'none' … connect-src 'none'`), injection de la **coquille** : bannière « ouvrir dans le navigateur » (états Default/Hover/Focus-Visible/Active), badge projet, récepteur `project_changed` (mise à jour **en place**, garde `event.source === parent`, zéro `location.reload`), zoom/déplacement (molette + glissé) sur le schéma relationnel, handshake léger `ui/initialize`/`ui/notifications/initialized`, `ui/notifications/size-changed`, activation bannière sous 320 px journalisée (`console.info`).
  - **Impact** : module dédié ≤300 L (découpage ADR-0202, pattern `_page.py` du drawdb).

### Ponts Tier A (périmètre ADR-005 — modifications minimales)

- #### `[MODIFY]` [`src/bridges/mcp_loop_mem.py`](file:///c:/Memory%20Loop/src/bridges/mcp_loop_mem.py)
  - **Intention** : `handle_initialize` capture `params.capabilities` → `note_client_capabilities(...)` ; `capabilities.extensions` = `ui_server_capabilities()` (dans `handle_initialize` **et** `handle_server_discover`, parité anti-dérive).
  - **Impact** : +4 lignes → 296 L (plafond 300 respecté).

- #### `[MODIFY]` [`src/bridges/mcp_tools.py`](file:///c:/Memory%20Loop/src/bridges/mcp_tools.py)
  - **Intention** : définitions `show_architecture` / `show_database_schema` (phase PLAN, inputSchema `project?`), dispatch → `ui_result` (résultat complet, jamais `isError`), `attach_ui_meta(tools)` sur `tools/list`, notification `notify_ui_project_changed` à `loop_mem_set_project`.
  - **Impact** : +~12 L → ~245 L.

- #### `[MODIFY]` [`src/bridges/mcp_resources.py`](file:///c:/Memory%20Loop/src/bridges/mcp_resources.py)
  - **Intention** : hook `ui://` sur `resources/list` (2 ressources déclarées, `mimeType: text/html;profile=mcp-app`, `_meta.ui.csp` à connexions vides) et `resources/read` (livraison HTML + paramètre `?project=` vs état du pont).
  - **Impact** : +~8 L → ~194 L.

### Tests & preuves

- #### `[NEW]` [`tests/test_mcp_ui_apps.py`](file:///c:/Memory%20Loop/tests/test_mcp_ui_apps.py)
  - **Intention** : couverture des **7 scénarios Gherkin** du récit (nominal, sans-support, adresse hors registre, bannière 320 px, isolement réseau, mise à jour en place, états/tracabilité) + négociation de capacité (absente / conforme / mimeTypes incorrect) + annonce serveur `capabilities.extensions` + notification SSE de changement de projet.

- #### `[MODIFY]` [`Projects/mLoop/memory/evidence/MLOOP-212-FE_evidence.json`](file:///c:/Memory%20Loop/Projects/mLoop/memory/evidence/MLOOP-212-FE_evidence.json)
  - **Intention** : `implementation_decisions` (OQ-212-01/02), `external_references` (SEP-1865), `verification_harness` réellement exécuté, `test_results`, `deliverables`, `admission_of_limits`.

> **Aucun fichier hors périmètre 212 modifié.** `backlog/stories/MLOOP-212-FE.md` et `sprint_backlog.md` ne sont **pas** touchés (prérogatives orchestrateur ; arrêt strict après `## Scénarios de test`, zéro note IA).

---

## 4. Gestion des Risques & Rollback

| Risque Identifié | Impact Potentiel | Stratégie d'Atténuation / Rollback |
| :--- | :--- | :--- |
| **Régression `mcp_loop_mem` (292→296 L, cœur de session)** | Élevé | Ajouts purement déclaratifs (+4 L) ; suites `test_mcp_loop_mem`, `test_mcp_sse_transport`, `test_mcp_protocol_*` avant/après ; rollback = `git checkout -- src/bridges/mcp_loop_mem.py`. |
| **Casse `tools/list` (outils existants / filtres de phase)** | Moyen | Outils en phase `PLAN` avec dispatch indépendant ; `test_google_mcp_toolbox_alignment` + `test_mcp_loop_mem` non-régression ; `_meta.ui` conditionnel (sans capacité → comportement identique à l'avant). |
| **HTML Archify dégradé par le strip CDN / CSP stricte** | Moyen | Strip limité aux balises `link/script/@import` externe ; la page est autonome (README showcase + vérif `requestAnimationFrame` conservé) ; test `no external asset` + `connect-src 'none'` au service. |
| **Conflit de zoom (shell vs navigation interne Archify)** | Moyen | Zoom shell **opt-in** (`zoomTarget`) activé uniquement pour DrawDB ; Archify garde son pan/zoom natif (« dependency-free pan/zoom » du showcase). |
| **Dépassement plafond 300 L (ADR-0202 / RULE-AST-01)** | Moyen | Découpage `mcp_ui` + `_mcp_ui_shell` ; `code-check --file` sur chaque livrable avant clôture. |

---

## 5. Plan de Vérification & Recette (Triple Gate)

### A. Tests Automatisés

- [x] Commande(s) de test / linting exécutées (41 + 63 tests verts, code-check 5/5, struct-check Conforme) :
  ```powershell
  # 1. Scenarios Gherkin du recit (nouveau harnais)
  python -m pytest tests/test_mcp_ui_apps.py -q -p no:cacheprovider

  # 2. Non-regression MCP (ponts touches)
  python -m pytest tests/test_mcp_loop_mem.py tests/test_mcp_sse_transport.py `
    tests/test_mcp_protocol_socle.py tests/test_mcp_protocol_routage.py `
    tests/test_mcp_resilience_guard.py tests/test_google_mcp_toolbox_alignment.py `
    -q -p no:cacheprovider

  # 3. Standards de robustesse (ADR-0202 : 300 L / 15 Ko)
  python src/swarm.py code-check --file src/bridges/mcp_ui.py
  python src/swarm.py code-check --file src/bridges/_mcp_ui_shell.py
  python src/swarm.py code-check --file src/bridges/mcp_loop_mem.py
  python src/swarm.py code-check --file src/bridges/mcp_tools.py
  python src/swarm.py code-check --file src/bridges/mcp_resources.py

  # 4. Gate C12 (Domain Sanity) sur le recit
  python src/swarm.py struct-check --project mLoop --file Projects/mLoop/backlog/stories/MLOOP-212-FE.md
  ```

- [x] **Checklist FRAMEWORK_STATE (ADR-0352)** :
  1. **Status source vérifié** : frontmatter lu ce jour → `status: IN_DEV`, `grill_me: DONE`, `invest_score: 6/6`, `blocked_by: [MLOOP-210-BE]` (livré `DONE_TESTED` le 2026-09-24).
  2. **Certificat NLI daté** : `struct-check` exécuté le 2026-09-24, postérieur au dernier commit framework → non obsolète.
  3. **`struct-check` inclus dans §5A** : ✅ commande + résultat *Conforme*.
  4. **`verification_harness` non vide** : ✅ 7 scénarios renseignés (tableau §5D).
  5. **Transition d'état valide** : `IN_DEV` (état courant) — toute bascule `→ DONE_TESTED` est **à la charge de l'orchestrateur**.

### B. Vérifications Manuelles & Scénarios Clés

- [x] **Scénario Nominal** : `tools/list` (client doté de la capacité) publie `_meta.ui.resourceUri` = `ui://archify/cockpit` / `ui://drawdb/schema` ; `resources/read` livre un HTML5 auto-contenu (CSP `connect-src 'none'`, zéro CDN, badge projet, zoom/pan actifs sur le schéma).
- [x] **Scénario d'Exception** : client sans capacité → texte + `http://localhost:8081/` (ou route `/api/archify/html`), aucun `_meta.ui`, appel sans erreur ; adresse `ui://` hors registre → refus « non conforme », aucun cadre rendu.
- [x] **Résilience** : shell JS — bannière sous `UI_MIN_WIDTH_PX = 320` (non bloquante, journalisée), `event.source !== window.parent` rejeté, mise à jour en place sans `reload`, aucun `localStorage`/`cookie`.

### C. Definition of Done (DoD)

- [x] Tous les fichiers modifiés respectent les standards du projet (Zéro lint error) : `code-check` livrables + `struct-check` récit.
- [x] Archivage du plan dans `Projects/mLoop/memory/plan/implementation_plan_MLOOP-212-FE.md` (le présent fichier).
- [x] EvidencePack mis à jour : `memory/evidence/MLOOP-212-FE_evidence.json`.
- [x] Sidecar worker ADR-0355 : `memory/worker_MLOOP-212-FE.status` → `COMPLETED`.
- [x] `python src/swarm.py sync --project mLoop` exécuté en clôture.
- [ ] **Orchestrateur** : `sprint_backlog.md` → `DONE_TESTED`, `git commit/push`.

### D. Verification Harness (ADR-0352 — non vide)

| # | Scénario Gherkin (récit §Scénarios de test) | Réf. de test | Statut |
| :-- | :--- | :--- | :--- |
| 1 | Affichage nominal des deux ressources `ui://` dans l'IDE | `tests/test_mcp_ui_apps.py::TestAffichageNominal` | ✅ |
| 2 | Appel d'outil sur client hôte sans support de l'extension `ui://` | `tests/test_mcp_ui_apps.py::TestClientSansSupport` | ✅ |
| 3 | Adresse de ressource hors registre des adresses officielles | `tests/test_mcp_ui_apps.py::TestAdresseHorsRegistre` | ✅ |
| 4 | Repli par bannière lorsque la largeur passe sous le seuil | `tests/test_mcp_ui_apps.py::TestBanniereRepliSeuil` | ✅ |
| 5 | Isolement réseau préservé à l'intérieur du cadre | `tests/test_mcp_ui_apps.py::TestIsolementReseau` | ✅ |
| 6 | Mise à jour en place lors d'un changement de projet | `tests/test_mcp_ui_apps.py::TestMiseAJourEnPlace` | ✅ |
| 7 | Indicateurs de progression, états de surface et traçabilité du repli | `tests/test_mcp_ui_apps.py::TestEtatsEtTracabilite` | ✅ |
