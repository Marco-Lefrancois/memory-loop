---
story_id: MLOOP-162-BE
jira_key: ''
dossier_status: CURRENT
last_verified_at: "2026-09-22T12:43:27Z"
ssot_source: .agents/skills/
sources_hashes:
  .agents/skills/grill/SKILL.md: "B8287A237B96E13A"
---

# 📂 Dossier de Preuves Documentaires & Cadrage SSOT — MLOOP-162-BE

**Titre Métier** : Renforcement de l'Étape Search-Before-Ask du Skill d'Entrevue par la Localisation SSOT
**Identifiant Story** : `MLOOP-162-BE`
**Clé Jira Officielle** : *(temporaire — framework interne)*
**Date d'Extraction & Cadrage** : 2026-09-22
**Auditeur mLoop** : Agentic Pair Programmer

> **Nature framework** : SSOT = la compétence portable elle-même (`.agents/skills/grill/SKILL.md`).

---

## 🧭 1. Sources Physiques & Matrice de Vérité

* 📜 **Compétence d'entrevue** : `.agents/skills/grill/SKILL.md` (sha256 `B8287A23...`, 83 lignes) — cible d'enrichissement de l'Étape 0.

### 1.1 Hiérarchie de Vérité
1. **Niveau 1** : Le fichier SKILL.md du skill grill (comportement opérationnel de l'agent).

---

## 🔬 2. Faits Extraits & Verbatims (Passage-Level Grounding)

| # | Source (fichier:section) | Verbatim | Fait établi |
| :---: | :--- | :--- | :--- |
| **F-01** | `grill/SKILL.md` — Étape 0 « Search-Before-Ask » | « Interroger l'index SQLite FTS5 […] et CONTEXT.md […]. Arbitrer Faits vs Décisions : si un fait est consigné dans la documentation […] interdiction absolue de poser la question à l'humain. » | L'Étape 0 impose déjà le fact-search mais **ne mentionne pas** la localisation du SSOT via `directives/`. C'est le gap exact. |
| **F-02** | `grill/SKILL.md` — Table Anti-Rationalisation | « Je vais griller chaque story sans faire de cadrage macro global → Conduit au syndrome du perroquet. Exécuter grill-project avant. » | Le skill connaît déjà la discipline de cadrage amont ; il faut y greffer la localisation SSOT. |
| **F-03** | Incident fondateur (session 22/09) | Brief de délégation pointant `docs/00-ingested/` au lieu de `docs/03-models/`. | Preuve empirique que l'absence de consigne de localisation SSOT produit des briefs non sourcés. |

---

## 🗄️ 3. Périmètre Structurel (Framework)

Artefact modifié : `.agents/skills/grill/SKILL.md` (Étape 0 enrichie). Aucune table de données.

---

## 🎯 4. Contrats Déclaratifs Cibles

Aucun endpoint REST. Contrat = présence, dans l'Étape 0, d'un ordre de recherche imposé (directives en tête) + interdiction de brief non sourcé.

---

## 🏁 5. Évaluation de la Frontière Active

* **Arbitrages retenus** : référence le protocole du récit 160 sans dupliquer son contenu.
* **Frontière** : ne touche pas au code du guardrail (récit 163), ne crée pas de nouveau skill (Zero-Bloat ADR-0362 : on bonifie l'existant).
* **Admission of Limits** : l'efficacité comportementale repose sur la lecture par l'agent ; complétée par le contrôle mécanique du récit 163.
