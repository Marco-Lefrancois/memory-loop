---
story_id: MLOOP-163-BE
jira_key: ''
dossier_status: CURRENT
last_verified_at: "2026-09-22T12:43:27Z"
ssot_source: src/pipelines/
sources_hashes:
  src/pipelines/vibe_check.py: "7252DC0596127934"
---

# 📂 Dossier de Preuves Documentaires & Cadrage SSOT — MLOOP-163-BE

**Titre Métier** : Contrôle de Pré-Vol d'Intégrité des Directives Projet et Sémantique Tri-État du Score
**Identifiant Story** : `MLOOP-163-BE`
**Clé Jira Officielle** : *(temporaire — framework interne)*
**Date d'Extraction & Cadrage** : 2026-09-22
**Auditeur mLoop** : Agentic Pair Programmer

> **Nature framework** : SSOT = le pipeline du guardrail de pré-vol (`src/pipelines/vibe_check.py`). Grounding par inspection AST réelle du fichier (743 lignes).

---

## 🧭 1. Sources Physiques & Matrice de Vérité

* 📜 **Pipeline guardrail** : `src/pipelines/vibe_check.py` (sha256 `7252DC05...`, 743 lignes) — fonction `run_vibe_check` (L129), 34 callers (`project_core.py`), 10 fichiers de tests.

### 1.1 Hiérarchie de Vérité
1. **Niveau 1** : Le code réel de `run_vibe_check` et son calcul de verdict.

---

## 🔬 2. Faits Extraits & Verbatims (Passage-Level Grounding — inspection code réelle)

| # | Source (fichier:lignes) | Verbatim / Constat | Fait établi |
| :---: | :--- | :--- | :--- |
| **F-01** | `vibe_check.py:712-713` | `passed_count = sum(1 for c in checks if c["status"] == "PASS")` ; `total_count = len(checks)` | Le score ne compte QUE les PASS ; WARNING est exclu du numérateur. |
| **F-02** | `vibe_check.py:723` | `is_valid = passed_count == total_count` | **Bug latent confirmé** : un WARNING fait chuter le score sous total → invalide le verdict. C'est la contrainte technique de RM-004. |
| **F-03** | `vibe_check.py:629-653` (Check 17) | Le Check 17 QA émet déjà `"status": "WARNING"` avec intention passive. | Précédent existant : un check WARNING passif est déjà voulu mais mal traité par le calcul actuel. |
| **F-04** | `vibe_check.py:156` + append pattern | `checks = []` puis `checks.append({...})` séquentiel ; checks numérotés 1-17 puis 19 (18 sauté). | Point d'insertion du Check 20 : après le Check 19 (L710), avant `passed_count` (L712). |
| **F-05** | Balayage cross-projets (constaté) | Seul `BoireFrere_Segment2` a `directives/tech.md`+`business.md` ; 7 autres projets ne l'ont pas. | Conditionnalité obligatoire : absence de `directives/` → PASS, sinon casse 7 projets. |

---

## 🗄️ 3. Périmètre Structurel (Framework)

Artefact modifié : `src/pipelines/vibe_check.py` (Check 20 ajouté L~711 + correctif calcul `is_valid` tri-état). Blast radius : 34 callers + 10 fichiers de tests (réalignés au récit 164).

---

## 🎯 4. Contrats Déclaratifs Cibles

Aucun endpoint REST. Contrat = fonction interne. Signature de sortie inchangée (`dict` avec `status`, `checks`, `score`, `lifecycle_mode`, `stage`) ; seule la sémantique de `status` évolue (tri-état).

---

## 🏁 5. Évaluation de la Frontière Active

* **Arbitrages retenus** : D1 (recalcul au fil de l'eau, pas de parité de score, RM-004 dans ce récit), D3 (WARNING seul).
* **Frontière** : ne rédige pas les tests (récit 164), n'ajoute pas le check d'ancrage visuel (récit 165).
* **Robustesse (ADR-0369)** : lecture fichiers en try/except + logger contextuel + encoding explicite, aucune ressource hors `with`.
* **Admission of Limits** : le correctif `is_valid` change la sémantique du verdict pour TOUS les projets — assumé (D1).
