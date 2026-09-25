---
id: MLOOP-322-BE
jira_key: ""
epic_key: EPIC-32
type: Feature
title: Garde Mécanique FSM & Verrou Anti-Promotion Directe en READY_FOR_DEV dans GrillEngine
tags:
- governance
- core-python
- fsm
- lifecycle
status: DONE_TESTED
layer: backend
invest_score: 6/6
macrostructure: ""
ttl_cycles: 3
validated_by: 'PO (Marco)'
validated_at: '2026-09-25T08:23:19-04:00'
content_hash: 7182d808e10a7564
blocked_by: ["MLOOP-320-BE"]
---
# Garde Mécanique FSM & Verrou Anti-Promotion Directe en READY_FOR_DEV dans GrillEngine

---

## Description
**En tant que** Développeur Système et Gardien de l'Intégrité de la Plateforme,  
**je veux** implémenter dans [`src/pipelines/state_machine.py`](file:///C:/Memory%20Loop/src/pipelines/state_machine.py) et [`src/pipelines/grill/_engine.py`](file:///C:/Memory%20Loop/src/pipelines/grill/_engine.py) l'exception dédiée `LifecycleAuthorityError`, supprimer les sauts directs `DRAFT ➔ READY_FOR_DEV` dans la table des transitions FSM, et brider mécaniquement toute tentative de mutation de stories lors des commandes de grill macro transverses,  
**afin d'** interdire techniquement à tout agent conversationnel ou script autonome de contourner l'autorité humaine exclusive requise pour la Gate 2.

---

## Contexte & Périmètre

### Contexte Métier
L'architecture de gouvernance mLoop repose sur une étanchéité absolue entre la proposition d'alignement de l'IA (plafonnée à `READY_FOR_GROOMING`) et l'autorisation d'engagement physique des ressources (réservée à l'humain sous `READY_FOR_DEV` en Gate 2). Des failles structurelles dans le code Python ont permis à des processus autonomes de promouvoir directement des ébauches au statut de développement. Ce récit érige les verrous logiciels indispensables au niveau du runtime pour garantir le principe du Fail-Closed strict.

