# Dossier de Preuves Documentaires — MLOOP-150-BE
> Grill-with-Docs (ADR-0320 / ADR-0326 / ADR-0361) — Cadrage DRAFT, séance Grill-Me 1:1 à venir. Fact-Search exécuté le 2026-09-22 (`python src/swarm.py fact-search --project mLoop` : 5 faits, aucun couvrant /api/archify → initiative nouvelle).

## 1. Sources & Maquettes SSOT
- file:///C:/Memory%20Loop/src/dashboard/server.py (L40-46, L69-76)
- file:///C:/Memory%20Loop/src/dashboard/routers/database.py (L27-54, L60-84)
- file:///C:/Memory%20Loop/tools/archify/showcase/ (artefacts `*.architecture.html` existants)
- file:///C:/Memory%20Loop/docs/05-assets/mloop-framework.architecture.html
- file:///C:/Memory%20Loop/src/commands/_registry.py (L892-905 : commande dashboard)

## 2. Extraits Verbatim Sourcés
**Extrait 1 — Montage des routers modulaires (server.py L69-76)** : « # ── Montage des Routeurs Modulaires Agentiques (Dashboard 2.0) ───── app.include_router(overview_router) ... app.include_router(database_router) » ➔ Fait établi : le pattern d'intégration d'un router Archify est déjà standardisé (7 routers montés via include_router).

**Extrait 2 — Sécurité allowlist (database.py L35-46)** : « def _resolve_secure_db_path(db_name: str...) ... raise HTTPException(status_code=403, detail="Accès interdit : nom de base non autorisé.") » ➔ Fait établi : le dashboard impose déjà une allowlist anti path-traversal répliquable telle quelle pour servir les artefacts Archify.

**Extrait 3 — Artefacts Archify sur disque** : `tools/archify/showcase/mloop-framework.architecture.html`, `tools/archify/showcase/phases/p0-inception.architecture.html`, `docs/05-assets/mloop-framework.architecture.html`, `docs/05-assets/mloop-lifecycle.lifecycle.html` ➔ Fait établi : les diagrammes HTML standalone existent déjà ; aucun endpoint ne les sert (vérification `search_codebase` "archify" : 0 hit sous `src/dashboard/`).

**Extrait 4 — Restitution HTML existante (database.py L60-77)** : « @router.get("/api/graph/html", response_class=HTMLResponse) ... return HTMLResponse(content=candidate.read_text(...), media_type="text/html; charset=utf-8") » ➔ Fait établi : le pattern de restitution d'un fichier HTML statique local est déjà opérationnel dans le routeur Graph.

## 3. Contrats Déclaratifs Cibles (REST)
| Méthode | Route | Finalité |
|:---|:---|:---|
| `GET` | `/api/archify/list?project=<nom>` | Inventaire des artefacts Archify (nom, type, taille, chemin relatif) |
| `GET` | `/api/archify/html?file=<nom>&project=<nom>` | Restitution HTML standalone (200 / 404 / 403 hors allowlist) |

## 4. Frontière Active & Admission of Limits
- **Conflit SCC** : `src/dashboard/server.py` figure dans le Groupe B de MLOOP-145-BE (instrumentation logging, story L58 : « src/dashboard/server.py (20 except) — API Cockpit ») ➔ `blocked_by: MLOOP-145-BE` obligatoire avant tout dev.
- Aucun endpoint `/api/archify*` n'existe aujourd'hui — preuve par recherche de code négative (2 passes).
- Open questions OQ-150-01 → OQ-150-05 : voir story §5 (résolution en Grill-Me 1:1).