---
id: MLOOP-181-BE
jira_key: ''
epic_key: EPIC-18-EVIDENCE-PARITY-PHASE3
type: Feature
title: Intégration Automatique des Décisions et Citations Ancrées avec le Harnais
  Phase 3 Build
origin: DIRECT_REQUIREMENT
source_ref: epic_evidence_impl_decisions.md
macro_size: L
status: DONE
grill_me: DONE
invest_score: 0/6
layer: backend
blocked_by:
- MLOOP-180-BE
created_at: '2026-09-22'
content_hash: bfc31ab9e0858af5
---

# 📖 MLOOP-181-BE : Intégration Automatique des Décisions et Citations Ancrées avec le Harnais Phase 3 Build

## 1. Intention Métier (User Story)
**En tant qu'** Ingénieur du framework mLoop,  
**je veux** que le harnais Phase 3 Build capture automatiquement décisions, citations ancrées et contrats dans l'EvidencePack,  
**afin d'**obtenir un pack éloquent sans effort manuel.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : `epic_evidence_impl_decisions.md` (Réf : Intégration build_harness + evidence_pack)
- **Hypothèse de Chiffrage Retenue** : Points d'injection tournoi + TDD + hook manuel + extraction citations depuis fichiers modifiés
- **Enveloppe Macro Estimée** : L (fourchette de 2-3 jours)

---

## 3. Périmètre Sommaire
### In-Scope (Macro)
- Injection des décisions du tournoi multi-draft (arbitrage Pareto) dans le pack
- Injection des décisions du cycle TDD Red-Green (choix de strategy)
- Hook `record_decision()` exposé pour les décisions manuelles
- Extraction des `verbatim_extracts` depuis les fichiers effectivement modifiés (lignes réelles)
- Injection des `declarative_contracts` référencés dans le code (zéro invention — `[API à définir]` si inconnu)
- Dédoublonnage : décision/citation identique non répétée (hash)

### Out-of-Scope (Macro)
- Extension du schema (couvert par MLOOP-180-BE)
- Backfill rétroactif (couvert par MLOOP-182-BE)
- Interface UI d'affichage des décisions

---

## 4. Contexte métier

Le harnais Phase 3 Build exécute tournoi multi-draft, cycle TDD et hooks sans jamais **persistenter** les décisions qu'il arbitre. Résultat : l'EvidencePack final est muet sur le *pourquoi* du code — exactement l'inverse des dossiers Phase 2 qui documentent chaque fait. Ce récit branche les 5 points de capture sur le schema étendu (MLOOP-180-BE).


---

## Critères d'acceptation

- [x] **CA-1** : Le tournoi multi-draft injecte automatiquement sa décision d'arbitrage Pareto (`category: architecture`) dans `<SID>_evidence.json`.
- [x] **CA-2** : Le cycle TDD injecte au moins une décision `category: testing` par cycle complet (rouge-vert-refactor).
- [x] **CA-3** : Hook public `record_decision(category, rationale, alternatives)` accessible depuis tout pipeline, avec dédoublonnage hash `category+rationale`.
- [x] **CA-4** : Citations extraites depuis les fichiers **réellement modifiés** (diff git), granularité **hybride D** : 1/fichier + 1/décision, ancrage `[start, end]` réel.
- [x] **CA-5** : Contrat inconnu → `[API à définir]` + `OQ-001`, **jamais** de route inventée (Zéro Fausse Route).
- [x] **CA-6** : Toutes décisions horodatées UTC ISO 8601, `alternatives_considered` renseigné (retenue vs rejetée tracée).

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : ce récit n'expose aucune route HTTP — capture interne de décisions. Toute route découverte en cours d'implémentation fera l'objet d'une `OQ-001` avec la mention `[API de soumission à définir]`.

---

## 5. Piliers Gherkin

### Pilier 1 : Nominal
```gherkin
Scénario: Arbitrage tournoi capturé comme décision
  Étant donné un tournoi multi-draft avec 3 candidats
  Quand l'arbitrage Pareto sélectionne le candidat B
  Alors une décision category="architecture" est ajoutée à implementation_decisions
  Et le rationale cite le score Pareto retenu
  Et alternatives_considered liste les candidats A et C
```

### Pilier 2 : Exceptions
```gherkin
Scénario: Décision en double rejetée
  Étant donné une décision existante (category="architecture", rationale identique hash)
  Quand record_decision est rappelée avec les mêmes valeurs
  Alors aucune nouvelle entrée n'est ajoutée
  Et un log DEBUG "duplicate_decision_skipped" est émis

Scénario: Contrat API inconnu pendant le build
  Étant donné un appel à une route absente du profil B
  Quand la capture de contrat est exécutée
  Alors declarative_contracts contient "[API de soumission à définir]"
  Et une OQ-001 est consignée dans docs/04-transverse/
  Et aucune URI n'est inventée
```

### Pilier 3 : Résilience & Mode Dégradé
```gherkin
Scénario: Fichier modifié supprimé avant extraction citation
  Étant donné un fichier référencé dans le diff mais supprimé sur disque
  Quand l'extraction de citation est exécutée
  Alors la citation est skippée avec alerte "source_deleted"
  Et les autres citations continuent d'être extraites
  Et le build ne crash pas

Scénario: Timeout extraction sur gros diff
  Étant donné un diff de 500 fichiers
  Quand l'extraction dépasse le timeout autorisé
  Alors un sous-ensemble déterministe (premiers N fichiers) est traité
  Et un log DEBUG contextualisé est émis (ADR-0369)
  Et une alerte "extraction_truncated" figure dans le pack
```

### Pilier 4 : UX (Observabilité)
```gherkin
Scénario: Richesse visible dans le rapport de build
  Étant donné un build ayant produit 3 décisions et 5 citations
  Quand le rapport WikiFix est généré
  Alors il affiche "decisions: 3 | citations: 5 | richness: OK"
  Et confidence_score reflète le multiplicateur richesse (Décision 5)
---

## 6. Décisions du Grill 1:1 Intégrées

- **Déc. 1 (Granularité)** : citations **hybrides** — 1/fichier modifié + 1/décision.
- **Déc. 2 (Sources)** : tournoi + TDD + fact_dossier + plan + hook `record_decision()`.
- **Déc. 3 (Emplacement)** : décisions dans `<SID>_evidence.json`, citations dans `<SID>_fact_dossier.md`.
- **Déc. 4 (Gate 5)** : blocking **new only** — legacy EPIC 10→17 exempté (warning), nouveau `DONE_TESTED`+ exige ≥ 1 citation.
- **Déc. 5 (Confiance)** : multiplicateur richesse + `richness_penalty` dans `epistemic_audit`.
- **Déc. 6 (Legacy)** : **EPIC 1-9 strictement exclus** — focus prioritaire EPIC 10→18, code parfait exigé.

---

## 7. Zones d'Ombre Restantes (post-Grill)

- ~~❓ Format natif du tournoi~~ → **RÉSOLU** : conversion directe `TournamentReport` → `ImplementationDecision` (catégorie `architecture`, rationale score Pareto, alternatives = candidats rejetés avec scores).
- ~~❓ Décisions TDD~~ → **RÉSOLU** : **par cycle complet** (rouge-vert), pas par test unitaire (cohérent avec le scellement `tdd_cycle` unique par banc).
- ~~❓ Extraction citation~~ → **RÉSOLU** : **eager** (à la capture, dans `handle_code_tournament`), avec mode dégradé Pilier 3 (WARNING, build jamais bloqué).
