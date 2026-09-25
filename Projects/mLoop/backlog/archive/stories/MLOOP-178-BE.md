---
id: MLOOP-178-BE
jira_key: ''
epic_key: EPIC-17-MODULAR-REFACTORING
type: refactor
title: Extraction Modulaire de src/loop_mem/db.py — Couche SQLite (BR=20)
origin: SPEC_SLICING
source_ref: 'EPIC-17 · epic17_prioritization_matrix.md · Rang #2 BR · OQ-171-05 Lot
  1 Top 5'
macro_size: M
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-172-BE
created_at: '2026-09-23'
grilled_at: '2026-09-23'
grill_decisions_ref: micro-grill 178 Q1-Q5 (Q2/Q4 pré-résolus Search-Before-Ask, Q3
  reprise macro Q3)
approved_at: '2026-09-23'
approved_by: humain (go explicite batch APPROVE 173/174/175/176/178/179)
ttl_cycles: 4
---

# Extraction Modulaire de src/loop_mem/db.py — Couche SQLite (BR=20)

## 1. Intention Métier (User Story)

**En tant qu'** ingénieur du framework mLoop,  
**je veux** découper `src/loop_mem/db.py` (956 L, 36.6 Ko, BR=20) en sous-modules cohérents inférieurs à 300 L chacun, en appliquant le cas général §2 du protocole d'extraction (famille DB/SQLite) et les exigences ADR-0369 sur les context managers,  
**afin de** résorber la violation RULE-AST-01 du module de persistance SQLite sans rompre les 20 callers existants ni introduire de fuite de connexion ou de désynchronisation transactionnelle.

---

## 2. Origine & Cadrage Avant-Projet

