---
id: MLOOP-150-BE
jira_key: MLOOP-150-BE
epic_key: EPIC-16-DASHBOARD-TOOLING
type: backend
title: API REST Archify — Inventaire et Restitution des Diagrammes HTML dans le Dashboard
layer: api
status: SHIPPED
grill_me: DONE
invest_score: 6/6
depends_on: []
blocked_by:
- MLOOP-145-BE
content_hash: 44e5d5d7dec8a091
---

# API REST Archify — Inventaire et Restitution des Diagrammes HTML dans le Dashboard

> [!NOTE]
> Récit Palier 2 consolidé suite à la séance **Grill-Me Micro 1:1** du 2026-09-22 (5 arbitrages verbatim consignés en §5). Dossier de preuves : `memory/evidence/MLOOP-150-BE_fact_dossier.md`.

## 1. Contexte & Value Proposition

Le dashboard mLoop (`python src/swarm.py dashboard`, port 8080) expose déjà les onglets OVERVIEW, PIPELINE, GRAPH & DATABASE, LEGACY. Les diagrammes interactifs générés par **Archify** (`*.architecture.html`, `*.lifecycle.html`) existent sur disque (`tools/archify/showcase/`, `docs/05-assets/`) mais **aucun endpoint ne les sert** (preuve par recherche de code négative : 0 hit `archify` sous `src/dashboard/`). L'agent doit aujourd'hui ouvrir ces fichiers manuellement — hors Cockpit, sans traçabilité.

**Valeur** : consultation souveraine et locale des diagrammes d'architecture directement dans le dashboard, sans exfiltration (zéro serveur externe), alignée sur le pattern sécurité existant de `database.py`.


---

## 2. Périmètre

