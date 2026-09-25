---
id: MLOOP-221-BE
jira_key: ""
epic_key: EPIC-22-TOOLING-ECOSYSTEM-HARNESS
type: Feature
title: "Harnais Automatisé Plannotator (Génération, Validation Visuelle HITL & Archivage Canonique)"
tags: [plannotator, hitl, plan, workflow, backend]
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: "Marco (PO)"
validated_at: "2026-09-24"
layer: backend
origin: DIRECT_REQUIREMENT
source_ref: "KN-051"
macro_size: M
blocked_by: []
created_at: "2026-09-24"
updated_at: "2026-09-24"
---

# 📖 MLOOP-221-BE : Harnais Automatisé Plannotator (Génération, Validation Visuelle HITL & Archivage Canonique)

---

## Description
**En tant qu'** Architecte et Développeur mLoop,  
**je veux** que le cycle de vie de génération et de revue des plans d'implémentation et de test s'exécute via Plannotator (`%LOCALAPPDATA%\plannotator\plannotator.exe`),  
**afin de** garantir que chaque plan soit validé visuellement par l'humain et archivé directement sous `Projects/<project>/memory/plan/` sans laisser de fichiers orphelins à la racine.

---

## Contexte & Périmètre

### Contexte Métier
Plannotator est l'outil visuel souverain pour l'inspection, l'annotation et l'approbation humaine (HITL) des plans de phase et de test avant toute modification de code de production. Jusqu'alors, l'invocation de Plannotator laissait des répertoires et fichiers temporaires à la racine de `C:\Memory Loop` (répertoire `plannotator/`). Ce récit assainit rigoureusement le harnais en confinant 100% des fichiers sous l'espace projet (`Projects/<project>/memory/plan/`) et en intégrant un commutateur headless `--approve` pour les environnements automatisés.

### In-Scope
- Refonte et consolidation de `src/commands/handlers/plannotator.py` (≤ 300L).
- Détection robuste du binaire système `%LOCALAPPDATA%\plannotator\plannotator.exe`.
- Commande `mloop plannotator open --project <proj> --story <id>` ouvrant le plan de phase dans Plannotator.
- Commande `mloop plannotator approve --project <proj> --story <id> [--approve]` archivant le plan annoté sous le nommage canonique `Projects/<project>/memory/plan/<story_id>_phase_plan.annotated.md`.
- Mode headless déterministe pour validation CI/CD sans affichage de fenêtre graphique.
- Éradication définitive de toute création de répertoire `plannotator/` à la racine globale.

### Out-of-Scope
- Modification du code source compilé du binaire Plannotator.
- Remplacement du visualiseur graphique par un autre composant tiers.

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [ ] **CA-1** — L'invocation de Plannotator n'écrit aucun fichier ni dossier à la racine de Memory Loop.
> - [ ] **CA-2** — Le plan annoté est sauvegardé sous `Projects/<project>/memory/plan/<story_id>_phase_plan.annotated.md`.
> - [ ] **CA-3** — Le binaire `%LOCALAPPDATA%\plannotator\plannotator.exe` est résolu de manière déterministe avec message explicite en cas d'absence.
> - [ ] **CA-4** — Le commutateur `--approve` permet une validation headless sans blocage de l'interface utilisateur.
> - [ ] **CA-5** — Le code Python de `src/commands/handlers/plannotator.py` respecte strictement le plafond de 300 lignes (ADR-0202).
> - [ ] **CA-6** — La suite de tests unitaires sous `tests/test_plannotator.py` passe à 100%.

### Opérations Métier & Logique Backend

#### 1. Ouverture du plan — `mloop plannotator open --project <proj> --story <id>`
* **Entrée Métier** : Identifiant du projet et identifiant du récit (`story_id`).
* **Règles d'admissibilité & Validation** : Le plan source `Projects/<proj>/memory/plan/<story_id>_phase_plan.md` doit exister ; le nom de projet ne doit pas être un champ vide.
* **Traitement & Algorithme Métier** :
  1. Résoudre le plan de phase source.
  2. Localiser l'exécutable `%LOCALAPPDATA%\plannotator\plannotator.exe`.
  3. Lancer le processus avec le chemin absolu du fichier.
