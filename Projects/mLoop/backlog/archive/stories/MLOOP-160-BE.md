---
id: MLOOP-160-BE
jira_key: ''
epic_key: EPIC-15-DIRECTIVES-SSOT-ENFORCEMENT
type: Feature
title: Protocole Normatif de Hiérarchie SSOT et Chargement des Directives Projet
tags:
- standards
- protocols
- governance
- ssot
origin: GRILL_PROJECT
source_ref: epic_project_directives_ssot_enforcement.md
macro_size: S
status: DONE_TESTED
grill_me: DONE
layer: backend
invest_score: 6/6
created_at: '2026-09-22'
blocked_by: []
---
# Protocole Normatif de Hiérarchie SSOT et Chargement des Directives Projet

---

## Description
**En tant qu'** Architecte en Chef mLoop,  
**je veux** un protocole normatif court et déterministe déclarant la hiérarchie documentaire (SSOT canonique > sources d'ingestion amont > staging local) et l'obligation de charger les directives d'un projet avant tout cadrage, audit ou délégation,  
**afin d'** éliminer définitivement la classe d'erreur qui a conduit un agent à auditer des récits sur des sources non autoritaires, produisant un faux diagnostic de conflit de modèle de données.

---

## Contexte & Périmètre

### Contexte Métier
L'écosystème mLoop encadre plusieurs projets simultanés, chacun pouvant déclarer sa propre source de vérité documentaire et ses propres lois d'affaires. Or aucun document normatif transverse ne fixe l'ordre de priorité entre une source de vérité consolidée, une source d'ingestion amont et un staging brut, ni n'impose de localiser cette source de vérité avant d'agir. Cette lacune a permis qu'une analyse soit conduite sur des documents amont non autoritaires alors que la hiérarchie était déjà tranchée dans les lois d'affaires du projet concerné. Ce protocole comble ce vide en établissant une règle universelle, citable et opposable.

### In-Scope
- Rédaction d'un protocole autonome et court établissant la hiérarchie documentaire à trois niveaux.
- Formalisation de l'obligation de localiser et citer la source de vérité canonique avant toute délégation d'analyse.
- Catalogue des directives projet impératives que le chargement obligatoire garantit de considérer.

### Out-of-Scope
- L'implémentation du contrôle automatique vérifiant le respect de ce protocole (couvert par le récit du guardrail de pré-vol).
- L'amendement des chartes d'instructions racine et des personas (couvert par le récit de décision d'architecture).
- Le renforcement des compétences d'interrogatoire (couvert par le récit du skill d'entrevue).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*

#### 1. Rédaction du Protocole de Hiérarchie SSOT
* **Entrée Métier** : Le constat documenté de l'incident fondateur et le catalogue des directives projet impératives découvertes.
* **Règles d'admissibilité & Validation** : Le document doit être autonome, concis (cible d'environ quarante lignes), rédigé en style déclaratif normatif, et placé sous le répertoire des protocoles standards.
* **Traitement & Algorithme Métier** : Le protocole énonce la hiérarchie à trois niveaux, l'obligation de localisation préalable et le catalogue des directives impératives, avec une distinction explicite entre les deux mécanismes de gouvernance.
* **Résultat Métier & Mutations** : Un nouveau fichier de protocole normatif disponible comme point d'ancrage citable par la décision d'architecture et le guardrail de pré-vol.
* **Cas de Rejet Métier** : Un protocole enfoui dans un document existant, ou dépassant significativement la cible de concision, ou omettant l'un des trois niveaux de hiérarchie, est refusé.

---

## Règles d'affaires

- **[Hiérarchie Documentaire à Trois Niveaux]** : Niveau 1, la source de vérité canonique déclarée par le projet (par exemple le modèle de données consolidé) fait foi absolue. Niveau 2, les sources d'ingestion amont ne sont pas autoritaires en cas de divergence avec le niveau 1. Niveau 3, le staging brut local n'est jamais lu directement ni jamais autoritaire.
- **[Obligation de Localisation Avant Délégation]** : Avant de déléguer une tâche d'audit ou d'analyse à un sous-agent, l'orchestrateur doit avoir identifié et cité la source de vérité canonique du projet actif.
- **[Catalogue de Directives Projet Impératives]** : Le protocole liste les directives projet impératives que le chargement obligatoire garantit de considérer, quelle que soit leur nature, avec des cas réels démontrant pourquoi la lecture forcée existe. Aucune de ces directives n'est un exemple négligeable.
- **[Distinction des Deux Mécanismes de Gouvernance]** : Le protocole distingue le mécanisme du contrôle mécanique générique (pour les principes universels) du mécanisme du chargement forcé (pour les directives propres à un projet).

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit produit un artefact documentaire normatif (protocole standards). Aucune API HTTP n'est exposée. Conformément à ADR-0319, l'absence de routes HTTP est consignée via la question ouverte **OQ-160-01**.

| Méthode | Route | Finalité |
|:---|:---|:---|
| N/A | N/A | Récit de gouvernance documentaire — aucune interface réseau |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-160-01** : Ce récit crée un protocole normatif Markdown sous `standards/protocols/`. Aucune API HTTP n'est exposée ni consommée. **[API de soumission à définir — sans objet pour un artefact documentaire]**

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Backlog d'Épopée** : [`backlog/epic_project_directives_ssot_enforcement.md`](../epics/epic_project_directives_ssot_enforcement.md)
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-160-BE_fact_dossier.md`](../../memory/evidence/MLOOP-160-BE_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Protocole de Rigueur d'Écosystème** : [`standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md`](../../../../standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md)
- 📜 **ADR d'Architecture (à créer)** : ADR-0384 — Application du Chargement des Directives Projet & Ancrage SSOT Canonique

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Protocole Normatif de Hiérarchie SSOT et Chargement des Directives Projet

  # CHEMIN NOMINAL
  Scénario: Consultation du protocole avant délégation d'audit
    Étant donné un orchestrateur sur le point de déléguer un audit à un sous-agent
    Quand il consulte le protocole de hiérarchie SSOT
    Alors il identifie la source de vérité canonique déclarée par le projet actif
    Et il cite cette source de vérité dans le brief transmis au sous-agent

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Refus d'un protocole enfoui dans un document existant
    Étant donné une proposition de rédaction du protocole
    Mais que la hiérarchie SSOT est insérée comme sous-section d'un protocole préexistant
    Quand la conformité au périmètre est évaluée
    Alors la proposition est rejetée
    Et l'exigence de fichier autonome citable est rappelée

  # RÉSILIENCE & COHÉRENCE
  Scénario: Divergence entre source canonique et source amont
    Étant donné un projet dont la source amont contredit la source canonique
    Quand un agent applique le protocole
    Alors il retient exclusivement la source canonique de niveau 1
    Et il consigne la divergence comme incohérence sourcée sans inventer de structure de remplacement

  # OBSERVABILITÉ & TRAÇABILITÉ
  Scénario: Traçabilité du catalogue de directives impératives
    Étant donné le protocole rédigé
    Quand un lecteur consulte la section catalogue
    Alors les directives projet impératives sont listées avec des cas réels
    Et la distinction entre les deux mécanismes de gouvernance est explicite
```