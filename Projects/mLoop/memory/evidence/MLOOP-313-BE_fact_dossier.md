# 📋 Fact Dossier — `MLOOP-313-BE` : Harmonisation Multi-Couches des Consommateurs (_sync_backlog, wikifix, scratch_prune, Dashboard)

---

- **Récit Cible** : `MLOOP-313-BE`
- **Épopée** : `EPIC-31-FSM-ANTI-HARDCODING-AND-LIFECYCLE-HARMONIZATION`
- **Composant** : `Pipelines/Sync` (`_sync_backlog_parser.py`, `wikifix_core.py`, `scratch_prune.py`, `dashboard/routers/backlog.py`)
- **Établi le** : 2026-09-25 — Session Macro-Grill VALIDÉE (PO Marco)
- **Autorité** : PO mLoop (Marco) / Architecte Framework

---

## ⚖️ 1. Matrice des Décisions Validées en Session Macro-Grill

| # | Question Grillée | Option Retenue | Justification & Impact Technique |
| :- | :--- | :---: | :--- |
| **Q-Sync** | Prise en compte des nouveaux statuts dans l'expression régulière du backlog | **Option A (Ordonnancement longs d'abord)** | Intégration de `READY_FOR_QA`, `QA_CERTIFIED`, `READY_TO_SHIP`, `DONE_TESTED`, `SHIPPED` dans `STATUS_VOCAB_RE` avec tri par longueur décroissante pour éviter toute troncature par regex. |
| **Q-Purge** | Déclenchement de la purge des artefacts scratch | **Option A (Statut terminal `DONE`)** | `scratch_prune.py` déclenche le nettoyage des brouillons de session dès que le récit atteint `DONE` ou `SHIPPED`. |

---

## 🔍 2. Extraits Sourcés & Passage-Level Grounding (Vérité Terrain)

### Extrait 1 — `src/pipelines/sync/_sync_backlog_parser.py` (Ligne 46) : Regex de capture de statut
```python
STATUS_VOCAB_RE = re.compile(
    r"\b(READY_FOR_GROOMING|READY_FOR_DEV|IN_ANALYZE|DONE_TESTED|IN_REVIEW|IN_DEV|IN_QA|DRAFT|BACKLOG|OPEN|ACCEPTED|DONE)\b",
    re.IGNORECASE,
)
```
* **Fait Établi** : L'expression régulière omet `READY_FOR_QA`, `QA_CERTIFIED`, `READY_TO_SHIP` et `SHIPPED`. Sans cette mise à jour, un statut `READY_FOR_QA` dans le Markdown serait tronqué ou ignoré par `parse_backlog_status_maps()`.

### Extrait 2 — `src/pipelines/wikifix_core.py` (Lignes 101–130, 202) : Gardes de statut tolérées
```python
_tolerated = re.compile(r"^(DONE|DONE_TESTED|SHIPPED|ACCEPTED|IN_DEV|IN_QA)$")
```
* **Fait Établi** : WikiFix doit tolérer `READY_FOR_QA` et `QA_CERTIFIED` pour ne pas lever de faux positifs bloquants lors de l'audit des récits en cours d'assurance qualité.

---

## 🚪 3. Frontière Active & Admission of Limits

- **In-Scope MLOOP-313-BE** :
  - `_sync_backlog_parser.py` : Regex enrichie et ordonnée.
  - `wikifix_core.py` : Gardes de statut et tolérances INVEST.
  - `scratch_prune.py` : `terminal_statuses` enrichi de `DONE`.
  - `dashboard/routers/backlog.py` : `STATUS_ORDER` adapté aux 5 phases.
- **Out-of-Scope** :
  - Définition Pydantic `_state_core.py` (couverte par `MLOOP-310-BE`).
  - Validation E2E globale (`MLOOP-314-FULL`).