* **Résultat Métier & Mutations** : Ouverture de la fenêtre graphique d'annotation.
* **Cas de Rejet Métier** : Plan inexistant ; binaire absent ; données partielles ou champ vide.

#### 2. Approbation et archivage — `mloop plannotator approve --project <proj> --story <id>`
* **Entrée Métier** : Projet, identifiant de récit et indicateur headless optionnel `--approve`.
* **Règles d'admissibilité & Validation** : Présence du plan annoté ou confirmation de validation sans altération.
* **Traitement & Algorithme Métier** :
  1. Vérifier la conformité du plan de phase.
  2. Archiver sous `<story_id>_phase_plan.annotated.md`.
  3. Mettre à jour l'état de validation dans les métadonnées de phase.
* **Résultat Métier & Mutations** : Écriture du fichier annoté canonique.
* **Cas de Rejet Métier** : Absence du fichier plan d'origine ; verrou en contention ou échec disque.

### Contrats d'échange API (Interface Python & In-Process)

#### Matrice des Contrats API
- **OQ-221 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — harnais d'orchestration local et in-process du binaire Plannotator via CLI Python sans exposition d'endpoints HTTP distants `[API de soumission à définir]` (ADR-0319).

**Contrats d'interface CLI (commandes in-process réelles)** :
- `python src/swarm.py plannotator open --project <name> --story <id>`
- `python src/swarm.py plannotator approve --project <name> --story <id> [--approve]`
- `python src/swarm.py plannotator status`

---

## Règles d'affaires

