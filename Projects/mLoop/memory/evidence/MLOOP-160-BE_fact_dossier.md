---
story_id: MLOOP-160-BE
jira_key: ''
dossier_status: CURRENT
last_verified_at: "2026-09-22T12:43:27Z"
ssot_source: standards/protocols/
sources_hashes:
  standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md: "C42BDD65BFE5269B"
  Projects/BoireFrere_Segment2/directives/tech.md: "8AD22E38347B0BE7"
  Projects/BoireFrere_Segment2/directives/business.md: "06919FCE5B076F8E"
---

# 📂 Dossier de Preuves Documentaires & Cadrage SSOT — MLOOP-160-BE

**Titre Métier** : Protocole Normatif de Hiérarchie SSOT et Chargement des Directives Projet
**Identifiant Story** : `MLOOP-160-BE`
**Clé Jira Officielle** : *(temporaire — framework interne, non synchronisé Jira)*
**Date d'Extraction & Cadrage** : 2026-09-22
**Auditeur mLoop** : Agentic Pair Programmer

> **Nature framework** : Ce récit relève de l'auto-développement mLoop. Sa source de vérité n'est pas un modèle de données métier (`docs/03-models/`) mais les **protocoles et directives du framework** eux-mêmes. Le grounding ci-dessous cite des fichiers réels du dépôt.

---

## 🧭 1. Sources Physiques & Matrice de Vérité

* 📜 **Protocole de rigueur d'écosystème (ancrage normatif)** : `standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md` (ADR-0376, sha256 `C42BDD65...`)
* 📜 **Directives techniques du projet témoin (preuve de la hiérarchie SSOT)** : `Projects/BoireFrere_Segment2/directives/tech.md` (sha256 `8AD22E38...`)
* 📜 **Directives d'affaires du projet témoin** : `Projects/BoireFrere_Segment2/directives/business.md` (sha256 `06919FCE...`)

### 1.1 Hiérarchie de Vérité (objet même de ce récit)
1. **Niveau 1 (Suprême)** : Source de vérité canonique déclarée par le projet.
2. **Niveau 2 (Amont)** : Sources d'ingestion amont — non autoritaires en cas de divergence.
3. **Niveau 3 (Staging)** : Matière première brute locale — jamais lue directement, jamais autoritaire.

---

## 🔬 2. Faits Extraits & Verbatims (Passage-Level Grounding)

| # | Source (fichier:lignes) | Verbatim | Fait établi |
| :---: | :--- | :--- | :--- |
| **F-01** | `directives/tech.md:15` | « Le document maître consolidé `docs/03-models/Structure-de-données.md` fait foi absolue […]. Le document historique `reference/Structure-de-données.md` […] n'est plus autoritaire pour le modèle applicatif dès lors qu'il diverge du maître. » | La hiérarchie SSOT est déjà tranchée par directive : le maître consolidé prime, l'amont est subordonné. |
| **F-02** | `directives/business.md:36` | « Souveraineté Absolue du Modèle Consolidé `docs/03-models/` […] constitue la véritable Source Unique de Vérité (SSOT) […]. Le document historique `reference/Structure-de-données.md` […] reste une source d'ingestion amont non autoritaire en cas de divergence. » | Redondance intentionnelle affaires+technique : la primauté du consolidé est un invariant du projet. |
| **F-03** | `ECOSYSTEM_RIGOR_PROTOCOL.md:6` | « Champ d'Application : Toute modification du moteur, des protocoles, des gabarits ou des directives de Memory Loop. » | Le présent récit (création d'un protocole normatif) tombe sous l'audit 360° en 7 couches. |

---

## 🗄️ 3. Périmètre Structurel (Framework — pas de schéma DBML)

Ce récit ne manipule aucune table de données. Il produit un artefact documentaire : `standards/protocols/PROJECT_DIRECTIVES_SSOT_PROTOCOL.md` (nouveau, autonome, ~40 lignes).

---

## 🎯 4. Contrats Déclaratifs Cibles

Aucun endpoint REST. Récit de gouvernance documentaire. Contrat = présence d'un fichier de protocole conforme aux règles d'affaires du récit.

---

## 🏁 5. Évaluation de la Frontière Active (Frontier Design Tree)

* **Arbitrages retenus (session Grill 22/09)** :
  * D2 — Fichier autonome court (~40 lignes), refus d'enfouissement.
  * Le protocole distingue deux mécanismes de gouvernance (check générique vs chargement forcé).
* **Frontière (ce que le récit NE fait PAS)** : n'implémente aucun contrôle automatique (récit 163), n'amende pas les chartes (récit 161).
* **Admission of Limits** : la numérotation ADR de référence (0384) sera reconfirmée au build du récit 161.
