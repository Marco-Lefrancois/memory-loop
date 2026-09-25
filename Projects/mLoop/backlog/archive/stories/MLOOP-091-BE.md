---
id: MLOOP-091-BE
jira_key: '-'
epic_key: EPIC-9-STAGE4-DETERMINISTIC-VALIDATION
status: SHIPPED
type: Feature
title: Contradiction Engine NLI et Verification Leakage Gate
tags: [qa, nli, leakage, gates, validation]
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-9-STAGE4-DETERMINISTIC-VALIDATION] Contradiction Engine NLI et Verification Leakage Gate (MLOOP-091-BE)

## Description
**En tant que** Auditeur QA Déterministe et Sentinel du framework mLoop,  
**je veux** soumettre les tests et les contrats du code source à une vérification anti-fuite (Verification Leakage Gate) et à une inférence logique de non-contradiction sémantique (Contradiction Engine NLI),  
**afin d'** interdire les tests tautologiques auto-validants, les violations d'encapsulation privée et les divergences sémantiques entre la documentation SSOT et le code physique.

---

## Contexte & Périmètre

### Contexte Métier
Dans les architectures d'agents autonomes, deux dérives pernicieuses menacent l'intégrité logicielle en Phase 4 :
1. **Les tests tautologiques et les fuites de vérification (ADR-0354)** : Des suites de tests créées par les agents qui s'auto-valident en affirmant qu'un mock vaut la valeur injectée dans le mock, ou qui brisent l'encapsulation en accédant aux attributs privés `_internal_state` au lieu de tester le contrat public.
2. **Les contradictions sémantiques documentation/code (ADR-0326)** : Des spécifications d'architecture qui promettent un comportement (ex: rejet 403, paramètre optionnel, invariant de circuit breaker) alors que l'implémentation physique s'est écartée du contrat sans mise à jour du SSOT.

Ce récit formalise les niveaux 4 et 5 du harnais de certification Phase 4 (ADR-0383) en interconnectant `VerificationLeakageGate` et `NLIVerifier` directement au moteur de certification QA `QaCertifierEngine`.

### In-Scope
- Audit anti-fuite automatisé (ADR-0354) des bancs de tests du sprint (Black-box strict, Anti-tautologie mocks, Invariants causaux métier).
- Moteur d'audit contradictoire NLI (ADR-0326) confrontant les assertions documentaires clés aux symboles et schémas réels du code.
- Module applicatif `src/pipelines/nli_auditor.py` conforme ADR-0202 (<=300 lignes, <=15 Ko) et ADR-0369.
- Intégration dans `QaCertifierEngine` des niveaux 4 (NLI) et 5 (Leakage).
- Commande CLI `python src/swarm.py nli-audit --project <P>`.

### Out-of-Scope
- Ré-entraînement de modèles d'inférence NLI locaux (utilisation du Tier-1 heuristique déterministe à 0 token et Tier-2 LLM avec cache SQLite).
- Modification des règles du compilateur AST.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Détection des Fuites de Vérification (Verification Leakage Gate - ADR-0354)
* **Entrée Métier** : Liste de fichiers de tests Python du projet ou du sprint.
* **Règles d'admissibilité & Validation** : Fichiers `.py` syntaxiquement valides sous `tests/`.
* **Traitement & Algorithme Métier** : Analyse AST des fonctions de test `test_*` :
  - *Critère 1 (Black-Box Strict)* : Rejet de toute assertion accédant à des attributs privés commençant par un underscore unique (ex: `assert obj._cache == ...`).
  - *Critère 2 (Anti-Tautologie Mocks)* : Rejet des assertions comparant directement une valeur mockée sans transformation métier (`assert mock.return_value == "val"` ou `assert res == "val"` où `"val"` est injecté dans le mock immédiatement avant).
  - *Critère 3 (Invariant Causal)* : Rejet des tests sans aucune assertion sur l'état ou le résultat métier (tests uniquement composés d'appels `assert_called_once`).
* **Résultat Métier & Mutations** : Rapport `LeakageSummary` avec comptage des violations critiques et statut `passed: bool`.

