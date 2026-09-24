# Protocole d'Extraction Modulaire v1
# MODULAR_EXTRACTION_PROTOCOL.md

> **Autorité** : EPIC-17-MODULAR-REFACTORING · ADR-0202 · ADR-0369 · ADR-0376  
> **Garde-fou** : [MLOOP-171-BE](../adr-system/README.md) — `src/pipelines/ast_delta_checker.py` + `MLOOP_SKIP_HOOKS`  
> **Issu du pilote** : MLOOP-170-BE (`vibe_check.py` 880L → package `src/pipelines/vibe_check/` <300L/module)  
> **Créé** : 2026-09-23 · **Statut** : ACTIVE

---

## 1. Objectif & Périmètre

Ce protocole définit la marche à suivre **déterministe et non-régressive** pour découper tout module Python dépassant le plafond ADR-0202 (≤300 L / 15 Ko) en sous-modules cohérents.

Il couvre :

1. **Le cas général** — découpe par famille de responsabilités (§2).
2. **Trois cas spéciaux avec contre-exemples** — registres déclaratifs, singletons d'état, effets de bord à l'import (§3).
3. **La checklist non-régression** — exigible à chaque lot (§4).
4. **Le lien vers le garde-fou anti-aggravation** MLOOP-171-BE (§5).
5. **La matrice de conformité Vibe-Check Phase 3** (§6).

---

## 2. Cas Général — Découpe par Famille de Responsabilités

> **Référence expérimentale** : `src/pipelines/vibe_check.py` 880 L → package `src/pipelines/vibe_check/` (7 modules, aucun >300 L).

### 2.1 Étapes obligatoires

```
Étape 0 — Diagnostic préalable
  python src/swarm.py code-check --all
  → Identifier le module cible (>300 L) et son Blast Radius (ast_import_count).
  → Archiver la liste des callers dans memory/plan/implementation_plan_<MODULE>_extraction.md §1.

Étape 1 — Cartographie des familles de responsabilités
  Lire le module entier.
  Regrouper les fonctions/classes en familles cohérentes (ex: sécurité, gouvernance, SSOT, agents).
  Chaque famille → un sous-module (_vc_security, _vc_governance, etc.).
  Contrainte : aucun sous-module >300 L / 15 Ko (ADR-0202, RULE-AST-01).

Étape 2 — Créer le package
  mkdir src/<chemin>/<module>/
  touch src/<chemin>/<module>/__init__.py  # shim de ré-export

Étape 3 — Déplacer les familles
  Pour chaque famille :
    a. Créer le sous-module <module>/_<famille>.py
    b. Y déplacer les symboles (fonctions/classes/constantes).
    c. Ajouter les imports manquants dans le sous-module.
    d. Mettre à jour __init__.py pour ré-exporter tous les symboles publics.

Étape 4 — Shim de ré-export (rétrocompatibilité callers)
  Le fichier source original (src/<chemin>/<module>.py) devient un shim 1-5 L :
    # shim de ré-export — rétrocompatibilité ADR-0202
    from src.<chemin>.<module> import *  # noqa: F401, F403
  Cela garantit que tous les callers existants (import module) continuent de fonctionner sans modification.

Étape 5 — Check fumée imports
  python -m src.pipelines.import_smoke_check --module src/<chemin>/<module>.py
  → Doit afficher : "✅ Aucun symbole non résolu détecté."
  → En cas d'échec : corriger avant de continuer.

Étape 6 — Suite de tests verte
  pytest tests/ -x -q
  → Zéro régression (le nombre de PASS ne doit pas diminuer).

Étape 7 — Contrôle de conformité post-extraction
  python src/swarm.py code-check --file src/<chemin>/<module>/__init__.py
  python src/swarm.py code-check --file src/<chemin>/<module>/_<famille>.py  # pour chaque sous-module
  → Tous doivent afficher PASS (≤300 L, ≤15 Ko).

Étape 8 — Archiver le plan et mettre à jour la matrice EPIC-17
  memory/plan/implementation_plan_<MODULE>_extraction.md : marquer DONE + résultats.
  memory/evidence/epic17_prioritization_matrix.md : mettre à jour le statut du module.
```

