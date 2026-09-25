---
id: MLOOP-173-BE
jira_key: ''
epic_key: EPIC-17-MODULAR-REFACTORING
type: refactor
title: Extraction Modulaire de src/state.py — Singleton d'État Partagé (BR=78)
origin: SPEC_SLICING
source_ref: 'EPIC-17 · epic17_prioritization_matrix.md · Rang #1 BR'
macro_size: M
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-172-BE
created_at: '2026-09-23'
grilled_at: '2026-09-23'
grill_decisions_ref: memory/evidence/EPIC17_grill_macro_fact_dossier.md + micro-grill
  173 Q1-Q3
approved_at: '2026-09-23'
approved_by: humain (go explicite batch APPROVE 173/174/175/176/178/179)
ttl_cycles: 4
---

# Extraction Modulaire de src/state.py — Singleton d'État Partagé (BR=78)

## 1. Intention Métier (User Story)

**En tant qu'** ingénieur du framework mLoop,  
**je veux** découper `src/state.py` (770 L, BR=78) en sous-modules cohérents inférieurs à 300 L chacun, en appliquant le pattern Singleton d'état partagé documenté au §3.2 du protocole d'extraction,  
**afin de** résorber la violation RULE-AST-01 la plus critique du codebase sans rompre les 78 callers existants ni provoquer de désynchronisation d'instance.

---

## 2. Origine & Cadrage Avant-Projet

