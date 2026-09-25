---
story_id: MLOOP-161-BE
jira_key: ''
dossier_status: CURRENT
last_verified_at: "2026-09-22T12:43:27Z"
ssot_source: standards/adr-system/
sources_hashes:
  standards/adr-system/README.md: "B6FDE914A4F1511A"
  AGENTS.md: "3EF613F235944A4C"
  Projects/BoireFrere_Segment2/directives/business.md: "06919FCE5B076F8E"
---

# 📂 Dossier de Preuves Documentaires & Cadrage SSOT — MLOOP-161-BE

**Titre Métier** : ADR de Boot Enforcement des Directives SSOT et Amendement des Chartes AGENTS
**Identifiant Story** : `MLOOP-161-BE`
**Clé Jira Officielle** : *(temporaire — framework interne)*
**Date d'Extraction & Cadrage** : 2026-09-22
**Auditeur mLoop** : Agentic Pair Programmer

> **Nature framework** : SSOT = catalogue ADR (`standards/adr-system/`) + chartes d'instructions (`AGENTS.md` et miroirs).

---

## 🧭 1. Sources Physiques & Matrice de Vérité

* 📜 **Catalogue des décisions d'architecture** : `standards/adr-system/README.md` (sha256 `B6FDE914...`, 136 lignes) — dernier ADR constaté : `0383-deterministic-phase-4-qa-certification-harness.md`.
* 📜 **Charte d'instructions racine** : `AGENTS.md` (sha256 `3EF613F2...`, 253 lignes) — cible d'amendement §4.1.
* 📜 **Charte du projet témoin** : `Projects/BoireFrere_Segment2/AGENTS.md` — ne liste pas son propre répertoire `directives/` (incohérence à corriger).

### 1.1 Hiérarchie de Vérité
1. **Niveau 1** : Décision d'architecture consignée (ADR Type 1).
2. **Niveau 2** : Chartes d'instructions (racine + miroirs GEMINI/CLAUDE + projet).

---

## 🔬 2. Faits Extraits & Verbatims (Passage-Level Grounding)

| # | Source (fichier:lignes) | Verbatim | Fait établi |
| :---: | :--- | :--- | :--- |
| **F-01** | `AGENTS.md` (Check 1 vibe_check, constaté) | Parité miroir AGENTS.md / GEMINI.md / CLAUDE.md avec auto-healing depuis AGENTS.md. | Toute clause ajoutée à AGENTS.md est propagée automatiquement aux miroirs. |
| **F-02** | `standards/adr-system/` (listing) | Dernier ADR : `0383-deterministic-phase-4-qa-certification-harness.md`. | Prochain slot libre au cadrage = `0384` (à reconfirmer au build). |
| **F-03** | `directives/business.md:26` | « Souveraineté des Maquettes Figma (SSOT Première) […] Tout récit […] ne découlant pas directement d'un écran […] est réputé non requis. » | Le Contrat Visuel Premier est une loi projet — motive la clause SSOT dans la charte. |
| **F-04** | `AGENTS.md` (§2 Boire, constaté) | La charte projet Boire liste `reference/`, `docs/`, `backlog/`, `memory/` mais **omet** `directives/`. | Correction requise : lister `directives/` et déclarer `docs/03-models/` comme SSOT. |

---

## 🗄️ 3. Périmètre Structurel (Framework)

Artefacts produits : `standards/adr-system/0384-*.md` (nouveau), `README.md` (index modifié), `AGENTS.md` + miroirs (clause ajoutée), `Projects/BoireFrere_Segment2/AGENTS.md` (correction). Aucune table de données.

---

## 🎯 4. Contrats Déclaratifs Cibles

Aucun endpoint REST. Contrat = ADR indexé + clause présente à l'identique dans les 3 chartes miroirs après synchronisation.

---

## 🏁 5. Évaluation de la Frontière Active

* **Arbitrages retenus** : D3 (WARNING seul, pas d'escalade gravée), D4 (0384 figé + garde de renumérotation).
* **Frontière** : n'implémente pas le contrôle automatique (récit 163), ne renforce pas le skill grill (récit 162).
* **Admission of Limits** : la parité miroir dépend du Check 1 existant ; à valider après amendement.
