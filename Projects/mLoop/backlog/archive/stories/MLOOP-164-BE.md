---
id: MLOOP-164-BE
jira_key: ''
epic_key: EPIC-15-DIRECTIVES-SSOT-ENFORCEMENT
type: Feature
title: Suite de Tests du Contrôle des Directives et Réalignement sur la Sémantique Tri-État
tags:
- tests
- vibe-check
- quality
- parity
origin: GRILL_PROJECT
source_ref: epic_project_directives_ssot_enforcement.md
macro_size: M
status: DONE_TESTED
grill_me: DONE
layer: backend
invest_score: 6/6
created_at: '2026-09-22'
blocked_by:
- MLOOP-163-BE
---
# Suite de Tests du Contrôle des Directives et Réalignement sur la Sémantique Tri-État

---

## Description
**En tant qu'** Ingénieur qualité du framework mLoop,  
**je veux** une suite de tests paramétrée couvrant les cas conditionnels du nouveau contrôle des directives, ainsi que le réalignement des tests de pré-vol existants qui encodaient l'ancienne sémantique binaire du verdict,  
**afin de** garantir que la suite de tests reste intégralement verte avec la nouvelle règle à trois états, sans chercher à préserver les anciens scores des projets.

---

## Contexte & Périmètre

### Contexte Métier
L'introduction du contrôle des directives et le passage à une sémantique de verdict à trois états modifient le comportement du guardrail de pré-vol. Certains tests existants encodent l'hypothèse que tout état non réussi équivaut à un échec. Ces tests doivent être réalignés volontairement sur la nouvelle règle. La décision de cadrage assume que les projets sont recalculés au fil de l'eau, ce qui écarte toute exigence de parité de score entre projets, mais impose que la suite de tests du framework reste verte.

### In-Scope
- Rédaction d'une suite de tests paramétrée couvrant les cas conditionnels du contrôle des directives.
- Réalignement explicite des tests de pré-vol existants sur la sémantique à trois états.
- Confirmation de l'absence de dérive du guide des commandes.

### Out-of-Scope
- L'implémentation du contrôle lui-même et du calcul tri-état (couverts par leur récit).
- Toute garantie de conservation des scores antérieurs des projets, explicitement écartée par la décision de cadrage.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*

#### 1. Couverture Paramétrée du Contrôle des Directives
* **Entrée Métier** : Les différents états possibles d'un projet vis-à-vis de ses directives.
* **Règles d'admissibilité & Validation** : La suite couvre au minimum cinq cas distincts représentatifs des comportements conditionnels et de la sémantique tri-état.
* **Traitement & Algorithme Métier** : Chaque cas simule un état de projet et vérifie l'état de contrôle attendu ainsi que l'effet sur le verdict global.
* **Résultat Métier & Mutations** : Une suite de tests dédiée validant le comportement du contrôle des directives.
* **Cas de Rejet Métier** : Une suite ne couvrant pas le cas du projet sans directives, ou ne vérifiant pas qu'un avertissement n'invalide pas le verdict, est insuffisante.

#### 2. Réalignement des Tests Existants
* **Entrée Métier** : Les tests de pré-vol existants encodant l'ancienne sémantique binaire.
* **Règles d'admissibilité & Validation** : Les tests concernés sont mis à jour pour refléter la sémantique à trois états, et l'exécution complète de la suite est intégralement verte.
* **Traitement & Algorithme Métier** : Identification des assertions dépendant de l'ancien calcul et mise à jour volontaire de ces assertions.
* **Résultat Métier & Mutations** : Une suite de tests globale alignée sur la nouvelle règle et intégralement verte.
* **Cas de Rejet Métier** : Une suite laissée en échec, ou une tentative de préserver artificiellement l'ancienne sémantique, constitue un rejet.

---

## Règles d'affaires

- **[Couverture Paramétrée Minimale]** : Les cas couverts incluent au minimum les directives conformes qui réussissent, l'absence totale de directives qui réussit, des directives présentes sans source de vérité déclarée qui avertissent, des lois d'affaires ou techniques vides qui avertissent, et la vérification qu'un avertissement ne fait pas basculer le verdict global en échec.
- **[Réalignement Explicite Assumé]** : Les tests existants encodant l'ancienne sémantique binaire sont mis à jour de façon volontaire et documentée. Il ne s'agit pas d'une garantie de non-régression passive mais d'un réalignement délibéré. L'objectif final est une suite de tests intégralement verte.
- **[Zéro Dérive du Guide des Commandes]** : Aucune nouvelle commande n'est ajoutée au registre des commandes, les contrôles étant internes au guardrail de pré-vol. Aucune synchronisation du guide des commandes n'est donc requise.

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit produit et réaligne des tests Python. Aucune API HTTP n'est exposée : les interfaces sont des appels de fonction de test internes. Conformément à ADR-0319, l'absence de routes HTTP est consignée via la question ouverte **OQ-164-01**.

| Méthode | Interface interne | Finalité |
|:---|:---|:---|
| Test | `tests/test_vibe_check_directives_ssot.py` | Suite paramétrée du contrôle des directives |
| Test | `tests/test_vibe_check_*.py` (existants) | Réalignement sur la sémantique tri-état |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-164-01** : Ce récit crée et modifie des fichiers de tests Python. Aucune API HTTP n'est exposée ni consommée. **[API de soumission à définir — sans objet pour une suite de tests]**

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Backlog d'Épopée** : [`backlog/epic_project_directives_ssot_enforcement.md`](../epics/epic_project_directives_ssot_enforcement.md)
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-164-BE_fact_dossier.md`](../../memory/evidence/MLOOP-164-BE_fact_dossier.md)
- 📄 **Récit Préalable** : Contrôle de Pré-Vol d'Intégrité des Directives Projet (récit bloquant amont)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Suite de Tests du Guardrail** : [`tests/`](../../../../tests/)
- 📜 **Protocole de Rigueur d'Écosystème** : [`standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md`](../../../../standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Suite de Tests du Contrôle des Directives et Réalignement sur la Sémantique Tri-État

  # CHEMIN NOMINAL
  Scénario: Exécution de la suite paramétrée du contrôle des directives
    Étant donné les cas paramétrés couvrant les états conditionnels du contrôle
    Quand la suite de tests dédiée est exécutée
    Alors tous les cas paramétrés passent
    Et la suite complète du guardrail reste intégralement verte

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Détection d'un test laissé en échec
    Étant donné un test existant encodant l'ancienne sémantique binaire
    Mais qu'il n'a pas été réaligné sur la sémantique à trois états
    Quand la suite complète est exécutée
    Alors l'échec est détecté
    Et le récit n'est pas considéré comme terminé tant que la suite n'est pas verte

  # RÉSILIENCE & COHÉRENCE
  Scénario: Absence de dérive du guide des commandes
    Étant donné l'ajout des contrôles internes au guardrail de pré-vol
    Quand la parité du guide des commandes est vérifiée
    Alors aucune commande nouvelle n'est détectée
    Et aucune synchronisation du guide n'est requise

  # OBSERVABILITÉ & COUVERTURE
  Scénario: Vérification de la couverture des cinq cas minimaux
    Étant donné la suite de tests dédiée au contrôle des directives
    Quand la couverture est inspectée
    Alors les cinq cas minimaux sont présents
    Et le cas du projet sans directives est explicitement couvert
```