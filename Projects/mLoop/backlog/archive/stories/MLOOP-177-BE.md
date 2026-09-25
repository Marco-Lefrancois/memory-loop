---
id: MLOOP-177-BE
jira_key: ''
epic_key: EPIC-17-MODULAR-REFACTORING
type: refactoring
title: Extraction Modulaire de src/dashboard/server.py — Routeurs FastAPI (BR=0, 1634L)
origin: SPEC_SLICING
source_ref: 'EPIC-17 · epic17_prioritization_matrix.md · Rang #36 BR · Lot 3 OQ-171-03'
macro_size: S
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-172-BE
created_at: '2026-09-23'
content_hash: b2e2337544b1d688
ttl_cycles: 4
---

# Extraction Modulaire de src/dashboard/server.py — Routeurs FastAPI (BR=0, 1634L)

## 1. Intention Métier (User Story)

**En tant qu'** ingénieur du framework mLoop,  
**je veux** découper `src/dashboard/server.py` (1634 L, BR=0) en routeurs FastAPI modulaires inférieurs à 300 L chacun, en suivant le cas général §2 du protocole d'extraction modulaire,  
**afin de** résorber la violation RULE-AST-01 du serveur dashboard — explicitement intégré dans la file d'attente par l'arbitrage OQ-171-03 — sans régression sur les endpoints REST ni sur le cockpit web.

---

## 2. Origine & Cadrage Avant-Projet

- **Document Source** : `Projects/mLoop/memory/evidence/epic17_prioritization_matrix.md` (Réf : Rang #36, BR=0, Lot 3, 65.9 Ko) · **Arbitrage OQ-171-03** : `archify.py` + `server.py` intégrés dans la file (Lot 3)
- **Protocole SSOT** : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` — **Cas général §2 (découpe par famille de responsabilités — routeurs FastAPI par domaine)**
- **Hypothèse de Chiffrage Retenue** : Découpe en routeurs FastAPI partiels par domaine (system, metrics, ledger, events, backlog, rules, graph) + `server.py` shim d'application principale ; BR=0 callers directs, risque faible en isolation mais surface d'intégration dashboard élevée.
- **Enveloppe Macro Estimée** : S (0.5 à 1 jour)

---

## 3. Périmètre Sommaire

### In-Scope (Macro)
- Lecture et cartographie de `src/dashboard/server.py` (1634 L, 65.9 Ko) : identification des domaines de routeurs FastAPI.
- Extraction vers `src/dashboard/routers/` : `system.py` (229L), `metrics.py` (200L), `_ledger_helpers.py` (243L), `ledger.py` (291L), `events.py` (256L), `rules.py` (85L), `graph.py` (88L), `_backlog_helpers.py` (188L), `backlog.py` (253L).
- `server.py` réduit au rôle de point d'entrée ASGI concis (144L) : instanciation `FastAPI()`, inclusion des routeurs, configuration middleware CORS, montage `/static` et route racine `/`.
- Rétrocompatibilité totale des imports (`stream_events`, `_get_active_project`, etc.) assurée via ré-export dans `server.py`.
- Vérification ADR-0369 sur tous les sous-modules : context managers `with` sur fichiers, timeouts, zéro exception silencieuse.
- Check fumée imports + suite tests verte (77/77 PASS) + mise à jour de `epic17_prioritization_matrix.md`.

### Out-of-Scope (Macro)
- Modification des logiques métier des endpoints (portée strictement structurelle / routage).
- Ajout de nouveaux endpoints ou refonte de l'API REST du dashboard.
- Autres fichiers Lot 3 (`svg_to_md.py`) — traités dans MLOOP-176-BE.
- `src/dashboard/routers/archify.py` (463 L, BR=2) — traité séparément.

---

## 4. Critères de Succès Préliminaires

- [x] Chaque routeur extrait passe `code-check --file` : ≤ 300 L, ≤ 15 Ko (10/10 PASS).
- [x] `server.py` réduit au rôle de shim ASGI : ≤ 300 L après extraction des routeurs (144 L).
- [x] Application FastAPI démarrable : `python -c "from src.dashboard.server import app; print(len(app.routes))"` sans erreur (42 routes).
- [x] Tous les endpoints REST répondent correctement après extraction (`pytest tests/ -k "dashboard"` 77/77 PASS).
- [x] ADR-0369 respecté : `with` sur fichiers, `timeout` sur appels réseau, zéro exception silencieuse.
- [x] Suite tests inchangée : `pytest tests/ -k "dashboard"` — 77 PASS, 0 FAIL.
- [x] Plan archivé sous `memory/plan/implementation_plan_MLOOP-177-BE.md` avec checklist complétée.

---

## 5. Arbitrages Grill-Me Micro 1:1

| Question | Arbitrage Tranché |
|:---|:---|
| ❓ Conflit SCC MLOOP-145-BE | **Pas de conflit** : Les loggers configurés par MLOOP-145-BE sont intégralement préservés dans chaque sous-routeur avec leurs noms de composant dédiés et `exc_info=True`. |
| ❓ Structure de routeurs existante | **Alignement direct** : Les nouveaux sous-routeurs s'intègrent dans `src/dashboard/routers/` à côté des routeurs existants (`overview`, `swarm`, `traces`, etc.). |
| ❓ Middleware et configuration ASGI | **Maintien dans server.py** : Les middlewares CORS et la gestion statique restent dans `server.py` en tant que configuration racine ASGI. |
| ❓ Tests d'intégration dashboard | **77 tests existants** : La suite `tests/test_dashboard*.py` sert de harnais de non-régression immédiat. |
| ❓ BR=0 et risque réel | **Zéro risque de rupture** : Endpoints REST 100% rétrocompatibles, `stream_events` réexporté dans `server.py`. |

---

## 6. Scénarios de Test (Gherkin 4 Piliers)

### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Découpage modulaire réussi sous le seuil strict de 300 lignes
  Étant donné le serveur monolithique "src/dashboard/server.py" de 1 635 lignes
  Quand le refactoring modulaire est appliqué en routeurs spécialisés sous "src/dashboard/routers/"
  Alors "src/dashboard/server.py" compte au maximum 300 lignes (144 lignes atteintes)
  Et chaque sous-routeur créé compte au maximum 300 lignes
  Et la commande "code-check" rapporte 0 violation RULE-AST-01 sur l'ensemble des modules
```

### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Rejet des violations de plafonds modulaires
  Étant donné un routeur extrait dont la taille dépasserait 300 lignes ou 15 Ko
  Quand la commande "code-check" est exécutée sur ce module
  Alors la violation RULE-AST-01 est levée et le module doit être scindé avec un helper
```

### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Tolérance aux données JSONL corrompues ou manquantes
  Étant donné un fichier "token_ledger.jsonl" ou "events.jsonl" contenant une ligne corrompue
  Quand un client appelle l'endpoint "/api/metrics", "/api/ledger" ou "/api/events"
  Alors l'erreur de parsing est logguée en debug avec exc_info=True selon ADR-0369
  Et les lignes valides restantes sont traitées et retournées sans crash HTTP 500
```

### Pilier 4 — Performance & Limites
```gherkin
Scénario : Non-régression complète de l'application FastAPI et de la suite de tests
  Étant donné l'application FastAPI instanciée dans "src/dashboard/server.py"
  Quand la suite de tests dashboard est exécutée via "pytest tests/ -k 'dashboard'"
  Alors les 77 tests existants réussissent sans aucune régression
  Et l'import de "stream_events" depuis "src.dashboard.server" fonctionne par ré-export
```
