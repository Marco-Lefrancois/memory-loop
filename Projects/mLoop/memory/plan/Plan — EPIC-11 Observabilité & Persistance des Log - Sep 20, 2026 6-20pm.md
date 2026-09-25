---
created: 2026-09-20T22:20:58.444Z
source: plannotator
tags: [plannotator, memory-loop, epic-11, observabilit, persistance]
---

[[Plannotator Plans]]

# Plan — EPIC-11 : Observabilité & Persistance des Logs d'Erreurs (mLoop)

## Contexte factuel (vérifié dans le code, zéro invention)

| Fait établi | Preuve |
| :--- | :--- |
| Le logging mLoop est **console-only** — aucune persistance | `src/utils/logger.py:95` → `StreamHandler(sys.stderr)`, aucun `FileHandler` dans tout `src/` |
| Les erreurs capturées (`logger.warning/debug exc_info`) sont **perdues** après affichage | Pas de handler fichier ; niveau défaut `WARNING` (`logger.py:91`) |
| Adoption du logging **fragmentée** | 22 fichiers via `get_logger` centralisé vs 30 via `logging.getLogger(__name__)` brut |
| Dette d'observabilité massive | **256** occurrences de `print()` dans `src/` + **221** blocs `except` à auditer |
| La seule "mémoire d'erreurs" persistante = RHO | `memory/loop_mem.db` table `rho_memory` (base sémantique, pas un log) |
| EPIC-7 existe déjà (Observabilité Agentique) mais orienté **cockpit/agents**, pas **logs runtime** | `sprint_backlog.md` — EPIC-7-AGENTIC-OBSERVABILITY |

**Incohérence de conception constatée** : `logger.py` a été bâti (ADR-0369) pour *« éliminer les except:pass silencieux en capturant les erreurs avec contexte »* — mais sans `FileHandler`, ces erreurs ne sont jamais archivées. En cas de crash non supervisé (worker background, hook, sync nocturne), la trace est irrécupérable.

---

## Positionnement & gouvernance

- **Nouvel EPIC : `EPIC-11-ERROR-OBSERVABILITY`** (le suivant après EPIC-10). Distinct et complémentaire d'EPIC-7 : EPIC-7 = observabilité *agentique/cockpit* ; EPIC-11 = *logs d'erreurs runtime & post-mortem*.
- **Herméticité** : travail 100 % sur le framework mLoop (`src/utils/logger.py`, `src/`), auto-développement autorisé (`C:\Memory Loop\src`).
- **⚠️ Contrainte de phase (ADR-0375/0378)** : ce plan crée **l'EPIC + des ébauches `DRAFT` (`grill_me: PENDING`)** uniquement. **Aucune story ne passera `READY_FOR_DEV`** sans Grill-Me 1:1 + 4 Piliers Gherkin + DoR 6/6 + approbation humaine.
- **⚠️ Audit 7 couches (ADR-0376)** : `logger.py` est un composant cœur transverse (utilisé par 52 fichiers). Toute implémentation exigera un plan zéro-blindspot dédié au moment du BUILD — hors de ce plan de cadrage.

---

## Périmètre proposé de l'EPIC-11 (ébauches DRAFT)

| Récit | Composant | Objet | Priorité |
| :--- | :--- | :--- | :---: |
| **MLOOP-110-BE** | Utils/Logger | `FileHandler` rotatif optionnel (`RotatingFileHandler` → `memory/logs/mloop_errors.log`), activable par env var (`MLOOP_LOG_FILE`), rétention bornée. Cœur de l'EPIC. | Haute |
| **MLOOP-111-BE** | Utils/Logger | Convergence du logging : migrer les 30 `logging.getLogger(__name__)` bruts vers `get_logger` centralisé (contexte projet/story/phase homogène). | Moyenne |
| **MLOOP-112-BE** | Src (transverse) | Éradication des 256 `print()` → logging structuré (audité par un contrôle Vibe-Check dédié anti-régression). | Moyenne |
| **MLOOP-113-BE** | Resilience/Errors | Audit des 221 blocs `except` : garantir zéro silence nu (log contextuel `exc_info=True`) + capture systématique vers le log fichier. | Moyenne |
| **MLOOP-114-FE** | Cockpit/UI | Onglet "Journal d'Erreurs" dans le cockpit web : lecture, filtrage par niveau/module, corrélation avec la mémoire RHO. Dépend de MLOOP-110. | Basse |

> Note anti-scope-creep : MLOOP-114 (visualisation) est optionnel et dépendant ; il peut être tombstoné si jugé redondant avec le cockpit EPIC-7.

---

## Fichiers impactés par ce plan de cadrage (écriture backlog uniquement)

1. `[MODIFY]` `Projects/mLoop/backlog/sprint_backlog.md` — ajout du bloc `## Épopée : EPIC-11-ERROR-OBSERVABILITY` + 5 lignes de récits au statut `DRAFT`.
2. `[NEW]` `Projects/mLoop/backlog/stories/MLOOP-110-BE.md` → `MLOOP-114-FE.md` — 5 ébauches au gabarit **`story_draft_template.md`** (Palier 1, `status: DRAFT`, `grill_me: PENDING`).
3. `[NONE]` Aucune modification de `src/` dans ce plan (le BUILD viendra après Grill-Me + plan zéro-blindspot séparé).

---

## Séquence d'exécution proposée

1. Charger le skill `plan` (découpage INVEST) + lire `standards/blueprints/story_draft_template.md`.
2. Écrire le bloc EPIC-11 dans `sprint_backlog.md`.
3. Générer les 5 ébauches `DRAFT` (gabarit Palier 1).
4. `python src/swarm.py sync --project mLoop` (fraîcheur index FTS5 + graphe).
5. **STOP** — restituer l'EPIC créé. Le Grill-Me (promotion vers `READY_FOR_DEV`) fera l'objet d'une session ultérieure, récit par récit.

---

## Questions ouvertes à trancher avant écriture

1. **Numérotation** : `EPIC-11` + récits `MLOOP-110→114` — OK, ou vous préférez rattacher ces récits à l'EPIC-7 existant (Observabilité) plutôt qu'un nouvel EPIC ?
2. **Périmètre** : les 5 récits proposés vous conviennent-ils, ou on réduit au strict essentiel (MLOOP-110 `FileHandler` seul comme MVP) ?
3. **MLOOP-114 (cockpit)** : à inclure en DRAFT, ou à écarter d'emblée (risque de doublon avec EPIC-7) ?