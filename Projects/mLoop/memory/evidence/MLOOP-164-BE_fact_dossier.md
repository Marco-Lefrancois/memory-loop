---
story_id: MLOOP-164-BE
jira_key: ''
dossier_status: CURRENT
last_verified_at: "2026-09-22T12:43:27Z"
ssot_source: tests/
sources_hashes:
  src/pipelines/vibe_check.py: "7252DC0596127934"
---

# 📂 Dossier de Preuves Documentaires & Cadrage SSOT — MLOOP-164-BE

**Titre Métier** : Suite de Tests du Contrôle des Directives et Réalignement sur la Sémantique Tri-État
**Identifiant Story** : `MLOOP-164-BE`
**Clé Jira Officielle** : *(temporaire — framework interne)*
**Date d'Extraction & Cadrage** : 2026-09-22
**Auditeur mLoop** : Agentic Pair Programmer

> **Nature framework** : SSOT = la suite de tests (`tests/`) et le comportement réel du guardrail après le récit 163.

---

## 🧭 1. Sources Physiques & Matrice de Vérité

* 📜 **Suite de tests du guardrail (existante)** : `tests/test_vibe_check_freshness.py`, `test_vibe_check_visual_contract.py`, `test_vibe_check_sow_granularity.py`, `test_vibe_check_phase_gate.py` (+6 autres) — constatés via blast radius de `run_vibe_check`.
* 📜 **Pipeline cible** : `src/pipelines/vibe_check.py` (sha256 `7252DC05...`) — comportement tri-état après récit 163.

### 1.1 Hiérarchie de Vérité
1. **Niveau 1** : Le comportement réel du guardrail (récit 163) ; les tests s'y alignent.

---

## 🔬 2. Faits Extraits & Verbatims (Passage-Level Grounding)

| # | Source (constat) | Verbatim / Constat | Fait établi |
| :---: | :--- | :--- | :--- |
| **F-01** | Blast radius `run_vibe_check` (codegraph) | 10 fichiers de tests dépendent de `run_vibe_check`. | Périmètre de réalignement = ces 10 fichiers, à auditer un par un. |
| **F-02** | `vibe_check.py:723` (ancien calcul) | `is_valid = passed_count == total_count` | Tout test asserting un statut global sur un scénario contenant un WARNING doit être réaligné sur la nouvelle règle tri-état. |
| **F-03** | Décision D1 (Grill 22/09) | Recalcul au fil de l'eau, pas de parité de score cross-projets. | L'exigence n'est PAS de préserver les anciens scores mais que `uv run pytest` reste vert après réalignement volontaire. |
| **F-04** | Check 15 (parité guide CLI, constaté L599) | Le guide CLI est auto-sync si des commandes changent. | RM-003 : aucune commande ajoutée (checks internes) → pas de `guide --sync` requis, à confirmer. |

---

## 🗄️ 3. Périmètre Structurel (Framework)

Artefacts : `tests/test_vibe_check_directives_ssot.py` (nouveau, 5 cas parametrize) + `[MODIFY]` des tests existants encodant l'ancienne sémantique. Aucune table de données.

---

## 🎯 4. Contrats Déclaratifs Cibles

Aucun endpoint REST. Contrat = `uv run pytest` intégralement vert + 5 cas paramétrés couverts.

---

## 🏁 5. Évaluation de la Frontière Active

* **Arbitrages retenus** : D1 — réalignement explicite `[MODIFY]`, pas de non-régression passive.
* **Frontière** : n'implémente pas le check (récit 163) ni le check d'ancrage visuel (récit 165, qui aura ses propres tests ou les partagera).
* **Admission of Limits** : la liste exacte des tests à réaligner sera figée à l'implémentation (dépend de l'état de `tests/` au moment du build).
