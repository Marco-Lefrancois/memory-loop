---
id: MLOOP-179-BE
jira_key: ''
epic_key: EPIC-17-MODULAR-REFACTORING
type: refactor
title: Extraction Modulaire de src/pipelines/sync.py — Pipeline Sync (BR=10)
origin: SPEC_SLICING
source_ref: 'EPIC-17 · epic17_prioritization_matrix.md · Rang #3 BR · OQ-171-05 Lot
  1 Top 5'
macro_size: S
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-172-BE
created_at: '2026-09-23'
grilled_at: '2026-09-23'
grill_decisions_ref: micro-grill 179 Q1-Q5 (Q1 micro B, Q2/Q4/Q5 pré-résolus Search-Before-Ask,
  Q3 reprise macro Q3)
approved_at: '2026-09-23'
approved_by: humain (go explicite batch APPROVE 173/174/175/176/178/179)
ttl_cycles: 4
---

# Extraction Modulaire de src/pipelines/sync.py — Pipeline Sync (BR=10)

## 1. Intention Métier (User Story)

**En tant qu'** ingénieur du framework mLoop,  
**je veux** découper `src/pipelines/sync.py` (542 L, 22.7 Ko, BR=10) en sous-modules cohérents inférieurs à 300 L chacun, en appliquant le cas général §2 du protocole d'extraction (famille Sync/Jira/Git) et les exigences ADR-0369 sur les timeouts réseau,  
**afin de** résorber la violation RULE-AST-01 du pipeline de synchronisation sans rompre les 10 callers existants ni introduire de blocage réseau non borné ou de régression du flux Jira/Git/hypergraphe.

---

## 2. Origine & Cadrage Avant-Projet

