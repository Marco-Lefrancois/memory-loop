---
story_id: MLOOP-165-BE
jira_key: ''
dossier_status: CURRENT
last_verified_at: "2026-09-22T12:43:27Z"
ssot_source: src/pipelines/
sources_hashes:
  src/pipelines/vibe_check.py: "7252DC0596127934"
  AGENTS.md: "3EF613F235944A4C"
  Projects/BoireFrere_Segment2/directives/business.md: "06919FCE5B076F8E"
---

# 📂 Dossier de Preuves Documentaires & Cadrage SSOT — MLOOP-165-BE

**Titre Métier** : Contrôle d'Ancrage Visuel des Récits Frontend selon le Principe du Contrat Visuel Premier
**Identifiant Story** : `MLOOP-165-BE`
**Clé Jira Officielle** : *(temporaire — framework interne)*
**Date d'Extraction & Cadrage** : 2026-09-22
**Auditeur mLoop** : Agentic Pair Programmer

> **Nature framework** : SSOT = le pipeline guardrail (`src/pipelines/vibe_check.py`, Check 10 existant à étendre) + le principe du Contrat Visuel en charte racine.

---

## 🧭 1. Sources Physiques & Matrice de Vérité

* 📜 **Pipeline guardrail (Check 10 existant)** : `src/pipelines/vibe_check.py:357-398` — « Contrat Visuel Lisible (Maquettes SSOT) » (détection OCR des maquettes vectorisées).
* 📜 **Charte racine** : `AGENTS.md` (sha256 `3EF613F2...`) — interdiction « Violation du Contrat Visuel (Maquettes = SSOT) ».
* 📜 **Preuve d'universalité** : `Projects/BoireFrere_Segment2/directives/business.md:26` (sha256 `06919FCE...`).

### 1.1 Hiérarchie de Vérité
1. **Niveau 1** : Le principe du Contrat Visuel (charte racine) — universel à tous les projets UI.
2. **Niveau 2** : L'infrastructure du Check 10 existant, à étendre.

---

## 🔬 2. Faits Extraits & Verbatims (Passage-Level Grounding)

| # | Source (fichier:lignes) | Verbatim / Constat | Fait établi |
| :---: | :--- | :--- | :--- |
| **F-01** | `vibe_check.py:357-398` (Check 10) | Le Check 10 traverse `docs/00-ingested/maquettes/*.md` et vérifie `is_vectorized`/`ocr_status`. | Il vérifie la **lisibilité** des maquettes, PAS l'**ancrage** d'un récit frontend à une maquette. Gap réel. |
| **F-02** | `AGENTS.md` (interdictions absolues) | « Ne jamais contredire une maquette […] elle constitue la source de vérité absolue pour l'interface. » | Le Contrat Visuel est un principe framework de premier rang, pas une spécificité projet. |
| **F-03** | `directives/business.md:26` | « Tout récit […] ne découlant pas directement d'un écran […] est réputé non requis. » | Un récit frontend sans ancrage visuel est un signal d'alerte — motive le check mécanique (Mécanisme A). |
| **F-04** | Story template (`layer` ADR-0366) | Frontmatter porte `layer: frontend | backend | fullstack`. | Cible du check : récits `frontend`/`fullstack` uniquement ; `backend` exclu. |

---

## 🗄️ 3. Périmètre Structurel (Framework)

Artefact modifié : `src/pipelines/vibe_check.py` (extension de la logique du Check 10 pour l'ancrage des récits frontend). Réutilise la traversée existante (DRY). Aucune table de données.

---

## 🎯 4. Contrats Déclaratifs Cibles

Aucun endpoint REST. Contrat = récit `layer: frontend`/`fullstack` en Phase ≥ 2 sans référence maquette (lien `docs/05-assets/`, lien Figma, ou section « Maquettes SSOT ») → WARNING listant les récits.

---

## 🏁 5. Évaluation de la Frontière Active

* **Arbitrages retenus** : D5 (Contrat Visuel = Mécanisme A, check dédié), D5-bis (récit dédié), D3 (WARNING seul).
* **Frontière** : ne re-vérifie pas la lisibilité OCR (déjà Check 10), n'implémente pas la sémantique tri-état (récit 163, prérequis).
* **Robustesse (ADR-0369)** : lecture récits en try/except + logger contextuel + encoding explicite.
* **Admission of Limits** : dépend de la sémantique tri-état du récit 163 pour émettre un WARNING non bloquant.