- **Sanctuarisation de la racine globale** : Interdiction absolue de créer un répertoire `plannotator/` ou d'écrire des fichiers d'état à la racine du dépôt `C:\Memory Loop\`.
- **Topologie Projet Stricte** : 100% des plans bruts et annotés résident sous `Projects/<project>/memory/plan/`.
- **Résilience et Délai d'Attente** : En cas de non-réponse du binaire ou de délai d'attente dépassé (timeout), le processus est proprement détaché ou interrompu avec message explicite.
- **Concurrence & Anti-Rebond** : Protection par verrou de fichier contre les approbations concurrentes ou double-clic involontaire lors de l'archivage du plan.
- **Session expirée & Authentification** : L'outil opère en local sans dépendance à une session expirée ou un code 401 d'API distante.
- **Validation des entrées** : Rejet strict si un champ vide, une valeur null ou un caractère spécial prohibé est transmis.

---

## Décisions de cadrage Grill-Me 1:1 (scellées ADR-014)

| Réf | Question tranchée | Option retenue (A) | Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q2** | Topologie Plannotator & Zéro-Orphelin | **Option A (Topologie Projet Stricte & Mode Headless)** : Confinement sous `Projects/<project>/memory/plan/`, binaire sous `%LOCALAPPDATA%`, éradication du dossier racine et commutateur `--approve`. | [KN-051](file:///C:/Memory%20Loop/docs/06-knowledge/06-tooling-ecosystem/KN-051_plannotator_workflow.md) · [ADR-014](file:///C:/Memory%20Loop/Projects/mLoop/docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md) |

---

## Definition of Ready (DoR 6/6)
- [x] **Clarté du besoin & non-ambiguïté** : Topologie de confinement et cycle d'approbation définis.
- [x] **Architecture & Contrats clarifiés** : Exemption OQ-221 formalisée, absence de routes fantômes.
- [x] **Critères d'acceptation 4 Piliers Gherkin** : Scénarios nominal, exceptions, résilience et UX rédigés.
- [x] **Dépendances identifiées & levées** : Localisation du binaire `%LOCALAPPDATA%` validée.
- [x] **Estimations et découpage validés** : Taille M (2 à 3 jours), modularité ≤ 300L (ADR-0202).
- [x] **Session Grill-Me complétée** : Arbitrage Q2 scellé dans l'ADR-014.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-221-BE_fact_dossier.md`](../../memory/evidence/MLOOP-221-BE_fact_dossier.md) *(statut `VALIDATED`)*

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **ADR de cadrage** : [ADR-014 — Intégration Opérationnelle Tooling (EPIC-22)](../../../docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md)
- 📜 **Fiche de Savoir** : [KN-051 Plannotator Workflow](file:///C:/Memory%20Loop/docs/06-knowledge/06-tooling-ecosystem/KN-051_plannotator_workflow.md)
- 📜 **Protocole Phase & Tests** : [PHASE_FILES_AND_TEST_PLAN.md](file:///C:/Memory%20Loop/standards/protocols/PHASE_FILES_AND_TEST_PLAN.md)
- 📋 **Épopée de rattachement** : [epic_tooling_ecosystem_harness.md](../epics/epic_tooling_ecosystem_harness.md)

---

## Scénarios de test

### Pilier 1 : Nominal (Happy Path — Ouverture & Approbation Plannotator)
```gherkin
Fonctionnalité: Harnais Plannotator

  Scénario: Ouverture réussie d'un plan de phase dans Plannotator
    Étant donné un plan de phase existant "Projects/mLoop/memory/plan/MLOOP-220-BE_phase_plan.md"
    Et l'exécutable Plannotator présent sous "%LOCALAPPDATA%\plannotator\plannotator.exe"
    Quand l'opérateur exécute "mloop plannotator open --project mLoop --story MLOOP-220-BE"
    Alors le processus Plannotator est lancé avec le fichier ciblé
    Et aucun fichier temporaire n'est créé à la racine de Memory Loop

  Scénario: Approbation headless en mode CI/CD
    Étant donné un plan de phase prêt pour validation
    Quand l'opérateur exécute "mloop plannotator approve --project mLoop --story MLOOP-220-BE --approve"
    Alors le fichier "Projects/mLoop/memory/plan/MLOOP-220-BE_phase_plan.annotated.md" est généré
    Et le cycle de vie enregistre la validation sans bloquer l'écran
```

### Pilier 2 : Exceptions & Rejets Métier (Binaire Absent & Plan Manquant)
```gherkin
Fonctionnalité: Harnais Plannotator

  Scénario: Tentative d'ouverture avec plan inexistant ou champ vide
    Étant donné un identifiant de récit inexistant ou un champ vide
    Quand la commande "mloop plannotator open" est invoquée
    Alors l'exécution est rejetée avec un message d'erreur explicite
    Et aucun processus n'est instancié

  Scénario: Binaire Plannotator non installé sur le système
    Étant donné l'absence de l'exécutable sous "%LOCALAPPDATA%\plannotator\"
    Quand l'opérateur tente d'ouvrir un plan
    Alors une erreur informative indique la procédure d'installation
```

### Pilier 3 : Résilience & Mode Dégradé (Timeout & Concurrence)
```gherkin
Fonctionnalité: Harnais Plannotator

  Scénario: Protection contre la concurrence et le double-clic lors de l'approbation
    Étant donné une validation déclenchée par un double-clic ou deux processus concurrents
    Quand le mécanisme de verrouillage intervient
    Alors un seul archivage est exécuté
    Et le fichier annoté conserve une intégrité parfaite sans corruption

  Scénario: Dépassement de délai d'attente (timeout) lors de l'appel système
    Étant donné un processus Plannotator bloqué ou non réactif
    Quand le délai d'attente maximal est atteint
    Alors le harnais capture l'événement sans crasher l'orchestrateur
```

### Pilier 4 : UX & Observabilité (Ergonomie & Accessibilité)
```gherkin
Fonctionnalité: Harnais Plannotator

  Scénario: Diagnostic d'état et accessibilité de la ligne de commande
    Étant donné l'opérateur vérifiant la disponibilité de Plannotator
    Quand la commande "mloop plannotator status" est exécutée
    Alors la console restitue l'emplacement du binaire et la version de façon lisible
    Et l'accès clavier et le focus console sont immédiatement restitués
```