- **Document Source** : `memory/evidence/epic17_prioritization_matrix.md` (Réf : Rang #3, BR=10, Lot 1)
- **Protocole SSOT** : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` — **Cas général §2 (famille Sync/Jira/Git)**
- **Contrainte ADR-0369** : tout appel réseau synchrone (Jira API, Git remote, hypergraphe) doit porter un paramètre `timeout` explicite — zéro appel réseau non borné après extraction.
- **Hypothèse de Chiffrage Retenue** : Découpe en 2 à 3 sous-modules selon familles identifiées (ex. `_sync_jira`, `_sync_git`, `_sync_graph`) + shim de ré-export ; BR=10 impose un smoke check avant merge ; la frontière Git vs Jira vs hypergraphe doit être arbitrée en Grill-Me avant codage.
- **Enveloppe Macro Estimée** : S (fourchette de 0.5 à 1 jour)

---

## 3. Périmètre Sommaire

### In-Scope (Macro)
- Lecture et cartographie complète de `src/pipelines/sync.py` (542 L, 22.7 Ko) : identification des familles de responsabilités (synchronisation Jira, synchronisation Git, mise à jour hypergraphe Graphify, orchestration).
- Création du package `src/pipelines/sync/` avec sous-modules thématiques ≤ 300 L / 15 Ko chacun.
- Shim de ré-export `src/pipelines/sync.py` → `from src.pipelines.sync import *` garantissant la rétrocompatibilité des 10 callers sans modification de ceux-ci.
- Application stricte d'ADR-0369 : argument `timeout` explicite sur chaque appel réseau synchrone (`requests`, `subprocess.run`, client Jira) — interdiction formelle d'appel réseau non borné.
- Check fumée imports (`import_smoke_check`) + suite tests verte post-extraction.
- Mise à jour de `memory/evidence/epic17_prioritization_matrix.md` et archivage du plan sous `memory/plan/implementation_plan_MLOOP-179-BE.md`.

### Out-of-Scope (Macro)
- Modification des 10 callers existants (le shim garantit la rétrocompatibilité transparente).
- Refactoring fonctionnel du comportement du pipeline Sync (portée strictement structurelle).
- Autres fichiers de la matrice EPIC-17 (traités dans leurs récits dédiés MLOOP-173 à MLOOP-178).
- Introduction d'un client Jira ou Git tiers, ou modification des credentials de connexion (hors périmètre).

---

## 4. Critères de Succès Préliminaires

- [ ] Chaque sous-module du package `src/pipelines/sync/` passe `code-check --file` : ≤ 300 L, ≤ 15 Ko (RULE-AST-01 PASS).
- [ ] Shim `src/pipelines/sync.py` opérationnel : `python -c "from src.pipelines.sync import *"` sans erreur, zéro `ImportError`.
- [ ] Check fumée vert : `import_smoke_check --module src/pipelines/sync.py` — zéro symbole non résolu détecté.
- [ ] Suite tests inchangée : `pytest tests/ -x -q` — N_après PASS ≥ N_avant PASS, 0 FAIL.
- [ ] Conformité ADR-0369 : audit AST confirmant `timeout` explicite sur 100% des appels réseau synchrones — zéro appel `requests.get/post` ou `subprocess.run` sans `timeout`.
- [ ] Plan archivé sous `memory/plan/implementation_plan_MLOOP-179-BE.md` avec checklist §4 du protocole complétée.

---

## 5. Décisions Grill-Me 1:1 (Frontière Épuisée 2026-09-23)

> [!DONE]
> *Session contradictoire 1:1 clôturée — 5/5 questions tranchées (Q1 micro ici ; Q2/Q4/Q5 pré-résolus Search-Before-Ask ; Q3 reprise macro Q3).*
> *Récit éligible conversion Palier 2 après validation wikifix/rubber-duck et approbation humaine.*

- ✅ **Q1 — Famille Git vs Jira vs hypergraphe → Option B (3 modules, hypothèse ébauche rejetée)** : **zéro API Jira dans `sync.py`** (Jira = `src/pipelines/jira/` séparé, `httpx timeout=30.0`). Découpe réelle : `_sync_docs.py` (cache + directives + OQ + sprint ~250L) / `_sync_graph.py` (git wikis `timeout=8` + hypergraphe ~145L) / `_sync_run.py` (`run_sync` orchestrateur ~126L) + shim. L’option 2 modules (A) est viable mais mélange git-wikis et FS docs sans affinité.
- ✅ **Q2 — Timeouts réseau → pré-résolu Search-Before-Ask (inchangé)** : unique appel réseau = `subprocess.run(git pull, timeout=8)` L282-287 — **déjà ADR-0369**. Aucune constante `JIRA_TIMEOUT_S`/`GIT_TIMEOUT_S` à inventer (F1 : pas de Jira ici). Extraction = conserver `timeout=8` tel quel.
- ✅ **Q3 — Rollback BR=10 → reprise macro Q3** : revert Git immédiat, **0 FAIL strict** ; **BR=10 < 20 → autonomie worker** (pas d’arbitrage humain obligatoire).
- ✅ **Q4 — Séquençage vs db.py → pré-résolu Search-Before-Ask + macro Q2** : séquence Beachhead `state(78) → db(20) → sync(10)`. `db` est un **import lazy L480** (dans `run_sync`), `state` est top-level L6 — extraction de `sync` **après** 173 et 178 clôturés. Aucun conflit de schéma : sync n’écrit pas directement SQLite (passe par les fonctions de `db`).
- ✅ **Q5 — Dépendances state/lifecycle → pré-résolu Search-Before-Ask (F4)** : **`from src.state import LoopState, JournalEntry` top-level L6** → dépend de **173** (shim isole le risque) ; **zéro import `lifecycle`** → aucune attente sur 174.

---

## Règles d'affaires

- **Plafond modulaire absolu** : chaque sous-module de `src/pipelines/sync/` doit rester sous 300 lignes et 15 Ko (ADR-0202 / RULE-AST-01).
- **Timeout réseau explicite** : tout appel réseau synchrone conserve un `timeout` borné (git pull `timeout=8` inchangé, ADR-0369).
- **Rétrocompatibilité stricte des callers** : les callers (`run_sync`, `sync_hypergraph`) ne sont jamais modifiés — le shim `src/pipelines/sync.py` rend tout import historique résoluble sans `ImportError`.
- **Séquençage Beachhead** : extraction de `sync` uniquement après clôture de `state` (173) et `db` (178) — dépendances top-level et lazy préservées via les shims amont.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Extraction Pipeline Sync 3 Modules (Q1-B)
- [ ] Package `src/pipelines/sync/` créé : `_sync_docs.py`, `_sync_graph.py`, `_sync_run.py` — chacun ≤ 300 L / 15 Ko
- [ ] Hypothèse « API Jira dans sync.py » réfutée (F1) — Jira reste dans `src/pipelines/jira/` (`httpx timeout=30.0`)
- [ ] Unique appel réseau `subprocess.run(git pull, timeout=8)` conservé tel quel (ADR-0369, Q2)

#### 2. Rétrocompatibilité & Séquençage (Q3/Q4/Q5)
- [ ] Shim `src/pipelines/sync.py` résout les imports des 10 callers sans `ImportError`
- [ ] Dépendances préservées : `state` top-level L6 (via shim 173), `db` lazy L480 (via shim 178), **zéro import `lifecycle`**
- [ ] Suite tests inchangée : `pytest tests/ -x -q` — N_après ≥ N_avant PASS, 0 FAIL
- [ ] Rollback BR=10 < 20 → autonomie worker (macro Q3), revert Git immédiat, 0 FAIL strict

### Admission of Limits
- Avertissements rubber-duck génériques (timeout réseau, expiration de session, saisie extrême) hors domaine : pipeline sync interne — timeout git, rollback partiel et état vide couverts par les piliers Gherkin.

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : refactoring modulaire interne de `src/pipelines/sync.py` — **aucune route HTTP n'est consommée ni exposée**. Toute route découverte en cours d'implémentation fera l'objet d'une question ouverte `OQ-179` avec la mention `[API de soumission à définir]` — jamais inventée (Zéro Fausse Route, AGENTS.md).

| Contrat | Engagement |
|:---|:---|
| `from src.pipelines.sync import *` (shim) | Rétrocompatibilité 10 callers, zéro modification caller |
| `subprocess.run(git pull, timeout=8)` | Timeout réseau borné conservé (ADR-0369) |
| `code-check --file` sous-modules | ≤ 300 L / 15 Ko each (RULE-AST-01 PASS) |

---

## Scénarios de test

### Pilier 1 — Nominal (Happy path)
```gherkin
Scénario : Découpage modulaire du pipeline sync
  Étant donné le package "src/pipelines/sync/" subdivisé en sous-modules <= 300 lignes
  Quand le pipeline sync est déclenché sur un projet
  Alors les artefacts sont synchronisés sans régression ni perte de données
```

### Pilier 2 — Exceptions (Cas d'erreur)
```gherkin
Scénario : Gestion d'erreur de parsing dans un artefact source
  Étant donné un fichier Markdown ou JSON corrompu lors de la synchronisation
  Quand le synchroniseur traite ce fichier
  Alors l'erreur est logguée avec exc_info et le traitement continue sur les autres fichiers
```

### Pilier 3 — Résilience (Réseau / Timeout / Mode dégradé)
```gherkin
Scénario : Interruption ou timeout pendant la synchronisation
  Étant donné une interruption de flux ou un timeout
  Quand le synchroniseur s'arrête
  Alors l'état partiel est rollbacké et les fichiers cibles restent dans un état cohérent
```

### Pilier 4 — UX / Accessibilité / État vide
```gherkin
Scénario : Synchronisation sur un projet vide
  Étant donné un projet sans récits ni artefacts
  Quand la commande sync est lancée
  Alors un message clair d'état vide est émis sans lever d'exception
```