| In Scope | Out of Scope |
|:---|:---|
| Router `src/dashboard/routers/archify.py` (endpoints `/api/archify/list`, `/api/archify/html`) | Compilation batch de nouveaux diagrammes (hors requis — seule la compilation à la volée arbitrée est incluse) |
| Allowlist multi-tenant (racines framework récursives + racines projet résolu) | Modification du runner Archify `tools/archify/archify_runner.py` |
| Compilation à la volée subprocess (timeout explicite ADR-0369) | Onglet UI Archify (récit MLOOP-151-FE, séparé) |
| Non-régression `tests/test_dashboard_*.py` | DrawDB (récit MLOOP-152-BE, sépar
---

## 3. Constats du Dossier de Preuves

1. **Pattern router standardisé** : 7 routers modulaires montés via `app.include_router(...)` dans `server.py` (L69-76) — le router Archify suit le même montage.
2. **Pattern sécurité répliquable** : `_resolve_secure_db_path` avec `HTTPException(403)` hors allowlist (`database.py` L27-54) — même mécanique pour les artefacts.
3. **Artefacts existants** : `tools/archify/showcase/mloop-framework.architecture.html`, `tools/archify/showcase/phases/p0-inception.architecture.html`, `docs/05-assets/mloop-framework.architecture.html`, `docs/05-assets/mloop-lifecycle.lifecycle.html`.
4. **Restitution HTML déjà opérationnelle** : `GET /api/graph/html` sert un fichier local via `HTMLResponse` (`database.py
---

## 4. Dépendances & Blocages

- `blocked_by: MLOOP-145-BE` — **Conflit SCC Group B** : `src/dashboard/server.py` est modifié par les deux récits (MLOOP-145-BE y instrumente le logging, 20 excepts). Aucun dev avant DONE_TESTED de MLOOP-145-BE.
- `depends_on: []` — aucune dépendance transverse autre que
---

## 5. Arbitrages Grill-Me Micro 1:1 (Séance du 2026-09-22)

> ✅ Session Grill-with-Docs tenue (1 question par tour, arbitrages verbatim du PO).

| OQ | Décision Arbitrée |
|:---|:---|
| OQ-150-01 | **Allowlist par racines, découverte récursive** : `tools/archify/showcase/`, `docs/05-assets/` — **amendée en clôture de séance** (« archify doit être également disponible pour tous les projets ») ➔ racines `Projects/<projet>/` intégrées (multi-tenant) |
| OQ-150-02 | **Paramètre `project` actif** : résolution canonique via `resolve_project_canonical_name` (pattern `database.py`) ; l'inventaire couvre le framework ET les artefacts du projet résolu |
| OQ-150-03 | **Lecture disque directe à chaque appel** — zéro cache (volumétrie < 50 artefacts, fraîcheur garantie) |
| OQ-150-04 | **Compilation à la volée activée** : si seul le JSON de spec existe, `subprocess` Archify avec `timeout` explicite (ADR-0369) ; échecs couverts au Pilier 3 |
| OQ-150-05 | **Endpoint unique** pour `*.architecture.html` et `*.lifecycle.html`, discrimination par champ `typ
---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Inventaire Multi-Tenant
- [ ] `GET /api/archify/list?project=<nom>` agrège les artefacts du framework (racines récursives) et du projet résolu, avec `name`, `type`, `size_bytes`, `relative_path`
- [ ] Validation anti path-traversal sur 100% des chemins (403 hors allowlist)

#### 2. Restitution & Compilation
- [ ] `GET /api/archify/html?file=...&project=...` restitue le HTML standalone (200) ; 404 si absent de toutes les racines ; 403 hors allowlist
- [ ] Compilation subprocess à la volée avec `timeout` explicite si JSON sans HTML ; 500 documenté si échec

#### 3. Non-Régression
- [ ] Suites `tests/test_dashboard_*.py` existantes passent
- [ ] Vibe-Check 20/20 après implémentation

### Scénarios de test (Gherkin 4 Piliers)

#### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Inventaire multi-tenant des artefacts Archify
  Étant donné des artefacts "*.architecture.html" sous "tools/archify/showcase/" et "docs/05-assets/"
  Et des artefacts compilés sous "Projects/<projet>/docs/05-assets/"
  Quand "GET /api/archify/list?project=<projet>" est appelé
  Alors la réponse 200 liste chaque artefact avec "name", "type", "size_bytes", "relative_path"
  Et le champ "type" vaut "architecture" ou "lifecycle" selon l'extension
```

#### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Requête hors allowlist rejetée
  Étant donné une requête "GET /api/archify/html?file=../src/state.py"
  Quand le chemin est résolu contre les racines allowlistées
  Alors la réponse est 403 avec un détail explicite
  Et aucun fichier hors allowlist n'est lu

Scénario : Artefact introuvable
  Étant donné un nom de fichier absent de toutes les racines
  Quand "GET /api/archify/html" est appelé
  Alors la réponse est 404 avec la commande CLI de compilation suggérée
```

#### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Compilation à la volée en échec
  Étant donné un JSON de spec Archify sans HTML compilé
  Quand "GET /api/archify/html" est appelé
  Alors la compilation subprocess est tentée avec un "timeout" explicite
  Et en cas de timeout ou de code de sortie non nul la réponse est 500 avec la cause loguée
  Et le serveur reste opérationnel pour les requêtes suivantes

Scénario : Anti-rebond sur la compilation à la volée
  Étant donné une compilation subprocess déjà en cours pour un artefact donné
  Quand une seconde requête "GET /api/archify/html" arrive pour le même artefact
  Alors une seule compilation est déclenchée (verrou en cours ou attente du résultat existant)
  Et le bouton de soumission double-clic n'émet pas de second processus
```

#### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Inventaire vide et message actionnable
  Étant donné un projet sans aucun artefact Archify
  Quand "GET /api/archify/list?project=<projet>" est appelé
  Alors la réponse 200 expose "total_artifacts": 0
  Et le message suggère la commande "python src/swarm.py archify 
---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

| Méthode | Route | Finalité |
|:---|:---|:---|
| `GET` | `/api/archify/list?project=<nom>` | Inventaire multi-tenant : artefacts framework (récursif) + artefacts du projet résolu, champ `type` discriminant |
| `GET` | `/api/archify/html?file=<nom>&project=<nom>` | Restitution HTML standalone ; compilation subprocess à la volée (timeout ADR-0369) si JSON sans HTML |
| `subprocess` | `tools.archify.archify_runner:run_archify_command` | Compilation à la volée (timeout explicite, code de sortie contrôlé, échec logué) |