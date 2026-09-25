# 📁 Dossier de Preuves Documentaires — `MLOOP-223-FE`

- **Récit** : `MLOOP-223-FE` — Module Dashboard pour l'Écosystème Tooling & Visualisation des Runtimes Développeur (EPIC-22-TOOLING-ECOSYSTEM-HARNESS)
- **Établi le** : 2026-09-24 — Cadrage Macro-Grill VALIDÉ
- **dossier_status**: VALIDATED
- **Décisions scellées** : Grill Macro EPIC-22 (Q4-A Tuile Synthétique Overview, Endpoint FastAPI `/api/tooling/status`) → `ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md`

---

## 1. Sources & Notes d'Atelier

- Épopée : `Projects/mLoop/backlog/epics/epic_tooling_ecosystem_harness.md`
- Fiches de Savoir SSOT : `docs/06-knowledge/06-tooling-ecosystem/KN-050_opencode_cli_runtime.md`, `KN-051_plannotator_workflow.md`
- ADR de référence : `standards/adr-system/0202-modularite-interne-agents.md` (≤ 300L), `standards/adr-system/0319-anti-invention-routes-api.md`
- ADR de cadrage local : `Projects/mLoop/docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md`
- Code source ciblé : `src/dashboard/routers/tooling.py` (≤ 300L), `src/dashboard/app.py`, `src/dashboard/static/index.html`

---

## 2. Matrice de Résolution des Conflits

| Conflit | Résolution |
| :--- | :--- |
| Page dédiée vs Tuile Overview | **Tuile Synthétique Overview (Q4-A)** : Intégration sur la page d'accueil du Dashboard mLoop pour une visibilité directe sans clic superflu. |
| Données statiques vs Monitoring réel | **Endpoint Déterministe** : Route `/api/tooling/status` interrogeant en temps réel la présence des binaires et les versions. |
| Actions déclenchables depuis l'IHM | **Actions Claires** : Bouton d'ouverture Plannotator et copie de commande OpenCode CLI. |

---

## 3. Extraits Verbatim Sourcés

**Extrait 1 — `Projects/mLoop/docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md` :**
```text
"Endpoint FastAPI /api/tooling/status dans src/dashboard/routers/tooling.py (≤ 300L). Intégration d'une carte cyber 'Developer Runtimes & Tooling' directement sur la page Overview du Dashboard web mLoop."
```
➔ **Fait établi (F-01)** : Le contrat d'échange HTTP expose la route `GET /api/tooling/status` répondant en JSON structuré.

**Extrait 2 — `standards/adr-system/0202-modularite-interne-agents.md` :**
```text
"Toute nouvelle route ou routeur de dashboard doit respecter le plafond de 300 lignes."
```
➔ **Fait établi (F-02)** : Le routeur `src/dashboard/routers/tooling.py` doit respecter impérativement `RULE-AST-01` (≤ 300L).
