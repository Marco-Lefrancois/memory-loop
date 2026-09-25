---
id: MLOOP-200-BE
jira_key: ''
epic_key: EPIC-20-PORTFOLIO-GOVERNANCE
type: Feature
title: Réaligner l'état de cycle de vie des projets actifs sur la vérité du CLI
tags:
- governance
- lifecycle
- portfolio
status: DONE
grill_me: DONE
layer: backend
invest_score: 6/6
macro_size: M
origin: DIRECT_REQUIREMENT
source_ref: epic_portfolio_governance_2026q4.md
blocked_by: []
created_at: '2026-09-23'
ttl_cycles: 3
---
# Réaligner l'état de cycle de vie des projets actifs sur la vérité du CLI

---

## Description
**En tant qu'** Orchestrateur mLoop,
**je veux** que l'état de cycle de vie de chaque projet actif reflète fidèlement la phase prouvée par le CLI et le backlog,
**afin de** rétablir la cohérence entre le badge de phase affiché et l'état réel du portefeuille, sans re-validation artificielle de portes déjà franchies.

---

## Contexte & Périmètre

### Contexte Métier
Le portefeuille mLoop affiche des badges de phase hétérogènes : certains fichiers d'état restent à leur état d'initialisation alors que le backlog et les contrôles pré-vol attestent d'une phase avancée. L'écart de confiance entre le badge et la réalité ralentit le pilotage du portefeuille et la séquence de gouvernance.

### In-Scope
- Audit du décalage phase CLI vs fichier d'état pour : Metro_FOOD, Metro_COMMERCE, Metro_SANTE, BoireFrere_Segment2, Shopify_AI_Item_Creator.
- Reconstruction des données manquantes (`current_stage`, `gates`) dans le fichier d'état de chaque projet, uniquement à partir des preuves CLI + backlog.
- Conservation de la sémantique « module conducteur » sur BoireFrere_Segment2 (le stage reflète le module Incubation) avec traçage explicite du mapping module→stage.
- Traçage du delta avant/après dans l'EvidencePack du récit.
- Validation post-correction par le contrôle pré-vol sur chacun des 5 projets.

