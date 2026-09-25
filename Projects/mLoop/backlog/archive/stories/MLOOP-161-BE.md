---
id: MLOOP-161-BE
jira_key: ''
epic_key: EPIC-15-DIRECTIVES-SSOT-ENFORCEMENT
type: Feature
title: ADR de Boot Enforcement des Directives SSOT et Amendement des Chartes AGENTS
tags:
- standards
- adr
- governance
- agents-md
origin: GRILL_PROJECT
source_ref: epic_project_directives_ssot_enforcement.md
macro_size: M
status: IN_ANALYZE
grill_me: DONE
layer: backend
invest_score: 6/6
created_at: '2026-09-22'
blocked_by:
- MLOOP-160-BE
---
# ADR de Boot Enforcement des Directives SSOT et Amendement des Chartes AGENTS

---

## Description
**En tant que** Système de Gouvernance mLoop,  
**je veux** consigner la décision d'application du chargement des directives sous forme d'un ADR indexé et amender les chartes d'instructions racine ainsi que la charte du projet concerné avec une clause explicite de source de vérité autoritaire,  
**afin de** rendre la règle traçable, citable et durablement opposable aux agents de tous les clients terminaux.

---

## Contexte & Périmètre

### Contexte Métier
Le principe selon lequel les directives d'un projet constituent ses lois fondamentales est abondamment documenté dans la documentation d'architecture du framework, mais n'a jamais été encodé comme décision formelle ni comme clause opposable dans les chartes d'instructions injectées à l'orchestrateur. De plus, la charte du projet ayant révélé l'incident ne mentionne même pas son propre répertoire de directives et pointe une source d'ingestion amont comme officielle, ce qui contredit sa véritable hiérarchie. Ce récit grave la décision et corrige ces incohérences.

### In-Scope
- Rédaction d'un ADR de type décision consignant l'application du chargement des directives et l'ancrage de la source de vérité canonique.
- Indexation de l'ADR dans le catalogue thématique des décisions d'architecture.
- Ajout d'une clause de chargement des directives et de source de vérité autoritaire dans la charte d'instructions racine, propagée à ses miroirs.
- Correction de la charte d'instructions du projet ayant révélé l'incident pour lister son répertoire de directives et déclarer sa source de vérité réelle.

### Out-of-Scope
- Le contrôle automatique de pré-vol vérifiant la présence et l'intégrité des directives (couvert par le récit du guardrail).
- La rédaction du protocole normatif autonome (couvert par le récit du protocole).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*

#### 1. Consignation de la Décision d'Architecture
* **Entrée Métier** : Les six décisions actées lors de la session d'entrevue de cadrage macro et le protocole normatif de hiérarchie SSOT.
* **Règles d'admissibilité & Validation** : L'ADR reçoit le prochain numéro libre du catalogue, confirmé au moment de sa création physique. Il n'écrase ni ne réécrit silencieusement aucun ADR antérieur.
* **Traitement & Algorithme Métier** : L'ADR documente le contexte de l'incident, la décision d'ajouter le contrôle conditionnel de pré-vol, la hiérarchie SSOT canonique et le caractère non-bloquant du contrôle.
* **Résultat Métier & Mutations** : Un nouvel ADR indexé dans le catalogue, plus les clauses ajoutées aux chartes racine et projet.
* **Cas de Rejet Métier** : Un ADR non indexé au catalogue, ou une réécriture destructive d'un ADR antérieur, ou une clause racine absente de ses miroirs, constitue un rejet.

#### 2. Amendement des Chartes d'Instructions
* **Entrée Métier** : La charte racine et la charte du projet concerné.
* **Règles d'admissibilité & Validation** : La clause racine doit apparaître dans la section des directives impératives et être présente à l'identique dans les fichiers miroirs après synchronisation.
* **Traitement & Algorithme Métier** : Ajout de la clause de chargement des directives et de source de vérité en phase active ; correction de la charte projet pour lister le répertoire de directives et déclarer la source de vérité canonique au lieu de la source amont.
* **Résultat Métier & Mutations** : Chartes alignées et cohérentes avec la hiérarchie réelle.
* **Cas de Rejet Métier** : Une charte projet continuant de désigner une source amont comme officielle est un rejet.

