---
id: MLOOP-090-BE
jira_key: '-'
epic_key: EPIC-9-STAGE4-DETERMINISTIC-VALIDATION
status: SHIPPED
type: Feature
title: Moteur de Certification Sprint et Runner 4 Piliers Gherkin
tags: [qa, certifier, cel, ast, validation]
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-9-STAGE4-DETERMINISTIC-VALIDATION] Moteur de Certification Sprint et Runner 4 Piliers Gherkin (MLOOP-090-BE)

## Description
**En tant que** Auditeur Qualité et Certificateur de Phase 4 (STAGE_4_VALIDATE),  
**je veux** disposer d'un moteur automatisé de certification opposable orchestrant les bancs de tests pytest, l'audit statique AST et la triangulation du Code Evidence Ledger (CEL),  
**afin d'** interdire toute progression de sprint sans preuve tangible et infalsifiable d'exécution intégrale des 4 Piliers Gherkin.

---

## Contexte & Périmètre

### Contexte Métier
En Phase 4, la tentation est grande de se reposer sur des déclarations verbales ou des évaluations superficielles du backlog. Ce récit met en place le composant central `src/pipelines/qa_certifier.py` qui pilote la certification déterministe en triangulant le code de test, le code source physique et les blocs de preuves consignés dans le Code Evidence Ledger.

### In-Scope
- Moteur de certification `QaCertifierEngine` dans `src/pipelines/qa_certifier.py`.
- Exécution de tests unitaires avec timeout déterministe (défaut 180s).
- Audit statique AST des modules produits par le sprint (ADR-0202 et ADR-0369).
- Triangulation du Code Evidence Ledger et vérification de la couverture des 4 Piliers Gherkin (Nominal, Rejets, Résilience, Observabilité).
- Commande CLI `python src/swarm.py validate-sprint --project <P>`.
- Production des rapports opposables `memory/qa_certification_report.json` et `.md`.

### Out-of-Scope
- Déploiement distant CI/CD externe (environnement local souverain mLoop).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Banc Pytest avec Timeout Déterministe
* **Entrée Métier** : Répertoire de tests du projet ou du sprint.
* **Traitement** : Exécution de `pytest` en sous-processus isolé avec capture de sortie et timeout explicite.
* **Résultat** : Dataclass `PytestExecutionResult` avec comptage passed/failed, durée et couverture.

#### 2. Audit Statique AST Ciblé
* **Traitement** : Analyse via `AstChecker` des modules impactés par le sprint.
* **Règle** : Tolérance zéro violation (seuil = 0).

#### 3. Triangulation Code Evidence Ledger
* **Traitement** : Découverte et validation du fichier `*code_evidence_ledger.json`.
* **Règle** : Les 4 Piliers Gherkin doivent impérativement être couverts par au moins un bloc vérifié.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Moteur de Certification Sprint et Runner 4 Piliers Gherkin

  # 1. CHEMIN NOMINAL
  Scénario: Certification nominale complète d'un sprint
    Étant donné un projet avec tests au vert, 0 violation AST et CEL complet
    Quand la commande validate-sprint est exécutée
    Alors le rapport de certification est généré avec is_certified=True
    Et le code de retour CLI est 0

  # 2. EXCEPTIONS & REJETS
  Scénario: Rejet si le Code Evidence Ledger présente des angles morts
    Étant donné un CEL omettant le Pilier 3 (Résilience)
    Quand validate-sprint est lancé
    Alors la certification est refusée avec motif bloquant explicite
```
