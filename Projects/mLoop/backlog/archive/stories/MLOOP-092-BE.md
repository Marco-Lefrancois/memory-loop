---
id: MLOOP-092-BE
jira_key: '-'
epic_key: EPIC-9-STAGE4-DETERMINISTIC-VALIDATION
status: SHIPPED
type: Feature
title: Verrous Bloquants de Gate 4 et Gouvernance Opposable de Recette QA
tags: [core, lifecycle, gatekeeper, governance, gate4]
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-9-STAGE4-DETERMINISTIC-VALIDATION] Verrous Bloquants de Gate 4 et Gouvernance Opposable de Recette QA (MLOOP-092-BE)

## Description
**En tant que** Gardien de la Conformité et du Cycle de Vie Projet (ProjectLifecycleManager),  
**je veux** verrouiller physiquement la transition de Gate 4 (Validation QA -> Phase 5 SHIP) par l'évaluation automatique de 5 contrôles bloquants déterministes et l'exigence d'une signature humaine authentique,  
**afin d'** interdire formellement toute livraison logicielle en production sans certification QA complète et approbation explicite du Lead Architect / Product Owner.

---

## Contexte & Périmètre

### Contexte Métier
Actuellement, dans `src/core/lifecycle.py`, la méthode `approve_gate(gate_number=4)` est une coquille vide : elle autorise la transition vers `STAGE_5_SHIP` sans vérifier si la suite de tests a tourné, si des violations de standards existent ou si le Code Evidence Ledger est complet. De plus, aucun contrôle n'interdit à un sous-agent IA de signer sa propre recette.

Ce composant implémente le verrouillage constitutionnel de Gate 4 tel que spécifié dans l'ADR-0383 :
1. Présence obligatoire du rapport `memory/qa_certification_report.json`.
2. 100% de tests unitaires et d'intégration au vert (`all_passed: True`).
3. Zéro violation de standards AST (ADR-0202 / ADR-0369) sur le code produit.
4. Triangulation complète des 4 Piliers Gherkin (Nominal, Rejets, Résilience, Observabilité).
5. Signature humaine obligatoire (rejet formel de toute signature par entité artificielle ou agentique).

### In-Scope
- Implémentation des 5 contrôles bloquants dans `ProjectLifecycleManager.approve_gate(gate_number=4)` (`src/core/lifecycle.py`).
- Enrichissement de la commande CLI `python src/swarm.py gate-approve --gate 4 --approver <nom> --notes <notes>`.
- Blocage strict avec levée d'exceptions explicites (`ValueError` détaillant le motif de rejet exact).
- Banc de tests unitaires dédié `tests/test_lifecycle_gate4.py` couvrant les 5 scénarios de rejet et le chemin nominal.

### Out-of-Scope
- Refonte des autres portes (Gate 1, 2, 3 et 5 déjà stabilisées).
- Déploiement CI/CD distant externe.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Contrôle 1 : Présence et Intégrité du Rapport de Certification QA
* **Règle** : Le fichier `Projects/<P>/memory/qa_certification_report.json` doit exister physiquement et être un JSON valide.
* **Rejet** : `ValueError("Approbation de Gate 4 refusée : aucun rapport de certification QA...")`.

#### 2. Contrôle 2 : Suite de Tests 100% au Vert
* **Règle** : `report.is_certified == True` et `report.pytest_result.all_passed == True`.
* **Rejet** : `ValueError("Approbation de Gate 4 refusée : la suite de tests comporte X échecs...")`.

#### 3. Contrôle 3 : Zéro Violation Statique AST
* **Règle** : `report.ast_summary.passed == True` (0 violation ADR-0202 et ADR-0369).
* **Rejet** : `ValueError("Approbation de Gate 4 refusée : X violations de standards AST détectées...")`.

#### 4. Contrôle 4 : Zéro Blindspot sur les 4 Piliers Gherkin
* **Règle** : `report.cel_result.is_complete == True` (les 4 piliers Gherkin sont couverts).
* **Rejet** : `ValueError("Approbation de Gate 4 refusée : le Code Evidence Ledger présente des angles morts...")`.

#### 5. Contrôle 5 : Signature Humaine Obligatoire
* **Règle** : Le champ `approver` doit être non vide et ne doit pas correspondre à une signature robotique/IA (rejet des chaînes insensibles à la casse : `"ai"`, `"bot"`, `"agent"`, `"subagent"`, `"sentinel"`, `"swarm"`, `"antigravity"` seule sans Marco).
* **Validation** : Les signatures contenant "Marco", "Lead Architect", "Human", ou "Product Owner" sont acceptées.
* **Rejet** : `ValueError("Approbation de Gate 4 refusée : la Gate 4 exige obligatoirement une signature humaine formelle...")`.

---

## Parcours Interactif & API

### Contrats d'Échange CLI
- `python src/swarm.py gate-approve --project <P> --gate 4 --approver "Marco" --notes "Recette validée"` :
  - Si les 5 critères sont validés : transition réussie vers `STAGE_5_SHIP` et enregistrement de l'empreinte cryptographique.
  - Si un critère échoue : message d'erreur rouge explicite avec instruction corrective.

---

## Règles d'affaires
* **[Infranchissabilité de Gate 4 sans Certification]** : Aucune dérogation technique n'est possible pour contourner les échecs de tests ou de standards.
* **[Souveraineté Humaine Exclusive]** : La validation de conformité métier ne peut être accordée que par un humain responsable identifié.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Verrous Bloquants de Gate 4 et Gouvernance Opposable de Recette QA

  # 1. CHEMIN NOMINAL (Approbation Réussie avec Certification Conforme et Signature Humaine)
  Scénario: Transition nominale vers STAGE_5_SHIP après validation des 5 contrôles
    Étant donné un projet en étape STAGE_4_VALIDATE
    Et un rapport de certification QA attestant 100% de tests verts, 0 violation AST et CEL complet
    Quand l'approbateur humain "Marco" exécute gate-approve pour la Gate 4
    Alors la Gate 4 est enregistrée avec son empreinte cryptographique
    Et le projet transite avec succès vers l'étape STAGE_5_SHIP

  # 2. EXCEPTIONS & REJETS MÉTIER (Absence de Rapport QA)
  Scénario: Rejet immédiat si le rapport de certification QA est introuvable
    Étant donné un projet sans fichier qa_certification_report.json
    Quand un utilisateur tente d'approuver la Gate 4
    Alors le système lève une exception bloquante ordonnant d'exécuter validate-sprint

  # 3. EXCEPTIONS & REJETS MÉTIER (Échec de Tests ou Violation AST)
  Scénario: Rejet de Gate 4 si la suite comporte un échec ou violation AST
    Étant donné un rapport de certification signalant des échecs ou violations
    Quand l'utilisateur tente d'approuver la Gate 4
    Alors le système refuse la transition et liste les motifs bloquants

  # 4. RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Rejet de Signature par Bot / IA)
  Scénario: Rejet systématique de signature par une entité artificielle
    Étant donné un rapport de certification 100% conforme
    Quand un agent tente d'approuver la Gate 4 avec approver="bot" ou "sentinel"
    Alors le système rejette l'approbation pour absence de signature humaine obligatoire
```
