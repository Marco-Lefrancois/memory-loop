---
id: MLOOP-175-BE
jira_key: ''
epic_key: EPIC-17-MODULAR-REFACTORING
type: refactor
title: Extraction Modulaire de src/commands/_registry.py — Registre Déclaratif CLI
  (BR=3, 2028L)
origin: SPEC_SLICING
source_ref: 'EPIC-17 · epic17_prioritization_matrix.md · Rang #15 BR · OQ-171-04 zéro
  dérogation'
macro_size: M
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-172-BE
created_at: '2026-09-23'
grilled_at: '2026-09-23'
grill_decisions_ref: micro-grill 175 Q1-Q5 (Q1 micro B, Q2/Q3/Q4 pré-résolus Search-Before-Ask,
  Q5 reprise macro Q2)
approved_at: '2026-09-23'
approved_by: humain (go explicite batch APPROVE 173/174/175/176/178/179)
ttl_cycles: 4
---

# Extraction Modulaire de src/commands/_registry.py — Registre Déclaratif CLI (BR=3, 2028L)

## 1. Intention Métier (User Story)

**En tant qu'** ingénieur du framework mLoop,
**je veux** découper `src/commands/_registry.py` (2028 L, 73.1 Ko, BR=3) en sous-registres partiels par domaine agrégés dans un `__init__.py`, en appliquant le cas spécial §3.1 du protocole d'extraction,
**afin de** résorber la violation RULE-AST-01 la plus volumineuse du codebase (2028 L, soit 6,7× le plafond) sans briser la découverte automatique des commandes CLI ni introduire d'import circulaire.

---

## 2. Origine & Cadrage Avant-Projet