### Out-of-Scope
- Toute modification du moteur de cycle de vie sous le cadre source du framework.
- Re-validation rétroactive de portes déjà franchies (aucune approbation gate passée n'est rejouée).
- Promotion automatique de récits de backlog vers un statut d'exécution.
- Correction du corps des récits métier (sujet d'entretiens dédiés).
- Initialisation de nouveaux projets.
- Correction du corps des récits legacy déjà livrés au client.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Reconstruction de l'état de cycle de vie
* **Entrée Métier** : Fichier d'état du projet + sortie du contrôle de cycle de vie + tableau de bord de sprint du projet cible.
* **Règles d'admissibilité & Validation** : Seules les phases **prouvées** par le CLI et le backlog sont écriptibles ; toute phase non prouvée reste à l'état minimal d'initialisation.
* **Traitement & Algorithme Métier** : Lecture de la vérité CLI, alignement des champs d'état, persistance atomique du fichier JSON, sans écriture dans le cadre source du framework.
* **Résultat Métier & Mutations** : Fichier d'état conforme au schéma du moteur, phase affichée = phase prouvé, delta tracé dans l'EvidencePack.
* **Cas de Rejet Métier** : Rejet si la preuve CLI/backlog est absente ou contradictoire pour un projet ; le projet est alors laissé intact et signalé comme exception documentée.

#### 2. Sémantique module conducteur (BoireFrere_Segment2)
* **Entrée Métier** : État du projet + mapping module→phase issu du tableau de bord modulaire.
* **Règles d'admissibilité & Validation** : La phase affichée décrit le module le plus avancé (Incubation) ; les autres modules ne déclenchent aucune écriture de phase.
* **Traitement & Algorithme Métier** : Conservation de la phase module conducteur, annotation du mapping dans les preuves, aucun bascule vers une moyenne multi-modules.
* **Résultat Métier & Mutations** : Badge stable + note de sémantique module dans l'EvidencePack.
* **Cas de Rejet Métier** : Rejet si le mapping module→phase n'est pas traçable dans le tableau de bord.

#### Matrice des Contrats API
N/A — Récit de gouvernance d'état fichier local 100% headless : aucune route REST/CTA n'est exposée, consommée ou modifiée.
- **OQ-200 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API — opération sur fichiers `lifecycle_state.json` sans interface HTTP `[API de soumission à définir]` ; toute future exposition d'API est à confirmer dans un récit dédié avec sa propre matrice.
- **Admission of Limits** : Les avertissements génériques rubber-duck (anti-rebond, expiration de session, validation de saisie) sont hors domaine pour ce composant headless (ni UI, ni API distante) ; la résilience fichier local est couverte par le Pilier 2 (fichier hors schéma, preuve absente, échec partiel).

---

## Règles d'affaires

- **Primauté de la preuve de phase** : En cas de conflit entre le fichier d'état et le CLI/backlog, la preuve CLI + backlog gagne ; le fichier est reconstruit, jamais l'inverse.
- **Zéro re-gate rétroactive** : Les portes déjà franchies ne sont pas re-soumises à approbation humaine ; seule l'approbation du présent récit valide l'écriture.
- **Sémantique module conducteur** : Sur un projet à modules, la phase affichée décrit le module le plus avancé et ce sens est documenté à l'écriture.
- **Refus sur preuve absente** : Sans preuve CLI/backlog exploitable, le fichier d'état reste inchangé et l'anomalie est consignée.
- **Gestion des données invalides** : Un fichier illisible ou hors schéma est reconstruit depuis la dernière preuve CLI valide, avec trace du remplacement dans l'EvidencePack.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-200-BE_fact_dossier.md`](../../memory/evidence/MLOOP-200-BE_fact_dossier.md)
- 🏛️ **Décisions de cadrage** : Q1 reconstruction depuis CLI/backlog · Q2 réécriture données seule · Q3b sémantique module conducteur (Grill-Me 2026-09-23)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **Protocole de cycle de vie** : [PROJECT_LIFECYCLE_STAGES.md](../../../standards/protocols/PROJECT_LIFECYCLE_STAGES.md)
- 📜 **Gouvernance des portes** : [ADR-0339](../../../standards/adr-system/0339-project-lifecycle-stages-governance-gates.md)
- 📜 **Architecture modulaire** : [ADR-0342](../../../standards/adr-system/0342-modular-project-architecture-and-subdomain-isolation.md)

### 3. Paquet OpenSpec (Handoff Développeur)
- 📄 **Épopée de rattachement** : [`backlog/epics/epic_portfolio_governance_2026q4.md`](../epics/epic_portfolio_governance_2026q4.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Réaligner l'état de cycle de vie des projets actifs sur la vérité du CLI

  # 1. NOMINAL (Happy Path & Persistance)
  Scénario: Reconstruction d'un état désaligné depuis la preuve CLI
    Étant donné un projet actif dont le fichier d'état indique l'initialisation
    Et que le contrôle de cycle de vie atteste une phase supérieure prouvée par le backlog
    Quand l'orchestrateur reconstruit l'état du projet
    Alors le fichier d'état affiche la phase prouvée
    Et le décalage avant/après est consigné dans les preuves du récit

  Scénario: Validation post-correction sans anomalie
    Étant donné les cinq projets actifs réalignés
    Quand le contrôle pré-vol est exécuté sur chacun d'eux
    Alors aucun échec bloquant n'est remonté pour la cohérence d'état

  # 2. EXCEPTIONS (Cas d'erreur & Rejets métier)
  Scénario: Refus d'écriture faute de preuve de phase
    Étant donné un projet actif sans preuve de phase exploitable dans le CLI ni le backlog
    Quand l'orchestrateur tente le réalignement
    Alors le fichier d'état reste inchangé
    Et l'exception est documentée dans les preuves du récit

  Scénario: Fichier d'état hors schéma
    Étant donné un projet dont le fichier d'état est illisible ou hors schéma
    Quand l'orchestrateur reconstruit l'état depuis la dernière preuve CLI valide
    Alors le fichier résultant est conforme au schéma du moteur
    Et le remplacement est tracé dans les preuves

  # 3. RÉSILIENCE (Réseau / Timeout / Mode dégradé)
  Scénario: Préserver les phases déjà justes
    Étant donné un projet dont l'état correspond déjà à la preuve CLI
    Quand l'orchestrateur exécute le réalignement
    Alors aucune écriture destructive n'a lieu
    Et le contrôle pré-vol reste au même niveau de résultat qu'avant

  Scénario: Échec partiel sans cascade
    Étant donné plusieurs projets cibles
    Quand la reconstruction échoue sur l'un d'eux
    Alors les autres projets sont traités indépendamment
    Et l'échec est isolé au projet fautif sans bloquer le portefeuille

  # 4. UX / ACCESSIBILITÉ / ÉTAT VIDE
  Scénario: Badge de phase cohérent pour le pilote portefeuille
    Étant donné le tableau de bord de pilotage du portefeuille
    Après le réalignement des cinq projets
    Alors chaque badge de phase correspond à la phase affichée par le contrôle de cycle de vie
    Et la sémantique module conducteur est lisible dans les preuves du récit

  Scénario: Projet sans état de cycle de vie
    Étant donné un projet actif sans fichier d'état de cycle de vie
    Quand l'orchestrateur inspecte le portefeuille
    Alors l'absence est signalée sans créer d'état fictionnel
```