#### 2. Audit Contradictoire Sémantique NLI (Contradiction Engine - ADR-0326)
* **Entrée Métier** : Documentation d'architecture (`docs/01-architecture/*.md`) et code source du sprint (`src/`).
* **Règles d'admissibilité & Validation** : Présence des documents de référence du projet.
* **Traitement & Algorithme Métier** : Extraction des affirmations atomiques via `claim_extractor` et inférence NLI via `nli_verifier` :
  - Vérification déterministe Tier-1 (présence des symboles, signatures de méthodes, constantes d'invariants).
  - Calcul du score de contradiction global. Tout verdict `CONTRADICTION` sur un invariant critique bloque la certification.
* **Résultat Métier & Mutations** : Rapport `NliAuditSummary` avec liste des contradictions et niveau de conformité.

#### 3. Intégration au Moteur de Certification Sprint (`QaCertifierEngine`)
* **Traitement** : `QaCertifierEngine.certify_sprint()` évalue désormais les 5 niveaux :
  1. Pytest suite
  2. AST checker
  3. CEL 4 Piliers
  4. NLI Contradiction Engine
  5. Verification Leakage Gate
* **Résultat Métier** : Le rapport opposable `qa_certification_report.json` intègre `leakage_summary` et `nli_summary`. Si une fuite critique ou une contradiction est détectée, `is_certified` est forcé à `False` avec mention explicite dans `blocking_reasons`.

---

## Parcours Interactif & API

### Contrats d'Échange CLI
- `python src/swarm.py check-leakage [--file <path>]` : Vérification ciblée ou globale anti-fuite.
- `python src/swarm.py nli-audit --project <P>` : Audit de non-contradiction sémantique documentation/code.
- `python src/swarm.py validate-sprint --project <P>` : Certification intégrale 5 niveaux.

---

## Règles d'affaires
* **[Tolérance Zéro Tautologie]** : Aucun test tautologique auto-validant n'est admis dans les livrables certifiés Phase 4.
* **[Inviolabilité du Contrat Public]** : Les tests unitaires d'intégration doivent valider le comportement observable du système sans briser l'encapsulation (`_attr`).
* **[Anti-Contradiction SSOT]** : Toute contradiction formelle identifiée entre la documentation normative et le code applicatif suspend la transition vers Gate 4.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Contradiction Engine NLI et Verification Leakage Gate

  # 1. CHEMIN NOMINAL (Suite de Tests Saine et Zéro Contradiction NLI)
  Scénario: Certification réussie d'un sprint sans fuite de test ni contradiction
    Étant donné un projet avec une suite de tests respectant l'encapsulation publique
    Et une documentation d'architecture alignée avec les contrats physiques du code
    Quand le moteur de certification de sprint est exécuté
    Alors la Verification Leakage Gate confirme 0 violation critique
    Et le Contradiction Engine confirme l'absence de contradiction sémantique
    Et le statut global de certification est CERTIFIÉ CONFORME

  # 2. EXCEPTIONS & REJETS MÉTIER (Détection d'une Fuite de Vérification Tautologique)
  Scénario: Rejet de certification suite à un test accédant à un membre privé
    Étant donné un fichier de test contenant une assertion "assert client._socket is not None"
    Quand la Verification Leakage Gate analyse le fichier
    Alors une violation critique de Critère 1 (Black-Box Strict) est levée
    Et la certification de sprint est immédiatement rejetée

  # 3. RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Détection de Contradiction Sémantique)
  Scénario: Rejet de certification suite à une contradiction documentaire formelle
    Étant donné une spécification affirmant un invariant formel démenti par l'implémentation
    Quand le Contradiction Engine NLI analyse le projet
    Alors un verdict CONTRADICTION est consigné avec preuve du désalignement
    Et la Gate 4 est verrouillée avec motif bloquant explicite

  # 4. UX & OBSERVABILITÉ (Rapport de Synthèse Multi-Niveaux et Événements OTel)
  Scénario: Émission du rapport opposable enrichi des niveaux NLI et Leakage
    Étant donné l'exécution complète de validate-sprint
    Quand le rapport qa_certification_report.json et son équivalent Markdown sont générés
    Alors ils comportent les sections détaillées des 5 Niveaux de Certification
    Et un événement d'audit est consigné dans le journal des événements
```