- **Document Source** : `memory/evidence/epic17_prioritization_matrix.md` (Réf : Rang #1, BR=78, Lot 1)
- **Protocole SSOT** : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` — **Cas spécial §3.2 Singletons d'état**
- **Hypothèse de Chiffrage Retenue** : Découpe en 3 sous-modules (`_state_core`, `_state_accessors`, `_state_serializer`) + shim de ré-export ; BR=78 impose des tests de fumée complets avant tout merge.
- **Enveloppe Macro Estimée** : M (fourchette de 1 à 2 jours)

---

## 3. Périmètre Sommaire

### In-Scope (Macro)
- Lecture et cartographie complète de `src/state.py` (770 L, 31.1 Ko) : identification des familles (noyau d'état, accesseurs get/set, sérialisation JSON).
- Création du package `src/state/` avec sous-modules `_state_core.py`, `_state_accessors.py`, `_state_serializer.py`, chacun ≤ 300 L / 15 Ko.
- Shim de ré-export `src/state.py` → `from src.state import *` garantissant la rétrocompatibilité des 78 callers sans modification de ceux-ci.
- Application stricte de la **règle critique §3.2** : instance singleton créée **une seule fois** dans `src/state/__init__.py` — toute instanciation de `ProjectState()` dans un sous-module est formellement interdite.
- Check fumée imports (`import_smoke_check`) + suite tests verte post-extraction.
- Mise à jour de `epic17_prioritization_matrix.md` et archivage du plan sous `memory/plan/`.

### Out-of-Scope (Macro)
- Modification des 78 callers (le shim garantit la rétrocompatibilité transparente).
- Refactoring fonctionnel ou enrichissement du comportement de `state.py` (portée strictement structurelle).
- Autres fichiers de la matrice EPIC-17 (traités dans leurs récits dédiés MLOOP-174 à MLOOP-177).

---

## 4. Critères de Succès Préliminaires

- [ ] Chaque sous-module du package `src/state/` passe `code-check --file` : ≤ 300 L, ≤ 15 Ko (RULE-AST-01 PASS).
- [ ] Shim `src/state.py` opérationnel : `python -c "from src.state import *"` sans erreur, zéro `ImportError`.
- [ ] Check fumée vert : `import_smoke_check --module src/state.py` — zéro symbole non résolu détecté.
- [ ] Suite tests inchangée : `pytest tests/ -x -q` — N_après PASS ≥ N_avant PASS, 0 FAIL.
- [ ] Instance singleton unique : aucune instanciation de la classe d'état hors de `src/state/__init__.py` (audit AST).
- [ ] Plan archivé sous `memory/plan/implementation_plan_MLOOP-173-BE.md` avec checklist §4 du protocole complétée.

---

## 5. Décisions Grill-Me 1:1 (Frontière Épuisée 2026-09-23)

> [!DONE]
> *Session contradictoire 1:1 clôturée — 5/5 questions tranchées (3 micro-grill ici + 2 reprises du macro Q2/Q3).*
> *Décisions consignées ci-dessous ; récit éligible conversion Palier 2 après validation wikifix/rubber-duck et approbation humaine.*

- ✅ **Q1 — Frontière noyau vs accesseurs → Option A** : `_state_core.py` = exceptions + enums + modèles Pydantic + `SavepointManager` (~340L) ; `_state_accessors.py` = méthodes `LoopState` pures (`transition_to`, `can_transition_to`, `query_graph`…) ; `_state_serializer.py` = méthodes I/O (`checkpoint`, `save_to_graph`, `load_from_graph`, `save_to_audit`, `load_from_audit`, `add_to_journal`). Import mid-file L79 (`ProjectLayout`) absorbé par `_state_core`.
- ✅ **Q2 — Pattern d'attachement serializer → Option A (Mixin)** : `StateSerializerMixin` + `StateAccessorsMixin` ; `class LoopState(AccessorsMixin, SerializerMixin, BaseModel)` — les 22 appels `state.<méthode>()` des callers restent intacts, zéro modification caller, shim trivial. Faits : aucun `to_dict` custom (Pydantic natif), 1 seul caller externe de serialisation (`lifecycle.py:L353 model_dump_json`).
- ✅ **Q3 — Effets de bord à l'import → Option A (3 modules)** : **pas** de `_state_init_effects.py` (sur-ingénierie — zéro `re.compile`/`basicConfig`/`open()` top-level) ; `logger = get_logger("state")` en top de `_state_core` ; import L79 remonté en tête de `_state_core`.
- ✅ **Q4 — Séquençage → reprise macro Q2 Option A** : `state.py` extrait **en premier** du Lot 1 (BR=78), séquence stricte Beachhead, un worker à la fois, Lot 3 gelé.
- ✅ **Q5 — Rollback → reprise macro Q3 Option A** : revert Git immédiat en cas d'échec smoke check, 0 FAIL strict, **arbitrage humain obligatoire** (BR=78 ≥ 20).

---

## Règles d'affaires

- **Singleton d'état unique** : l'instance `LoopState` doit être créée exactement une seule fois dans `src/state/__init__.py` — toute instanciation locale dans un sous-module du package est interdite (protocole §3.2).
- **Plafond modulaire absolu** : chaque sous-module extrait du monolithe doit rester sous 300 lignes et 15 Ko (ADR-0202 / RULE-AST-01).
- **Rétrocompatibilité stricte des callers** : les 78 fichiers appelants ne sont jamais modifiés — le shim de ré-export `src/state.py` doit rendre tout import historique résoluble sans `ImportError`.
- **Rollback borné BR ≥ 20** : en cas d'échec du smoke check, le revert Git est immédiat mais l'arbitrage humain est obligatoire avant toute action (seuil macro Q3).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Extraction Modulaire Singleton (Q1/Q2)
- [ ] Package `src/state/` créé avec `_state_core.py`, `_state_accessors.py`, `_state_serializer.py` — chacun ≤ 300 L / 15 Ko
- [ ] Mixins `StateAccessorsMixin` + `StateSerializerMixin` attachés à `LoopState` — API `state.<méthode>()` intacte pour les 78 callers
- [ ] Instance singleton unique créée uniquement dans `src/state/__init__.py` (audit AST : zéro `ProjectState()` local)

#### 2. Rétrocompatibilité & Non-Régression
- [ ] Shim `src/state.py` résout `from src.state import *` sans `ImportError` (78 callers inchangés)
- [ ] Check fumée vert + `pytest tests/ -x -q` : N_après PASS ≥ N_avant PASS, 0 FAIL
- [ ] Rollback borné BR ≥ 20 : échec smoke → revert Git immédiat sous arbitrage humain obligatoire

### Admission of Limits
- Avertissements rubber-duck génériques (timeout réseau, expiration de session, saisie extrême) hors domaine : composant headless sans UI ni API distante — résilience locale couverte par les 4 piliers Gherkin.

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : refactoring modulaire interne de `src/state.py` — **aucune route HTTP n'est consommée ni exposée**. Toute route découverte en cours d'implémentation fera l'objet d'une question ouverte `OQ-173` avec la mention `[API de soumission à définir]` — jamais inventée (Zéro Fausse Route, AGENTS.md).

| Contrat | Engagement |
|:---|:---|
| `from src.state import *` (shim) | Rétrocompatibilité 78 callers, zéro modification caller |
| `src/state/__init__.py` | Instance singleton unique `LoopState` |
| `code-check --file` sous-modules | ≤ 300 L / 15 Ko each (RULE-AST-01 PASS) |

---

## Scénarios de test

### Scénarios de test (Gherkin 4 Piliers)

#### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Extraction modulaire conforme au contrat Singleton
  Étant donné le monolithe "src/state.py" de 770 lignes avec 78 callers
  Quand le worker crée le package "src/state/" avec "_state_core", "_state_accessors", "_state_serializer" et le shim de ré-export
  Alors chaque sous-module pèse moins de 300 lignes et passe "code-check --file"
  Et l'import "from src.state import *" n'élève aucune erreur
  Et la suite de tests obtient N_après PASS supérieur ou égal à N_avant PASS avec 0 FAIL
  Et l'audit AST confirme zéro instanciation de "LoopState()" hors de "src/state/__init__.py"
```

#### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Échec du smoke check déclenche le rollback sous arbitrage humain
  Étant donné un échec du smoke check post-extraction sur les 78 callers
  Quand le résultat du check fumée revient en échec
  Alors le rollback s'exécute par revert Git immédiat de la branche d'extraction
  Et l'arbitrage humain est obligatoire avant tout revert car le blast radius vaut 78
  Et aucun merge n'est autorisé tant que 0 FAIL strict n'est pas atteint
  Et une instanciation locale de "LoopState" dans un sous-module bloque le merge via l'audit AST
```

#### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Instance unique préservée malgré imports multiples et effets de bord d'import
  Étant donné l'import simultané du shim par les 78 callers existants
  Quand le package "src/state" est chargé une première fois
  Alors l'instance "LoopState" reste unique car elle n'est créée qu'une seule fois dans "__init__.py"
  Et les mixins "StateAccessorsMixin" et "StateSerializerMixin" partagent le même "self" BaseModel
  Et l'import mid-file de la ligne 79 est remonté en tête de "_state_core"
  Et aucun appel concurrent "state.checkpoint()" et "state.save_to_audit()" ne provoque de course sur l'état
```

#### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Transparence totale pour le développeur consommateur
  Étant donné un développeur qui importe "from src.state import LoopState, LoopPhase, StoryStatus, ProjectLayout"
  Quand le refactoring est livré
  Alors tous les symboles historiques restent accessibles via le shim
  Et le logger "get_logger(\"state\")" conserve son canal unique sans double configuration
  Et "code-check --all" ne remonte plus RULE-AST-01 sur "src/state.py"
  Et la trace d'extraction est consignée dans "memory/plan/implementation_plan_MLOOP-173-BE.md"
```