- **Document Source** : `memory/evidence/epic17_prioritization_matrix.md` (Réf : Rang #15, BR=3, Lot 1, 73.1 Ko) · Arbitrage OQ-171-04 : **zéro dérogation, `_registry.py` inclus**
- **Protocole SSOT** : `standards/protocols/MODULAR_EXTRACTION_PROTOCOL.md` — **Cas spécial §3.1 Registres déclaratifs**
- **Obligation ADR-0370** : toute modification de `_registry.py` ou de ses sous-registres après découpe doit être immédiatement suivie de `python src/swarm.py guide --sync`.
- **Hypothèse de Chiffrage Retenue** : Découpe en 5 registres partiels par phase CLI (`_reg_ingest`, `_reg_plan`, `_reg_build`, `_reg_validate`, `_reg_ship`) + `__init__.py` agrégateur ; BR=3 callers, risque maîtrisé si import circulaire évité.
- **Enveloppe Macro Estimée** : M (fourchette de 1 à 2 jours)

---

## 3. Périmètre Sommaire

### In-Scope (Macro)
- Lecture et cartographie de `src/commands/_registry.py` (2028 L, 73.1 Ko) : classification des commandes par phase CLI (Ingest / Plan / Build / Validate / Ship / Transverse).
- Création du package `src/commands/_registry/` avec sous-registres partiels par domaine, chacun ≤ 300 L / 15 Ko.
- `__init__.py` agrégateur exposant `ALL_COMMANDS = {**INGEST_COMMANDS, **PLAN_COMMANDS, ...}` — point d'entrée unique du dispatcher.
- Prévention stricte de l'**import circulaire §3.1** : aucun sous-registre n'importe le dispatcher parent.
- Shim de ré-export `src/commands/_registry.py` pour rétrocompatibilité des 3 callers.
- Exécution de `python src/swarm.py guide --sync` après toute modification (ADR-0370).
- Check fumée imports + suite tests verte + parité guide CLI.

### Out-of-Scope (Macro)
- Modification des handlers CLI associés aux commandes (portée strictement déclarative).
- Ajout ou suppression de commandes du registre (hors périmètre de ce récit de refactoring).
- Autres fichiers Lot 1 (`state.py`, `lifecycle.py`) — MLOOP-173-BE et MLOOP-174-BE.

---

## 4. Critères de Succès Préliminaires

- [ ] Chaque sous-registre du package `src/commands/_registry/` passe `code-check --file` : ≤ 300 L, ≤ 15 Ko.
- [ ] `__init__.py` agrège toutes les commandes sans import circulaire : `python -c "from src.commands._registry import COMMANDS"` — succès.
- [ ] Shim `src/commands/_registry.py` opérationnel : les 3 callers fonctionnent sans modification.
- [ ] `python src/swarm.py guide --sync` exécuté post-modification : parité 100 % guide CLI SSOT (Vibe-Check 15).
- [ ] Suite tests inchangée : `pytest tests/ -x -q` — N_après ≥ N_avant PASS, 0 FAIL.
- [ ] Plan archivé sous `memory/plan/implementation_plan_MLOOP-175-BE.md` avec checklist §4 complétée.

---

## 5. Décisions Grill-Me 1:1 (Frontière Épuisée 2026-09-23)

> [!DONE]
> *Session contradictoire 1:1 clôturée — 5/5 questions tranchées (Q1 micro ici ; Q2/Q3/Q4 pré-résolus Search-Before-Ask ; Q5 reprise macro Q2).*
> *Récit éligible conversion Palier 2 après validation wikifix/rubber-duck et approbation humaine.*

- ✅ **Q1 — Granularité des domaines → Option B (7 domaines agrégés)** : hypothèse « 5 phases CLI » de l'ébauche **réfétée par F3** (22 sections thématiques réelles, Analyse = 27 commandes / 386L > 300L). Découpe retenue : regroupement des 22 sections en **~7 `_reg_*.py` ≤300L**, **Analyse splité en 2** (seule section >300L) : `_reg_project` / `_reg_analysis_core` / `_reg_analysis_ext` / `_reg_pipelines_arch` / `_reg_validate_tool` / `_reg_export_skill` / `_reg_runtime_ops` + `__init__.py` agrégateur. Sections existantes conservées comme sous-commentaires. Doublons F2 (`dream`/`story-clean`/`drawdb` ×2) tranchés « dernier gagne » = comportement Python dict préservé.
- ✅ **Q2 — Dispatcher actuel → pré-résolu Search-Before-Ask (F5)** : point d'entrée **`COMMANDS` conservé tel quel** (zéro rename → zéro modification des 3 callers : `router.py`, `guide_generator.py`, `calibrate.py`). Le shim doit exposer `COMMANDS` comme attribut de module **et** survivre à `importlib.reload(reg_mod)` (router L81). `ALL_COMMANDS` du protocole §3.1 = exemple, pas l'entrée réelle.
- ✅ **Q3 — Import circulaire latent → pré-résolu Search-Before-Ask (F4)** : **nul** — seul import du fichier = `from src.core.worker_runtimes import WORKER_RUNTIMES` **lazy dans une fonction** (L21) ; **aucun handler n'importe `_registry`**. Pattern §3.1 « mauvais » inapplicable ici.
- ✅ **Q4 — `guide --sync` systématique → pré-résolu ADR-0370** : exécuté **une fois en fin de story** avant harvest (pas à chaque commit intermédiaire WIP sur branche) ; vibe-check 15 (contrôle 15ᵉ) couvre toute dérive résiduelle.
- ✅ **Q5 — Volume et ordre de découpe → reprise macro Q2 Option A** : position **5/5** (dernier du Lot 1 Beachhead `state(78) → db(20) → sync(10) → lifecycle(8) → _registry(3)`), un worker à la fois, smoke check vert entre chaque ; BR=3 < 20 → **autonomie worker** (macro Q3).

---

## Règles d'affaires

- **Plafond modulaire absolu** : chaque sous-registre de `src/commands/_registry/` doit rester sous 300 lignes et 15 Ko (ADR-0202 / RULE-AST-01).
- **Entrée `COMMANDS` stable** : le point d'entrée du dispatcher reste `COMMANDS` (pas `ALL_COMMANDS`) — zéro renommage, zéro modification des 3 callers existants.
- **Zéro import circulaire** : aucun sous-registre n'importe le dispatcher parent ni les handlers CLI (F4 : seul import = `worker_runtimes` lazy).
- **Parité guide CLI (ADR-0370)** : `python src/swarm.py guide --sync` exécuté une fois en fin de story avant harvest — parité 100 % avec `CLI_PIPELINE_GUIDE.md`.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Découpe Registre 7 Domaines (Q1-B)
- [ ] Package `src/commands/_registry/` créé : `_reg_project`, `_reg_analysis_core`, `_reg_analysis_ext`, `_reg_pipelines_arch`, `_reg_validate_tool`, `_reg_export_skill`, `_reg_runtime_ops` + `__init__.py` — chacun ≤ 300 L / 15 Ko
- [ ] Point d'entrée `COMMANDS` conservé tel quel (zéro rename) — 3 callers (`router.py`, `guide_generator.py`, `calibrate.py`) inchangés
- [ ] `importlib.reload(reg_mod)` survivant (router L81) : attribut `COMMANDS` toujours accessible après reload

#### 2. Zéro Import Circulaire & Parité Guide (Q3/Q4)
- [ ] Aucun sous-registre n'importe le dispatcher parent ni les handlers CLI (F4 confirmé)
- [ ] `python src/swarm.py guide --sync` exécuté une fois en fin de story — parité 100 % `CLI_PIPELINE_GUIDE.md` (ADR-0370, Vibe-Check 15)
- [ ] Suite tests inchangée : `pytest tests/ -x -q` — N_après ≥ N_avant PASS, 0 FAIL

### Admission of Limits
- Avertissements rubber-duck génériques (timeout réseau, expiration de session, saisie extrême) hors domaine : registre déclaratif CLI headless — couvert par les 4 piliers Gherkin.

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : refactoring modulaire interne de `src/commands/_registry.py` — **aucune route HTTP n'est consommée ni exposée**. Toute route découverte en cours d'implémentation fera l'objet d'une question ouverte `OQ-175` avec la mention `[API de soumission à définir]` — jamais inventée (Zéro Fausse Route, AGENTS.md).

| Contrat | Engagement |
|:---|:---|
| `from src.commands._registry import COMMANDS` | Entrée dispatcher stable, 122 clés uniques |
| `python src/swarm.py guide --sync` | Parité guide CLI 100 % post-extraction (ADR-0370) |
| `code-check --file` sous-registres | ≤ 300 L / 15 Ko each (RULE-AST-01 PASS) |

---

## Scénarios de test

### Pilier 1 — Nominal (Happy path)
```gherkin
Scénario : Découpage modulaire transparent du registre CLI
  Étant donné le package "src/commands/_registry/" subdivisé en 7 sous-registres <= 300 lignes
  Quand un caller importe "from src.commands._registry import COMMANDS"
  Alors les 122 clés uniques de commandes sont résolues sans régression ni avertissement
```

### Pilier 2 — Exceptions (Cas d'erreur)
```gherkin
Scénario : Détection d'une commande manquante après extraction
  Étant donné un sous-registre partiel qui omet une commande vitale
  Quand le dispatcher construit le parser argparse
  Alors le contrôle "vital_commands" de router.py déclenche un reload défensif et log l'erreur
```

### Pilier 3 — Résilience (Réseau / Timeout / Mode dégradé)
```gherkin
Scénario : Recharge dynamique du registre sous accès concurrent
  Étant donné "importlib.reload(reg_mod)" appelé par router.py en cas de commande vitale manquante
  Quand le module "src.commands._registry" est rechargé
  Alors l'attribut "COMMANDS" reste accessible et le dict est reconstruit sans ImportError
```

### Pilier 4 — UX / Accessibilité / État vide
```gherkin
Scénario : Parité du guide CLI après extraction
  Étant donné le registre découpé en 7 sous-registres avec "COMMANDS" agrégé
  Quand "python src/swarm.py guide --sync" régénère le guide
  Alors "CLI_PIPELINE_GUIDE.md" est en parité 100 % avec les 122 commandes actives
```
