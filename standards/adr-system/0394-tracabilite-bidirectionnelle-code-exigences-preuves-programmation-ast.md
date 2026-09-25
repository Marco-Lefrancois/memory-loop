# ADR-0394 : Traçabilité Bidirectionnelle Code ↔ Exigences, Preuves de Programmation AST & EvidencePack 2.0

* **Statut** : PROPOSÉ *(Épopée EPIC-33)*
* **Date** : 25 septembre 2026
* **Décideurs** : Product Owner (Marco), Lead Architect mLoop, Agent Orchestrateur
* **Dépendances / Références** : [ADR-0320](0320-grill-me-frontier-design-tree-alignment.md) (Grounding Preuves Amont), [ADR-0326](0326-fact-search-and-substantive-content-review.md) (Fact-Search FTS5), [ADR-0369](0369-standards-robustesse-python-senior.md) (Python Senior), [ADR-0375](0375-project-lifecycle-5-phases-and-analysis-types.md) (5 Phases & Règle des 2 Gabarits), [ADR-0376](0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md) (Rigueur 360° Zéro Blindspot), [ECOSYSTEM_RIGOR_PROTOCOL.md](../protocols/ECOSYSTEM_RIGOR_PROTOCOL.md).

---

## 🚀 1. Contexte & Problématique

Dans l'écosystème **Memory Loop**, la traçabilité des exigences était historiquement asymétrique :
1. **L'Amont était ultra-rigide** : Le Dossier de Preuves (`_fact_dossier.md`) justifie minutieusement chaque exigence en amont en citant mot-à-mot les sources réelles (Figma, ateliers, directives).
2. **L'Aval était fragmenté** : Lors de la Phase 3 (**BUILD & DEV**), le lien entre un bloc de code physique (fonction, méthode, branche de garde) et son exigence d'origine reposait uniquement sur la bonne volonté du développeur ou sur des tests unitaires dispersés.
3. **Le Risque du "Ghost Code" (Sur-ingénierie non auditée)** : Sans lien formel, des pans entiers de code ou des branches défensives complexes peuvent être introduits sans correspondre à aucune règle métier (`RM-XXX`) ni critère d'acceptation Gherkin.
4. **La Contrainte No-Code Inviolable du Récit** : La User Story Markdown (`story_template.md`) doit impérativement rester 100% déclarative et no-code (Gate G4). Il était donc hors de question d'y injecter des noms de méthodes physiques ou des références AST.

---

## 💡 2. Décisions d'Architecture

### A. Séparation Étanche des Preuves Amont vs Preuves Aval

Le système formalise le continuum de preuve en deux livrables distincts et complémentaires :

1. **Preuve d'Amont (Pourquoi l'exigence existe)** :
   * Consignée dans : `memory/evidence/<STORY_ID>_fact_dossier.md`.
   * Ancrage : Citations verbatim de sources documentaires, maquettes SVG/Figma, schémas DBML.
   * Phase : Phase 1 (Ingest) & Phase 2 (Plan & Grill).

2. **Preuve d'Aval / Preuve de Programmation (Pourquoi ce code existe)** :
   * Consignée dans :
     - Le **Plan d'Implémentation** (`memory/plan/implementation_plan_<STORY_ID>.md`, Section 3).
     - Le **Sidecar EvidencePack JSON** (`memory/evidence/<STORY_ID>_evidence.json`, champ `code_traceability_matrix`).
   * Ancrage : Symboles AST physiques (`chemin/fichier.py::NomClasse.methode`).
   * Phase : Phase 3 (Build & Dev) & Phase 4 (Validate & QA).

---

### B. Matrice de Traçabilité Code ↔ Exigences (Code Evidence Matrix)

Toute modification physique substantielle réalisée sous `src/` (ou guidée en Dev Handoff client) doit être couplée à la matrice déclarative :

```json
{
  "code_traceability_matrix": [
    {
      "ast_symbol": "src/core/auth.py::TokenVerifier.verify_expiration",
      "requirement_ref": "RM-012",
      "gherkin_scenario": "Pilier 2 (Exception - Jeton expiré)",
      "rationale": "Lève HTTP 401 et consigne l'événement pour initier le refresh token asynchrone sans déconnexion brutale.",
      "test_symbol": "tests/test_auth.py::test_token_expired_triggers_401"
    }
  ]
}
```

---

### C. Ancrage par Symbole AST Déterministe (Anti-Fragilité)

* **Interdiction de l'ancrage par numéro de ligne** : Les numéros de ligne (`L42-L58`) dérivent à chaque commit et créent une illusion de preuve éphémère.
* **Obligation de l'ancrage par Symbole Qualifié (AST Identifier)** : Utilisation de la notation canonique `chemin/fichier.ext::Symbole`.
  - Python : `module/fichier.py::Classe.methode` ou `module/fichier.py::fonction`.
  - TypeScript : `src/components/Fichier.tsx::NomComposant` ou `src/services/api.ts::nomFonction`.

---

### D. Contrôle Déterministe Vibe-Check (Check 29 — Zero Ghost Code)

Une sonde d'intégrité automatique est intégrée dans le pipeline de validation pré-vol :
* **Check 29** : Vérifie que 100% des fichiers et symboles déclarés dans le plan d'implémentation de la story courante disposent d'un rattachement explicite à une règle métier ou un scénario de test.
* Tout ajout de code sans ancrage dans la matrice lève un avertissement ou une anomalie `UNANCHORED_CODE_MUTATION`.

---

### E. Alignement Souverain OpenSpec (Standard de Pair-Programming IA)

Conformément à l'arbitrage officiel de l'équipe d'architecture, **OpenSpec ([openspec.dev](https://openspec.dev/)) est le standard canonique retenu pour cadrer les travaux de pair-programming avec l'IA en aval (Cursor, Claude Code, Cline, Antigravity, OpenCode)**.

La traçabilité mLoop s'articule ainsi de manière bidirectionnelle avec la topologie OpenSpec :

| Concept mLoop (Amont) | Équivalent OpenSpec (Aval) | Emplacement Canonique |
| :--- | :--- | :--- |
| **User Story & Règle Métier (`RM-XXX`)** | `Requirement: <Titre>` (`The system SHALL...`) | `openspec/specs/<capability>/spec.md` |
| **Critères d'Acceptation Gherkin (4 Piliers)** | `Scenario: <Nom>` (`GIVEN / WHEN / THEN`) | `openspec/specs/<capability>/spec.md` |
| **Plan d'Implémentation & Symboles AST** | `tasks.md` (Tâches d'implémentation par fichier) | `openspec/changes/<change>/tasks.md` |
| **Dossier de Preuves & Rationale** | `proposal.md` & `design.md` | `openspec/changes/<change>/` |

*Règle d'or : Tout récit validé `READY_FOR_DEV` est nativement convertible en changeset OpenSpec (`proposal.md` + `specs/` + `tasks.md`), permettant à l'agent de pair-programming de travailler sans aucune dérive ni hallucination.*

---

## ⚖️ 3. Conséquences & Bénéfices

* **Clarté Absolue pour les Revues de Code** : L'auditeur (humain ou Sentinel) comprend en 5 secondes *pourquoi* une fonction existe en consultant la matrice de l'EvidencePack.
* **Protection Anti-Slop & Anti-Sur-Ingénierie** : Tout code superflu non justifié par une exigence est immédiatement repéré et élagué.
* **Préservation Totale du No-Code Métier** : Les Product Owners continuent de lire des récits purs en français fonctionnel, pendant que les développeurs disposent d'une cartographie technique rigoureuse.