- **Document Source** : `memory/evidence/epic17_prioritization_matrix.md` (Réf : Rang #2, BR=20, Lot 1)
- **Protocole SSOT** : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` — **Cas général §2 (famille DB/SQLite)**
- **Contrainte ADR-0369** : 100% des accès SQLite encapsulés dans des blocs `with sqlite3.connect(...)` — zéro connexion ouverte hors context manager après extraction.
- **Hypothèse de Chiffrage Retenue** : Découpe en 3 sous-modules (`_db_schema`, `_db_queries`, `_db_migrations`) + shim de ré-export ; BR=20 impose un smoke check complet avant tout merge ; la frontière connection-pool vs queries doit être arbitrée en Grill-Me avant codage.
- **Enveloppe Macro Estimée** : M (fourchette de 1 à 2 jours)

---

## 3. Périmètre Sommaire

### In-Scope (Macro)
- Lecture et cartographie complète de `src/loop_mem/db.py` (956 L, 36.6 Ko) : identification des familles (schéma/DDL, requêtes CRUD, migrations, connexion pool le cas échéant).
- Création du package `src/loop_mem/db/` avec sous-modules thématiques ≤ 300 L / 15 Ko chacun.
- Shim de ré-export `src/loop_mem/db.py` → `from src.loop_mem.db import *` garantissant la rétrocompatibilité des 20 callers sans modification de ceux-ci.
- Application stricte d'ADR-0369 : chaque accès `sqlite3.connect` dans les sous-modules encapsulé dans un bloc `with` — interdiction formelle d'ouvrir une connexion hors context manager.
- Check fumée imports (`import_smoke_check`) + suite tests verte post-extraction.
- Mise à jour de `memory/evidence/epic17_prioritization_matrix.md` et archivage du plan sous `memory/plan/implementation_plan_MLOOP-178-BE.md`.

### Out-of-Scope (Macro)
- Modification des 20 callers existants (le shim garantit la rétrocompatibilité transparente).
- Refactoring fonctionnel ou enrichissement du comportement de `db.py` (portée strictement structurelle).
- Autres fichiers de la matrice EPIC-17 (traités dans leurs récits dédiés MLOOP-173 à MLOOP-177 et MLOOP-179).
- Introduction d'un ORM ou couche d'abstraction tierce (hors périmètre, aucun JSON fictif ni fausse route API).

---

## 4. Critères de Succès Préliminaires

- [ ] Chaque sous-module du package `src/loop_mem/db/` passe `code-check --file` : ≤ 300 L, ≤ 15 Ko (RULE-AST-01 PASS).
- [ ] Shim `src/loop_mem/db.py` opérationnel : `python -c "from src.loop_mem.db import *"` sans erreur, zéro `ImportError`.
- [ ] Check fumée vert : `import_smoke_check --module src/loop_mem/db.py` — zéro symbole non résolu détecté.
- [ ] Suite tests inchangée : `pytest tests/ -x -q` — N_après PASS ≥ N_avant PASS, 0 FAIL.
- [ ] Conformité ADR-0369 : audit AST confirmant 100% des `sqlite3.connect` dans un bloc `with` — zéro connexion nue détectée.
- [ ] Plan archivé sous `memory/plan/implementation_plan_MLOOP-178-BE.md` avec checklist §4 du protocole complétée.

---

## 5. Décisions Grill-Me 1:1 (Frontière Épuisée 2026-09-23)

> [!DONE]
> *Session contradictoire 1:1 clôturée — 5/5 questions tranchées (Q1 et Q5 micro ici ; Q2/Q4 pré-résolus Search-Before-Ask ; Q3 reprise macro Q3).*
> *Récit éligible conversion Palier 2 après validation wikifix/rubber-duck et approbation humaine.*

- ✅ **Q1 — Frontière connection vs queries → Option A (4 modules)** : `_db_connection.py` (session CM + DDL + legacy) / `_db_observations.py` (CRUD ~140L) / `_db_lexicon.py` (lexicon + rho ~225L) / `_db_search.py` (FTS + fact-search + helpers JSON ~290L) + shim. L’option 3 modules était rejetée (4ᵉ coupure imposée par le plafond 300L).
- ✅ **Q2 — Effets de bord à l’import → pré-résolu Search-Before-Ask (pas de `_db_init.py`)** : zéro `open()`/`re.compile` top-level ; schéma lazzy via `_init_observation_db` + `_INITIALIZED_DBS` ; side effects minimes (logger L9, path L147, set L215) — sur-ingénierie d’un 5ᵉ module.
- ✅ **Q3 — Rollback BR=20 → reprise macro Q3** : revert Git immédiat, **0 FAIL strict**, **arbitrage humain obligatoire** (BR=20 ≥ 20).
- ✅ **Q4 — Séquençage vs state.py → reprise macro Q2 + fait F5** : `state → db → sync` (Beachhead). **Aucune circularité** : `db.py` n’importe pas `state.py` ; dépendance inversée uniquement (`state.py:L506/L669` importe `search_in_memory`).
- ✅ **Q5 — Legacy `_get_observation_conn` → Option A (supprimer à l’extraction)** : 0 caller production (seul usage = test de dépréciation `test_python_senior_standards.py:L178`) ; ADR-0369 L47 interdit formellement le pattern. Migration test → assert « symbole absent du shim » ; critère §4 : zéro fonction retournant `sqlite3.Connection` nue dans le package.

---

## Règles d'affaires

- **Plafond modulaire absolu** : chaque sous-module de `src/loop_mem/db/` doit rester sous 300 lignes et 15 Ko (ADR-0202 / RULE-AST-01).
- **Context manager obligatoire** : 100% des accès SQLite via `with get_observation_db_session()` — zéro connexion nue retournée à l’appelant après extraction (ADR-0369 L46-47).
- **Rétrocompatibilité stricte des callers** : les callers existants ne sont jamais modifiés — le shim `src/loop_mem/db.py` rend tout import historique résoluble sans `ImportError`.
- **Rollback borné BR ≥ 20** : échec smoke check → revert Git immédiat sous arbitrage humain obligatoire (seuil macro Q3).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Extraction Couche SQLite 4 Modules (Q1-A)
- [ ] Package `src/loop_mem/db/` créé : `_db_connection.py`, `_db_observations.py`, `_db_lexicon.py`, `_db_search.py` — chacun ≤ 300 L / 15 Ko
- [ ] 100% des accès SQLite via `with get_observation_db_session()` — zéro connexion nue retournée (ADR-0369 L46-47)
- [ ] Legacy `_get_observation_conn` supprimé du shim (Q5-A) — assert « symbole absent » migré dans le test de dépréciation

#### 2. Rétrocompatibilité & Rollback BR=20 (Q3)
- [ ] Shim `src/loop_mem/db.py` résout les imports des 20 callers sans `ImportError`
- [ ] Check fumée vert + `pytest tests/ -x -q` : N_après PASS ≥ N_avant PASS, 0 FAIL
- [ ] Rollback borné BR ≥ 20 : échec smoke → revert Git immédiat sous arbitrage humain obligatoire
- [ ] Séquençage Beachhead #2 — extraction après `state` (173), avant `sync` (179)

### Admission of Limits
- Avertissements rubber-duck génériques (timeout réseau, expiration de session, anti-rebond) hors domaine : couche SQLite interne headless — contention, rollback et initialisation vierge couverts par les piliers Gherkin.

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : refactoring modulaire interne de `src/loop_mem/db.py` — **aucune route HTTP n'est consommée ni exposée**. Toute route découverte en cours d'implémentation fera l'objet d'une question ouverte `OQ-178` avec la mention `[API de soumission à définir]` — jamais inventée (Zéro Fausse Route, AGENTS.md).

| Contrat | Engagement |
|:---|:---|
| `from src.loop_mem.db import *` (shim) | Rétrocompatibilité 20 callers, zéro modification caller |
| `with get_observation_db_session()` | Context manager obligatoire, zéro connexion nue (ADR-0369) |
| `code-check --file` sous-modules | ≤ 300 L / 15 Ko each (RULE-AST-01 PASS) |

---

## Scénarios de test

### Pilier 1 — Nominal (Happy path)
```gherkin
Scénario : Découpage modulaire transparent de la couche SQLite
  Étant donné le package "src/loop_mem/db/" subdivisé en sous-modules <= 300 lignes
  Quand un appelant importe les symboles via le shim "src/loop_mem/db.py"
  Alors tous les symboles publics sont résolus sans régression ni avertissement
```

### Pilier 2 — Exceptions (Cas d'erreur)
```gherkin
Scénario : Détection d'accès SQLite non sécurisé
  Étant donné une requête SQL malformée ou un verrou SQLite actif
  Quand la requête est exécutée dans le harnais
  Alors une exception typée est levée avec rollback automatique
```

### Pilier 3 — Résilience (Réseau / Timeout / Mode dégradé)
```gherkin
Scénario : Timeout et récupération sur base verrouillée
  Étant donné une contention sur la base SQLite
  Quand le timeout explicite ADR-0369 expire
  Alors la connexion est fermée proprement sans fuite de descripteur
```

### Pilier 4 — UX / Accessibilité / État vide
```gherkin
Scénario : Initialisation sur base de données vierge
  Étant donné un chemin de base SQLite vierge
  Quand le module est initialisé
  Alors les tables sont créées sans effet de bord ni message parasite
```