### 2.2 Garanties invariantes

| Garantie | Méthode de vérification |
|:---------|:------------------------|
| Rétrocompatibilité imports | Shim de ré-export + check fumée (§2.1 Étape 5) |
| Signature publique inchangée | `__all__` dans `__init__.py` + test import direct |
| Non-régression tests | `pytest tests/ -x -q` avant/après (zéro régression) |
| ADR-0202 (≤300 L / 15 Ko) | `code-check --file` sur chaque sous-module post-extraction |
| ADR-0369 (timeout, with, no except pass) | Review manuelle + check Python Senior (Vibe-Check 14) |

### 2.3 Shim de ré-export — patron standard

```python
# src/pipelines/<module>.py — shim de ré-export MLOOP-172-BE
# Ce fichier est maintenu pour la rétrocompatibilité (ADR-0202).
# Ne pas modifier : les symboles sont définis dans src/pipelines/<module>/.
from src.pipelines.<module> import *  # noqa: F401, F403
```

---

## 3. Cas Spéciaux (avec contre-exemples)

### 3.1 Registres Déclaratifs (`_registry.py`)

**Description** : Un registre déclaratif est un module qui contient la déclaration centralisée de toutes les commandes, plugins ou entrées d'un dispatcher. Exemple : `src/commands/_registry.py` (2028 L, BR=3).

**Risque** : La découpe naïve en registres partiels brise la découverte automatique si le dispatcher itère sur un seul point d'entrée. Un import circulaire peut également apparaître si les sous-registres importent le dispatcher qui les importe en retour.

**Pattern sûr** : Découpe en **registres partiels par domaine** avec agrégation explicite dans `__init__.py`.

```
_registry/
├── __init__.py          # agrège et ré-exporte TOUTES les commandes
├── _reg_ingest.py       # commandes Phase 1 (ingest, markitdown, svg-ocr…)
├── _reg_plan.py         # commandes Phase 2 (grill, plan, triage…)
├── _reg_build.py        # commandes Phase 3 (build, code-check, worker…)
├── _reg_validate.py     # commandes Phase 4 (qa, rubber-duck, sentinel…)
└── _reg_ship.py         # commandes Phase 5 (sync, jira_sync, guide…)
```

`__init__.py` :
```python
from src.commands._registry._reg_ingest import INGEST_COMMANDS
from src.commands._registry._reg_plan import PLAN_COMMANDS
# ... etc.
ALL_COMMANDS = {**INGEST_COMMANDS, **PLAN_COMMANDS, ...}
```

**Contre-exemple** ❌ — À NE PAS FAIRE :
```python
# _reg_plan.py — MAUVAIS : import circulaire
from src.commands._registry import dispatcher  # importe le parent qui importe _reg_plan !
```
Ce pattern provoque une `ImportError: cannot import name 'dispatcher' from partially initialized module`.

**Obligation ADR-0370** : Toute modification de `_registry.py` (ou de ses sous-registres après découpe) doit être suivie immédiatement de :
```bash
python src/swarm.py guide --sync
```

---

### 3.2 Singletons d'État (modules d'état partagé / cache process-global)

**Description** : Modules qui maintiennent un état partagé au niveau du processus via des variables globales ou des instances de classe uniques. Exemple : `src/state.py` (770 L, BR=78).

**Risque** : Si le singleton est instancié dans plusieurs sous-modules, chaque import crée une instance séparée, rompant le contrat de partage d'état. Le BR=78 signifie que 78 fichiers importent `state.py` — une découpe mal faite brise immédiatement la cohérence globale.

**Pattern sûr** : Isoler le **noyau d'état** (données + getters/setters primitifs) dans un sous-module `_state_core.py`, et les **accesseurs de haut niveau** dans `_state_accessors.py`. Le shim `state.py` ré-exporte le tout.

```
state/
├── __init__.py          # shim + ré-export de l'instance unique
├── _state_core.py       # classe ProjectState, champs, __init__
├── _state_accessors.py  # méthodes get_*/set_* de haut niveau
└── _state_serializer.py # to_dict(), from_dict(), sauvegarde JSON
```