---

## Règles d'affaires

- **[ADR Additif Non-Écrasant]** : L'ADR n'annule aucun ADR antérieur ; il ajoute une couche de gouvernance sur la séquence d'amorçage et sur le protocole d'entrevue. Toute interaction avec un ADR existant se fait par bannière d'amendement, jamais par écrasement.
- **[Règle de Garde de Numérotation]** : Au moment de créer le fichier ADR, le prochain slot libre du catalogue est reconfirmé et le numéro est réattribué en cas de collision. La référence de travail est le numéro figé lors du cadrage.
- **[Clause de Chargement en Phase Active]** : La charte racine impose, en phase de planification et au-delà, la lecture des directives d'affaires et techniques du projet si elles existent, ainsi que l'identification de la source de vérité autoritaire avant tout cadrage, audit ou délégation.
- **[Parité Miroir des Chartes]** : Toute clause ajoutée à la charte racine est présente à l'identique dans ses fichiers miroirs, conformément au contrôle de parité existant.
- **[Correction de la Charte Projet]** : La charte du projet ayant révélé l'incident liste explicitement son répertoire de directives et déclare sa source de vérité consolidée comme autoritaire, la source amont étant reléguée au rang de source d'ingestion non autoritaire.

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit produit un ADR et amende des chartes d'instructions Markdown. Aucune API HTTP n'est exposée. Conformément à ADR-0319, l'absence de routes HTTP est consignée via la question ouverte **OQ-161-01**.

| Méthode | Route | Finalité |
|:---|:---|:---|
| N/A | N/A | Récit de gouvernance documentaire — aucune interface réseau |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-161-01** : Ce récit consigne une décision d'architecture et modifie des fichiers de chartes. Aucune API HTTP n'est exposée ni consommée. **[API de soumission à définir — sans objet pour un artefact documentaire]**

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Backlog d'Épopée** : [`backlog/epic_project_directives_ssot_enforcement.md`](../epics/epic_project_directives_ssot_enforcement.md)
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-161-BE_fact_dossier.md`](../../memory/evidence/MLOOP-161-BE_fact_dossier.md)
- 📄 **Récit Préalable** : Protocole Normatif de Hiérarchie SSOT (récit bloquant amont)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Catalogue des Décisions d'Architecture** : [`standards/adr-system/README.md`](../../../../standards/adr-system/README.md)
- 📜 **Protocole de Rigueur d'Écosystème** : [`standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md`](../../../../standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: ADR de Boot Enforcement des Directives SSOT et Amendement des Chartes AGENTS

  # CHEMIN NOMINAL
  Scénario: Traçabilité de la décision dans le catalogue
    Étant donné le catalogue des décisions d'architecture
    Quand l'ADR de boot enforcement est consigné
    Alors il apparaît indexé par thème avec un lien direct
    Et la clause de source de vérité autoritaire figure dans les chartes miroirs

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Rejet d'une réécriture destructive d'un ADR antérieur
    Étant donné une proposition d'ADR
    Mais qu'elle écrase silencieusement le contenu d'un ADR existant
    Quand la conformité au principe additif est évaluée
    Alors la proposition est rejetée
    Et l'exigence de bannière d'amendement est rappelée

  # RÉSILIENCE & COHÉRENCE
  Scénario: Collision de numérotation au moment du build
    Étant donné une référence de numéro d'ADR figée lors du cadrage
    Mais qu'un autre ADR a occupé ce numéro entretemps
    Quand le fichier est créé physiquement
    Alors le prochain slot libre est reconfirmé
    Et le numéro est réattribué sans collision

  # OBSERVABILITÉ & PARITÉ
  Scénario: Parité miroir de la clause racine
    Étant donné la clause ajoutée à la charte racine
    Quand le contrôle de parité miroir s'exécute
    Alors la clause est présente à l'identique dans tous les fichiers miroirs
    Et la charte du projet concerné déclare sa source de vérité consolidée comme autoritaire
```