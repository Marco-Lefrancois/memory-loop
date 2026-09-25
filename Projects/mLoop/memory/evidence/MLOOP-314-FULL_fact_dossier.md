# 📋 Fact Dossier — `MLOOP-314-FULL` : Formalisation Normative ADR-0391, Mise à Jour SSOT & Harnais de Certification E2E

---

- **Récit Cible** : `MLOOP-314-FULL`
- **Épopée** : `EPIC-31-FSM-ANTI-HARDCODING-AND-LIFECYCLE-HARMONIZATION`
- **Composant** : `Standards/QA` (`standards/adr-system/`, `STORY_LIFECYCLE_PROTOCOL.md`, `tests/`)
- **Établi le** : 2026-09-25 — Session Macro-Grill VALIDÉE (PO Marco)
- **Autorité** : PO mLoop (Marco) / Architecte Framework

---

## ⚖️ 1. Matrice des Décisions Validées en Session Macro-Grill

| # | Question Grillée | Option Retenue | Justification & Impact Technique |
| :- | :--- | :---: | :--- |
| **Q5** | Résolution du numéro d'ADR pour l'harmonisation FSM | **Option 5.A (ADR-0391)** | Attribution du prochain numéro séquentiel libre `0391` : `standards/adr-system/0391-harmonisation-cycle-de-vie-recits-5-phases-fsm.md`. Aucune collision avec l'ADR-0390 existante sur Fact-Search. |
| **Q-Rule** | Règle d'immuabilité absolue des récits `DONE` | **Validée** | Un récit au statut `DONE` est un incrément clos, inviolable et scellé. Toute anomalie ultérieure donne lieu à un nouveau `BUG` ou `HOTFIX` dans le sprint suivant. |
| **Q-Auto** | Auto-clôture Gate 5 sans confirmation humaine | **Validée** | Gate 5 est 100% autonome dès lors que 100% des vérifications pré-vol sont vertes. |

---

## 🔍 2. Extraits Sourcés & Passage-Level Grounding (Vérité Terrain)

### Extrait 1 — `standards/adr-system/0390-fact-search-indexation-arbres-niches-docs-domaine-couche.md`
* **Fait Établi** : L'ID `0390` est déjà scellé et archivé pour l'indexation Fact-Search FTS5. L'ADR de l'EPIC-31 s'intitule formellement `ADR-0391 : Harmonisation Déterministe du Cycle de Vie des Récits en 5 Phases, Éradication du Hardcoding FSM & Clôture Autonome Gate 5`.

### Extrait 2 — `standards/protocols/STORY_LIFECYCLE_PROTOCOL.md` (Lignes 13–23)
* **Fait Établi** : Le schéma de machine à états doit être mis à jour pour représenter la chaîne :
  $$\text{DRAFT} \longrightarrow \text{IN\_ANALYZE} \longrightarrow \text{READY\_FOR\_GROOMING} \overset{\text{Gate 2}}{\longrightarrow} \text{READY\_FOR\_DEV} \longrightarrow \text{IN\_DEV} \overset{\text{Gate 3}}{\longrightarrow} \text{READY\_FOR\_QA} \overset{\text{Gate 4}}{\longrightarrow} \text{QA\_CERTIFIED} \overset{\text{Gate 5 (Auto)}}{\longrightarrow} \text{DONE}$$

---

## 🚪 3. Frontière Active & Admission of Limits

- **In-Scope MLOOP-314-FULL** :
  - Rédaction complète de `0391-harmonisation-cycle-de-vie-recits-5-phases-fsm.md`.
  - Mise à jour de `standards/protocols/STORY_LIFECYCLE_PROTOCOL.md`.
  - Mise à jour des gabarits de backlog.
  - Exécution et certification du harnais complet de tests (1638+ tests au vert).
- **Out-of-Scope** :
  - Modification destructrice des 91 récits archivés.