**Règle critique** : L'instance singleton doit être créée **une seule fois** dans `__init__.py` et importée partout :
```python
# state/__init__.py
from src.state._state_core import ProjectState
_GLOBAL_STATE: ProjectState = ProjectState()  # instance unique

from src.state._state_accessors import *  # bind sur _GLOBAL_STATE
```

**Contre-exemple** ❌ — À NE PAS FAIRE :
```python
# _state_accessors.py — MAUVAIS : instanciation dupliquée
from src.state._state_core import ProjectState
_LOCAL_STATE = ProjectState()  # crée UNE DEUXIÈME instance — désynchronisation garantie
```
Toute écriture via `_state_accessors` sera invisible pour les 78 callers qui lisent via `state.__init__`.

---

### 3.3 Effets de Bord à l'Import

**Description** : Modules qui exécutent du code au moment de l'import : configuration du logging, compilation de regex globales, ouverture de fichiers, connexions réseau. Exemple : tout module contenant `logging.basicConfig(...)` ou `_PATTERNS = [re.compile(p) for p in ...]` au niveau module.

**Risque** : La découpe déplace les effets de bord dans plusieurs sous-modules. Si l'ordre d'import change, les effets de bord s'appliquent dans un ordre différent, causant des comportements non déterministes (logger écrasé, regex recompilées, fichier ouvert deux fois).

**Pattern sûr** : Regrouper **tous les effets de bord** dans un sous-module `_<module>_init_effects.py` importé en **premier** dans `__init__.py`.

```python
# _vc_init_effects.py — effets de bord à l'import (MLOOP-172-BE)
import re
import logging

# Compilation des patterns (coût unique au démarrage)
_VAGUE_PATTERN = re.compile(
    r"(?<!double-clic\s)\b(?:rapide|facile|approprié)\b", re.IGNORECASE
)

# Configuration du logger module (une seule fois)
_MODULE_LOGGER = logging.getLogger("pipelines.vibe_check")
```

```python
# __init__.py — import des effets de bord EN PREMIER
from src.pipelines.vibe_check._vc_init_effects import _VAGUE_PATTERN, _MODULE_LOGGER
from src.pipelines.vibe_check._vc_governance import check_13_phase_gate
# ...
```

**Contre-exemple** ❌ — À NE PAS FAIRE :
```python
# _vc_governance.py — MAUVAIS : reconfiguration du logging dans un sous-module
import logging
logging.basicConfig(level=logging.DEBUG)  # écrase la config globale à chaque import !
```
Ce pattern réinitialise le logger racine à chaque import du sous-module, écrasant la configuration centralisée (souvent définie dans `src/utils/logger.py`).

**Contre-exemple ❌ — Ouverture de fichier à l'import** :
```python
# _config.py — MAUVAIS
CONFIG = json.load(open("config.json"))  # ouvre un fichier à l'import, sans context manager
```
Utiliser à la place un chargement paresseux (`lazy loading`) via une fonction :
```python
# _config.py — CORRECT (ADR-0369 : with + lazy)
_CONFIG_CACHE: dict | None = None

def get_config() -> dict:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        with open("config.json", encoding="utf-8") as f:
            _CONFIG_CACHE = json.load(f)
    return _CONFIG_CACHE
```

---

## 4. Checklist Non-Régression (exigible à chaque lot)

À compléter et archiver dans `memory/plan/implementation_plan_<MODULE>_extraction.md §5` avant tout merge/commit.

