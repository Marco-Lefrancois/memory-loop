---
id: MLOOP-323-BE
jira_key: ''
epic_key: EPIC-32
type: Feature
title: Contrôle de Gating CLI & Sonde de Détection de Cascade (Check 28 Vibe-Check)
tags:
- governance
- cli
- vibe-check
- anti-cascade
status: DONE_TESTED
layer: backend
invest_score: 6/6
macrostructure: ''
ttl_cycles: 3
validated_by: PO (Marco)
validated_at: '2026-09-25T08:28:06-04:00'
content_hash: a660e6241c71b25a
blocked_by:
- MLOOP-321-BE
- MLOOP-322-BE
---
# Contrôle de Gating CLI & Sonde de Détection de Cascade (Check 28 Vibe-Check)

---

## Description
**En tant qu'** Auditeur Qualité et Développeur de la Plateforme mLoop,  
**je veux** intégrer dans le harnais de vérification pré-vol [`src/pipelines/vibe_check/`](file:///C:/Memory%20Loop/src/pipelines/vibe_check/) la sonde Check 28 (*Story Cascade Drift Check*) pour déceler toute promotion groupée de récits sans preuve unitaire, et étendre le registre CLI [`src/commands/_registry/_reg_pipelines_arch.py`](file:///C:/Memory%20Loop/src/commands/_registry/_reg_pipelines_arch.py) avec les arguments `--format` et `--scope`,  
**afin d'** interdire techniquement le passage en qualification de sprint si des récits ont été générés en cascade sans séance d'arbitrage 1:1 dédiée.

---

## Contexte & Périmètre

### Contexte Métier
La rigueur du framework repose sur la traçabilité factuelle de chaque décision d'architecture et de conception. Lorsqu'un agent conversationnel génère des stories en série sans instruire de dossier de preuves individuel, l'intégrité du sprint est compromise. Ce récit dote le harnais Vibe-Check d'une sonde d'analyse temporelle et documentaire (Check 28) capable d'identifier les anomalies de prolifération en masse, tout en adaptant l'interface CLI pour expliciter la matrice $2 \times 2$ (Format $\times$ Scope).

### In-Scope
- Implémentation du Check 28 dans [`src/pipelines/vibe_check/_vc_governance.py`](file:///C:/Memory%20Loop/src/pipelines/vibe_check/_vc_governance.py) :
  - Analyse des récits sous `backlog/stories/` ayant le statut `READY_FOR_GROOMING` ou `READY_FOR_DEV`.
  - Contrôle d'existence et de fraîcheur du dossier de preuves associé sous `memory/evidence/<STORY_ID>_fact_dossier.md`.
  - Détection de vélocité anormale : si $\ge 3$ récits ont été modifiés dans un intervalle inférieur à 60 secondes sans horodatages distincts de fact dossiers, l'anomalie de cascade est levée.
  - Sévérité graduée selon le cycle de vie : `WARNING` informatif en Phase 2 (PLAN), et `FAIL` bloquant impératif en Phase 4 (VALIDATE / `validate-sprint`) et Phase 5 (SHIP).
- Intégration du Check 28 dans [`src/pipelines/vibe_check/__init__.py`](file:///C:/Memory%20Loop/src/pipelines/vibe_check/__init__.py) au sein du pipeline des sondes pré-vol.
- Mise à niveau du registre CLI [`src/commands/_registry/_reg_pipelines_arch.py`](file:///C:/Memory%20Loop/src/commands/_registry/_reg_pipelines_arch.py) :
  - Support formel de `--format` (`round` | `atomic`) et `--scope` (`story` | `epic` | `project`).
  - Maintien transparent de `--mode` avec priorisation stricte accordée à `--format`.
- Adaptation du gestionnaire [`src/pipelines/grill/_cli_handler.py`](file:///C:/Memory%20Loop/src/pipelines/grill/_cli_handler.py) pour afficher la matrice active en console.

### Out-of-Scope
- Harnais de tests d'intégration automatisés Pytest (`MLOOP-324-FULL`).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend / fullstack)*
#### 1. Sonde de Surveillance et Découplage CLI
* **Entrée Métier** : Spécifications d'audit issues du micro-grill `ADR-020` et d'[ADR-0393](file:///C:/Memory%20Loop/standards/adr-system/0393-decouplage-modalite-grill-scope-anti-cascade.md).
* **Règles d'admissibilité & Validation** : Respect strict du contrat Vibe-Check tri-état (PASS / WARNING / FAIL) et conformité au registre des commandes mLoop.
* **Traitement & Algorithme Métier** :
  1. Inspecter les fichiers Markdown de stories sous `backlog/stories/`.
  2. Vérifier la présence du fichier de preuves correspondant dans `memory/evidence/`.
  3. Vérifier que la métadonnée temporelle ne reflète pas une écriture en rafale sous 60 secondes non étayée.
  4. Positionner le verdict en `WARNING` lors de la Phase 2 et en `FAIL` bloquant dès la Phase 4.
  5. Accepter les arguments `--format` et `--scope` dans les commandes `grill` et `grill-project`, avec arbitrage en faveur de `--format` en cas de coexistence avec `--mode`.
* **Résultat Métier & Mutations** : Sonde Check 28 opérationnelle dans Vibe-Check et commandes CLI enrichies.
* **Cas de Rejet Métier** : Tout lot de stories sans dossiers de preuves unitaires bloque la certification QA en Gate 4.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
> *Définition déclarative des interfaces normatives de gouvernance.*

#### Matrice des Contrats API
> 📌 **Clause d'Exemption (ADR-0319 / OQ-323-01)** : Récit d'outillage CLI et de sonde d'audit interne modifiant le harnais Vibe-Check (`src/pipelines/vibe_check/`, `src/commands/_registry/`, `src/pipelines/grill/_cli_handler.py`). Aucune route API HTTP REST exposée, interfaces de transport réseau déclarées à définir comme sans objet externe.

| Contrat / Interface | Type | Direction | Format / Schéma | Description |
| :--- | :---: | :---: | :--- | :--- |
| `check_28_story_cascade_drift` | Fonction Python | Interne | `project_dir, stage -> dict` | Sonde d'audit de dérive de cascade |
| `execute_grill_cli` | Fonction Python | Interne | `args, state, project_path -> int` | Gestionnaire CLI avec support format et scope |

---

## Règles d'affaires

- **Obligation de Preuve Unitaire par Récit** : Chaque récit au statut `READY_FOR_GROOMING` ou supérieur doit obligatoirement posséder un dossier de preuves unitaire `memory/evidence/<ID>_fact_dossier.md` scellé.
- **Blocage Pré-Vol en Phase 4** : La qualification de sprint (`validate-sprint`) échoue avec `FAIL` bloquant si au moins une story en Palier 2 est orpheline de dossier de preuves ou issue d'une cascade non régularisée.
- **Primauté Déterministe des Arguments CLI** : Si `--format` et `--mode` sont fournis simultanément, `--format` prévaut obligatoirement et une notification d'alignement est affichée.
- **Transparence d'Affichage** : Lors du lancement de toute session de grill, l'agent ou la console affiche explicitement le couple matrice actif (ex: `Format: ROUND | Scope: PROJECT`).

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-323-BE_fact_dossier.md`](../../memory/evidence/MLOOP-323-BE_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Micro-Grill MLOOP-323-BE** : [`Projects/mLoop/docs/01-architecture/ADR-020_micro-grill_mloop-323-be__2_decisions.md`](../../docs/01-architecture/ADR-020_micro-grill_mloop-323-be__2_decisions.md)
- 📜 **Standard Système Découplage & Anti-Cascade** : [ADR-0393](../../standards/adr-system/0393-decouplage-modalite-grill-scope-anti-cascade.md)
- 🏛️ **Cadrage Macro EPIC-32** : [`Projects/mLoop/docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md`](../../docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md)
- 📋 **Constitution Agentique mLoop** : [AGENTS.md](../../AGENTS.md)
- 🧭 **Architecture Vibe-Check** : [`src/pipelines/vibe_check/__init__.py`](../../../src/pipelines/vibe_check/__init__.py)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Contrôle de Gating CLI & Sonde de Détection de Cascade Check 28

  # CHEMIN NOMINAL (Happy Path & Arrêt Déterministe)
  Scénario: Exécution conforme du Check 28 sur un backlog avec dossiers de preuves réguliers
    Étant donné un projet mLoop contenant des récits au statut READY_FOR_GROOMING
    Et que chaque récit dispose de son dossier de preuves memory/evidence/<ID>_fact_dossier.md
    Quand l'auditeur exécute la sonde Check 28 dans vibe-check
    Alors la sonde retourne le statut PASS
    Et aucun avertissement de dérive de cascade n'est levé

  # EXCEPTIONS & REJETS MÉTIER (Tentative de Cascade Non Sollicitée)
  Scénario: Détection d'une promotion groupée sans preuves et blocage en Phase 4
    Étant donné un lot de 3 récits modifiés en écriture en rafale sous 60 secondes
    Mais constatant l'absence de dossiers de preuves unitaires horodatés
    Quand la validation de pré-vol validate-sprint est lancée en Phase 4
    Alors le Check 28 retourne immédiatement un verdict FAIL bloquant
    Et la porte de qualification Gate 4 est fermée avec interdiction de promotion vers READY_TO_SHIP
    Et la liste exacte des récits orphelins est affichée en console

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Anti-Rebond, Concurrence & Timeouts)
  Scénario: Résilience face aux frappes concurrentes sous 500 millisecondes et perte réseau
    Étant donné un opérateur saisissant des commandes CLI de grill
    Mais qu'un double-clic ou des soumissions consécutives sous 500 millisecondes se produisent
    Quand le routeur d'arguments analyse les paramètres entrants
    Alors le verrou d'exécution CLI filtre la seconde requête par déduplication
    Et la stabilité du diagnostic Vibe-Check est garantie sans corruption d'état sous 500 millisecondes
    Et en cas de session expirée, timeout ou coupure réseau le rapport d'audit partiel est sécurisé

  # UX, OBSERVABILITÉ & VALIDATION DES SAISIES (Validation des Entrées Incomplètes)
  Scénario: Détection d'arguments invalides, champ vide ou conflit d'options CLI
    Étant donné un utilisateur invoquant la commande avec un champ vide, des données partielles ou options contradictoires
    Quand le parseur d'arguments évalue les directives --mode atomic et --format round
    Alors le paramètre formel --format round prend la priorité absolue
    Et un message informatif signale l'alignement sur la nouvelle matrice
    Et si une valeur inconnue est passée un message explicite invite à utiliser round ou atomic
```