### In-Scope
- Modification de [`src/pipelines/state_machine.py`](file:///C:/Memory%20Loop/src/pipelines/state_machine.py) :
  - Déclaration de la classe d'exception `LifecycleAuthorityError(StateTransitionError)`.
  - Assainissement de la table `ALLOWED_TRANSITIONS` : suppression définitive de `READY_FOR_DEV` depuis `DRAFT` et `OPEN`. Seul l'état `READY_FOR_GROOMING` est habilité à transiter vers `READY_FOR_DEV`.
  - Enrichissement de `validate_transition` : lors d'une transition cible vers `READY_FOR_DEV`, vérification obligatoire des métadonnées du récit (`validated_by` non vide et sans signature de bot, `validated_at` au format ISO-8601 valide) avec levée de `LifecycleAuthorityError` en cas de non-conformité.
- Modification de [`src/pipelines/grill/_engine.py`](file:///C:/Memory%20Loop/src/pipelines/grill/_engine.py) :
  - Bridage strict de `mark_story_grilled` : verrouillage au statut `READY_FOR_GROOMING` et levée de `LifecycleAuthorityError` si `READY_FOR_DEV` est requis par une commande machine.
  - Ajout de la méthode de protection `assert_no_story_mutation(scope: str)` interdisant tout accès en écriture sur `backlog/stories/` lorsque le scope est `EPIC` ou `PROJECT`.
- Modification de [`src/pipelines/grill/_cli_handler.py`](file:///C:/Memory%20Loop/src/pipelines/grill/_cli_handler.py) :
  - Interception des arguments illicites et journalisation structurée de toute infraction dans [`memory/audit_lifecycle_violations.jsonl`](file:///C:/Memory%20Loop/Projects/mLoop/memory/audit_lifecycle_violations.jsonl).

### Out-of-Scope
- Sonde de détection d'écriture en rafale sous 60 secondes Check 28 dans `vibe_check.py` (`MLOOP-323-BE`).
- Suite de tests unitaires et de bout en bout (`MLOOP-324-FULL`).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend / fullstack)*
#### 1. Verrouillage Logiciel du Moteur de Cycle de Vie
* **Entrée Métier** : Décisions d'arbitrage issues du micro-grill `ADR-019` et cadrage `ADR-017`.
* **Règles d'admissibilité & Validation** : Respect strict du modèle FSM à 5 phases de l'ADR-0391 et zéro régression sur les transitions légitimes.
* **Traitement & Algorithme Métier** :
  1. Instancier la classe d'exception `LifecycleAuthorityError(StateTransitionError)` avec message explicatif normé.
  2. Épurer `ALLOWED_TRANSITIONS[StoryStatus.DRAFT]` et `ALLOWED_TRANSITIONS[StoryStatus.OPEN]` de toute mention de `StoryStatus.READY_FOR_DEV`.
  3. Conditionner la transition vers `READY_FOR_DEV` à la validation nominative humaine de `validated_by` et `validated_at`.
  4. Sécuriser `mark_story_grilled` pour garantir que seul `READY_FOR_GROOMING` est positionné.
  5. Imposer un arrêt d'exécution avec code de sortie `1` et consigner l'incident dans `memory/audit_lifecycle_violations.jsonl`.
* **Résultat Métier & Mutations** : Fichiers `src/pipelines/state_machine.py`, `src/pipelines/grill/_engine.py` et `src/pipelines/grill/_cli_handler.py` sécurisés et opérationnels.
* **Cas de Rejet Métier** : Toute tentative d'auto-promotion ou de mutation transverse sans mandat explicite est rejetée avec levée immédiate de `LifecycleAuthorityError`.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
> *Définition déclarative des interfaces normatives de gouvernance.*

#### Matrice des Contrats API
> 📌 **Clause d'Exemption (ADR-0319 / OQ-322-01)** : Récit d'ingénierie interne modifiant le moteur FSM et le gestionnaire CLI Python (`src/pipelines/state_machine.py`, `src/pipelines/grill/_engine.py`, `src/pipelines/grill/_cli_handler.py`). Aucune route API HTTP REST exposée, interfaces de transport réseau déclarées à définir comme sans objet externe.

| Contrat / Interface | Type | Direction | Format / Schéma | Description |
| :--- | :---: | :---: | :--- | :--- |
| `StateMachineEngine.validate_transition` | Méthode Python | Interne | `current, target, story_data` | Validation stricte de la transition et de l'autorité |
| `GrillEngine.assert_no_story_mutation` | Méthode Python | Interne | `scope: str` | Barrière d'écriture interdisant les mutations en macro |

---

## Règles d'affaires

- **Inviolabilité de la Transition READY_FOR_DEV** : Aucun composant logiciel ne peut faire transiter un récit directement vers `READY_FOR_DEV` depuis `DRAFT` ou `OPEN`. Le passage préalable par `READY_FOR_GROOMING` est un prérequis technique absolu.
- **Autorité Nominative Humaine Non Substituable** : L'état `READY_FOR_DEV` requiert obligatoirement un champ `validated_by` signé par une personne physique et un horodatage `validated_at` au format ISO-8601.
- **Fail-Closed Immédiat** : Toute infraction aux règles d'autorité déclenche l'exception `LifecycleAuthorityError`, interrompt le script avec code `1` et produit une trace d'audit.
- **Étanchéité du Scope Macro Transverse** : L'exécution d'un grill sur un périmètre transverse (`EPIC` ou `PROJECT`) a l'interdiction technique absolue de modifier les fichiers sous `backlog/stories/`.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-322-BE_fact_dossier.md`](../../memory/evidence/MLOOP-322-BE_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Micro-Grill MLOOP-322-BE** : [`Projects/mLoop/docs/01-architecture/ADR-019_micro-grill_mloop-322-be__2_decisions.md`](../../docs/01-architecture/ADR-019_micro-grill_mloop-322-be__2_decisions.md)
- 📜 **Standard Système Découplage & Anti-Cascade** : [ADR-0393](../../standards/adr-system/0393-decouplage-modalite-grill-scope-anti-cascade.md)
- 🏛️ **Cadrage Macro EPIC-32** : [`Projects/mLoop/docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md`](../../docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md)
- 📋 **Constitution Agentique mLoop** : [AGENTS.md](../../AGENTS.md)
- 🧭 **Protocole de Cycle de Vie des Récits** : [STORY_LIFECYCLE_PROTOCOL.md](../../standards/protocols/STORY_LIFECYCLE_PROTOCOL.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Garde Mécanique FSM & Verrou Anti-Promotion Directe dans GrillEngine

  # CHEMIN NOMINAL (Happy Path & Arrêt Déterministe)
  Scénario: Promotion légitime d'un récit au statut READY_FOR_GROOMING par GrillEngine
    Étant donné un récit au statut IN_ANALYZE ayant complété son micro-grill
    Quand la méthode mark_story_grilled est exécutée par le moteur
    Alors le statut du récit est positionné à READY_FOR_GROOMING
    Et le hash cryptographique anti-altération est calculé et scellé
    Et le moteur ne tente aucune promotion vers READY_FOR_DEV

  # EXCEPTIONS & REJETS MÉTIER (Tentative de Cascade Non Sollicitée)
  Scénario: Levée de LifecycleAuthorityError lors d'une tentative d'auto-promotion vers READY_FOR_DEV
    Étant donné un script ou agent tentant de forcer la transition vers READY_FOR_DEV
    Mais constatant l'absence de signature humaine valide dans validated_by
    Quand la méthode validate_transition de la machine à états est appelée
    Alors une exception LifecycleAuthorityError est immédiatement levée
    Et l'incident est consigné dans le journal memory/audit_lifecycle_violations.jsonl
    Et l'exécution est interrompue avec un code de retour égal à 1

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Anti-Rebond, Concurrence & Timeouts)
  Scénario: Résilience face aux accès concurrents sous 500 millisecondes et perte réseau
    Étant donné deux processus concurrents invoquant la validation de transition
    Mais qu'un double-clic ou des appels simultanés sous 500 millisecondes se produisent
    Quand le verrou de transition FSM évalue la requête
    Alors un verrouillage atomique sérialise les accès aux fichiers de métadonnées
    Et la corruption de statut est prévenue même en cas de session expirée, timeout ou coupure réseau
    Et l'état cohérent est préservé sous 500 millisecondes

  # UX, OBSERVABILITÉ & VALIDATION DES SAISIES (Validation des Entrées Incomplètes)
  Scénario: Détection de métadonnées incomplètes ou champ vide lors du contrôle d'autorité
    Étant donné une requête de transition vers READY_FOR_DEV avec un champ vide ou des données partielles
    Quand le validateur inspecte les métadonnées validated_by et validated_at
    Alors la transition est rejetée avec un message explicite détaillant les champs manquants
    Et le récit conserve son statut d'origine sans altération partielle
    Et une alerte de validation d'autorité est émise dans la console
```