```
CHECKLIST NON-RÉGRESSION — Lot d'extraction <MODULE> (<date>)

PRÉ-EXTRACTION
[ ] code-check --file <module> : violations listées (baseline)
[ ] pytest tests/ -q --tb=no : N_avant PASS, 0 FAIL (baseline)
[ ] Callers identifiés via ast_import_count ou grep : liste dans §1

EXTRACTION
[ ] Sous-modules créés, chacun ≤300 L / ≤15 Ko (RULE-AST-01)
[ ] Shim de ré-export créé (src/<chemin>/<module>.py → from package import *)
[ ] __init__.py expose tous les symboles publics (même surface qu'avant)
[ ] Aucun import circulaire (python -c "import src.<chemin>.<module>" → no error)

POST-EXTRACTION
[ ] check fumée vert : python -m src.pipelines.import_smoke_check --module src/<chemin>/<module>.py
[ ] code-check --file sur chaque sous-module : PASS
[ ] pytest tests/ -q --tb=no : N_après PASS = N_avant (zéro régression)
[ ] Si _registry modifié : guide --sync exécuté (ADR-0370)
[ ] Plan archivé mis à jour : statut DONE + résultats
[ ] Matrice EPIC-17 mise à jour
[ ] MLOOP_SKIP_HOOKS non utilisé (ou audit enregistré dans mloop_skip_hooks_audit.log)
```

---

## 5. Garde-Fou Anti-Aggravation (MLOOP-171-BE)

Le protocole s'appuie sur le garde-fou implémenté dans MLOOP-171-BE pour empêcher toute ré-aggravation de la dette AST pendant les lots.

### 5.1 Mécanisme

| Composant | Rôle |
|:----------|:-----|
| `src/pipelines/ast_delta_checker.py` (297 L) | Hook Git pre-commit : bloque tout commit agrandissant un fichier déjà en dépassement |
| `standards/blueprints/git_pre_commit_hook.sh` | Shell hook appelant `python -m src.pipelines.ast_delta_checker` |
| `MLOOP_SKIP_HOOKS=1` | Bypass d'urgence — déclenche l'audit automatique dans `mloop_skip_hooks_audit.log` |

### 5.2 Règles du garde-fou

- **Fichier déjà >300 L en HEAD** : commit autorisé ssi `staged_lines ≤ head_lines` ET `staged_bytes ≤ head_bytes`.
- **Fichier conforme ou nouveau** : rejeté si >300 L ou >15 Ko.
- **Bypass MLOOP_SKIP_HOOKS** : tracé automatiquement (ISO-8601 UTC + user + raison). Tout bypass doit être justifié dans le plan d'extraction.

### 5.3 Matrice PASS/WARNING/FAIL (Vibe-Check Phase 3 — Check 22)

| Plan archivé | Fumée imports | Modifications en dépassement | Résultat Check 22 |
|:---:|:---:|:---:|:---:|
| ✅ Présent | ✅ Vert | Non | **PASS** |
| ✅ Présent | ⚠️ Non exécuté | Oui | **WARNING** |
| ✅ Présent | ❌ Rouge | Oui | **FAIL** |
| ❌ Absent | ✅ Vert | Non | **WARNING** |
| ❌ Absent | ❌ Rouge / Non exécuté | Oui | **FAIL** |
| ❌ Absent | ❌ Rouge / Non exécuté | Non | **WARNING** |

**Règle de synthèse** : FAIL si et seulement si (plan absent **ET** fumée rouge/non exécutée **ET** modifications en dépassement actif) **OU** (plan absent ET fumée rouge ET modifications en dépassement).

---

## 6. Éventuel Gabarit de Plan d'Extraction

Voir `standards/blueprints/modular_extraction_plan_template.md` pour le gabarit complet à utiliser dans `memory/plan/implementation_plan_<MODULE>_extraction.md`.

---

## 7. Références

| Référence | Lien |
|:----------|:-----|
| ADR-0202 — Plafond 300 L / 15 Ko | `standards/adr-system/` |
| ADR-0369 — Standards Python Senior | `standards/protocols/PYTHON_SENIOR_CODING_STANDARDS.md` |
| ADR-0370 — Anti-Drift Guide CLI | `standards/adr-system/` |
| ADR-0376 — Audit 360° 7 Couches | `standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md` |
| MLOOP-171-BE — Garde-fou anti-aggravation | `memory/evidence/MLOOP-171-BE_report.md` |
| Matrice EPIC-17 | `memory/evidence/epic17_prioritization_matrix.md` |
| Pilote MLOOP-170-BE | `memory/plan/implementation_plan_MLOOP-170-BE.md` |
