---
id: MLOOP-224-FULL
jira_key: ""
epic_key: EPIC-22-TOOLING-ECOSYSTEM-HARNESS
type: Feature
title: "Harnais de Certification E2E du Cycle Tooling (Phase -> Plan Visuel -> Build -> Vibe-Check)"
tags: [e2e, certification, tooling, fullstack, vibe-check]
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: "Marco (PO)"
validated_at: "2026-09-24"
layer: fullstack
origin: DIRECT_REQUIREMENT
source_ref: "ADR-0375, ADR-0376"
macro_size: L
blocked_by: [MLOOP-220-BE, MLOOP-221-BE, MLOOP-222-BE, MLOOP-223-FE]
created_at: "2026-09-24"
updated_at: "2026-09-24"
---

# 📖 MLOOP-224-FULL : Harnais de Certification E2E du Cycle Tooling (Phase -> Plan Visuel -> Build -> Vibe-Check)

---

## Description
**En tant que** Responsable Qualité et Architecte mLoop,  
**je veux** disposer d'un scénario de test d'intégration bout en bout validant le cycle complet : de la cartographie Wayfinder au plan de phase validé sous Plannotator, exécuté par les runtimes connectés et certifié par Vibe-Check,  
**afin de** garantir que l'écosystème outillage fonctionne en harmonie souveraine sans friction humaine inutile ni rupture de conformité.

---

## Contexte & Périmètre

### Contexte Métier
L'intégration des différents outils développeur (OpenCode, Plannotator, Wayfinder, Dashboard) requiert une vérification bout en bout pour s'assurer qu'aucune régression silencieuse ne s'infiltre dans le cycle de vie des récits. Le harnais de certification simule un projet complet sur un environnement isolé (`TestToolingProject`), vérifiant la transition déterministe entre chaque étape et s'assurant qu'aucun déchet ni répertoire orphelin n'est créé à la racine globale de Memory Loop.

### In-Scope
- Scénario de test E2E automatisé sous `tests/test_tooling_lifecycle_e2e.py` (≤ 300L, ADR-0202).
- Validation séquentielle complète :
  1. Initialisation de carte Wayfinder (`mloop wayfinder init-map`).
  2. Résolution d'un ticket décisionnel et déblocage de frontière.
  3. Génération d'un plan de phase et approbation headless Plannotator (`mloop plannotator approve --approve`).
  4. Vérification de l'intégrité du stockage sous `Projects/TestToolingProject/memory/plan/`.
  5. Audit de non-régression Vibe-Check (`vibe-check` à 22+ PASS / 0 FAIL).
- Vérification rigoureuse de l'absence totale de répertoires orphelins à la racine `C:\Memory Loop\`.
- Mise à jour du guide de référence CLI SSOT (`standards/protocols/CLI_PIPELINE_GUIDE.md`).

### Out-of-Scope
- Déploiement vers des infrastructures distantes ou des pipelines cloud externes.
- Modification des seuils de qualité des règles ADR existantes.

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [ ] **CA-1** — Le scénario E2E s'exécute de bout en bout avec un taux de réussite de 100%.
> - [ ] **CA-2** — L'absence absolue de fichiers ou dossiers orphelins à la racine de Memory Loop est formellement vérifiée.
> - [ ] **CA-3** — Le contrôle souverain `python src/swarm.py vibe-check --project mLoop` retourne 0 FAIL.
> - [ ] **CA-4** — Le guide CLI SSOT `CLI_PIPELINE_GUIDE.md` est mis à jour et validé par le check de parité.
> - [ ] **CA-5** — Le fichier de test E2E `tests/test_tooling_lifecycle_e2e.py` respecte le plafond de 300 lignes (ADR-0202).
> - [ ] **CA-6** — La gestion des pannes (timeout, binaire manquant, données partielles) est validée par des assertions explicites.

### Opérations Métier & Logique Fullstack

#### 1. Exécution du harnais E2E — `pytest tests/test_tooling_lifecycle_e2e.py`
* **Entrée Métier** : Suite de tests pytest exécutée en environnement local.
* **Règles d'admissibilité & Validation** : Création d'un espace de travail temporaire sous `Projects/TestToolingProject/`.
* **Traitement & Algorithme Métier** :
  1. Instancier le projet de test isolé.
  2. Dérouler la séquence Wayfinder -> Plannotator -> OpenCode.
  3. Valider la persistance des fichiers annotés sous `memory/plan/`.
  4. Nettoyer l'espace de test temporaire après assertions.
* **Résultat Métier & Mutations** : Rapports de test au vert.
* **Cas de Rejet Métier** : Échec d'une assertion ; persistance d'un fichier orphelin à la racine.

#### 2. Contrôle de parité SSOT — `CLI_PIPELINE_GUIDE.md`
* **Entrée Métier** : Documentation de référence des commandes mLoop.
* **Règles d'admissibilité & Validation** : Parité stricte entre les commandes CLI exposées et la documentation.
* **Traitement & Algorithme Métier** :
  1. Auditer les signatures des commandes `opencode`, `plannotator`, `wayfinder`.
  2. Documenter la syntaxe et les commutateurs associés.
* **Résultat Métier & Mutations** : Guide CLI actualisé.
* **Cas de Rejet Métier** : Commande non documentée ou description obsolète.

### Contrats d'échange API (Interface Python, CLI & HTTP)

#### Matrice des Contrats API

| Méthode | Endpoint | Description | Auth / Rôle | Statut Réponse |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/tooling/status` | Statut de disponibilité des runtimes développeur | Local / Développeur | `200 OK` |

- **OQ-224 (Exemption Complémentaire)** : Les interactions de test E2E, commandes CLI locales et scripts Python sont in-process sans route HTTP additionnelle `[API de soumission à définir]` (ADR-0319).

---

## Règles d'affaires

- **Isolation Stricte des Tests** : Le harnais E2E opère dans un projet isolé pour ne jamais polluer la mémoire des projets réels.
- **Règle Zéro Résidu** : Tout fichier temporaire généré pendant le cycle de test doit être nettoyé en fin d'exécution ou confiné dans le dossier de test.
- **Résilience & Délai d'Attente** : Tout appel système ou vérification de statut dispose d'un timeout explicite afin de ne jamais bloquer la suite de test en boucle infinie.
- **Concurrence & Anti-Rebond** : Vérification que les opérations concurrentes sur les plans et la carte n'entraînent pas d'états incohérents.
- **Gestion des Sessions & Codes d'Erreur** : En cas de déconnexion réseau ou d'erreur 401 simulée, le scénario vérifie la résilience du fallback.
- **Contrôle d'Intégrité** : Rejet de toute transition en présence d'un champ vide, de données partielles ou d'une valeur null.

---

## Décisions de cadrage Grill-Me 1:1 (scellées ADR-014)

| Réf | Question tranchée | Option retenue (A) | Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q4** | Certification E2E & Zéro Régression | **Option A (Harnais E2E Déterministe & Vibe-Check 0 FAIL)** : Scénario complet validant Wayfinder, Plannotator headless et OpenCode avec 0 déchet à la racine. | [ADR-0375](file:///C:/Memory%20Loop/standards/adr-system/0375-standard-preuve-epistemique-et-tracabilite-radicale.md) · [ADR-0376](file:///C:/Memory%20Loop/standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md) · [ADR-014](file:///C:/Memory%20Loop/Projects/mLoop/docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md) |

---

## Definition of Ready (DoR 6/6)
- [x] **Clarté du besoin & non-ambiguïté** : Enchaînement séquentiel E2E validé.
- [x] **Architecture & Contrats clarifiés** : Matrice API et exemption OQ-224 renseignées.
- [x] **Critères d'acceptation 4 Piliers Gherkin** : Scénarios nominal, exceptions, résilience et UX rédigés.
- [x] **Dépendances identifiées & levées** : Raccordement aux récits MLOOP-220 à 223 établi.
- [x] **Estimations et découpage validés** : Taille L (3 à 4 jours), code de test ≤ 300L (ADR-0202).
- [x] **Session Grill-Me complétée** : Arbitrage Q4 scellé dans l'ADR-014.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-224-FULL_fact_dossier.md`](../../memory/evidence/MLOOP-224-FULL_fact_dossier.md) *(statut `VALIDATED`)*

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **ADR de cadrage** : [ADR-014 — Intégration Opérationnelle Tooling (EPIC-22)](../../../docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md)
- 📜 **Standards de Traçabilité** : [ADR-0375](file:///C:/Memory%20Loop/standards/adr-system/0375-standard-preuve-epistemique-et-tracabilite-radicale.md) · [ADR-0376](file:///C:/Memory%20Loop/standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md)
- 📋 **Épopée de rattachement** : [epic_tooling_ecosystem_harness.md](../epics/epic_tooling_ecosystem_harness.md)

---

## Scénarios de test

### Pilier 1 : Nominal (Happy Path — Exécution E2E Complète)
```gherkin
Fonctionnalité: Certification E2E Tooling

  Scénario: Cycle complet réussi de la décision au plan validé
    Étant donné un projet de test isolé "TestToolingProject"
    Quand le harnais initialise la carte Wayfinder et résout le premier ticket
    Et qu'il génère le plan de phase et l'approuve en mode headless Plannotator
    Alors le fichier annoté est sauvegardé dans "memory/plan/"
    Et aucun fichier résiduel n'existe à la racine globale de Memory Loop

  Scénario: Certification Vibe-Check au vert
    Étant donné l'ensemble des modules d'outillage intégrés
    Quand la commande "python src/swarm.py vibe-check --project mLoop" est exécutée
    Alors le résultat affiche au moins 22 vérifications passées et 0 échec
```

### Pilier 2 : Exceptions & Rejets Métier (Détection de Pollution & Fichier Manquant)
```gherkin
Fonctionnalité: Certification E2E Tooling

  Scénario: Détection d'un fichier orphelin créé à la racine
    Étant donné une anomalie simulée créant un fichier "plannotator/plan.tmp" à la racine
    Quand le test de propreté est déclenché
    Alors le test E2E échoue avec un rapport signalant la violation d'hygiène
    Et le fichier polluant est supprimé

  Scénario: Exécution avec projet corrompu ou données partielles
    Étant donné un projet de test avec champ vide ou métadonnées manquantes
    Quand le harnais E2E démarre
    Alors il lève une exception explicite interrompant proprement le cycle
```

### Pilier 3 : Résilience & Mode Dégradé (Timeout & Concurrence de Test)
```gherkin
Fonctionnalité: Certification E2E Tooling

  Scénario: Résilience face à un timeout lors de l'exécution du plan
    Étant donné une sous-étape E2E dont le délai d'attente dépasse le seuil configuré
    Quand le gestionnaire de test constate le timeout
    Alors il consigne la défaillance dans le journal sans figer l'exécuteur de tests

  Scénario: Concurrence de plusieurs tests E2E
    Étant donné l'exécution simultanée de deux suites de tests sur des projets distincts
    Quand les verrous d'écriture s'activent
    Alors chaque suite opère dans son périmètre sans collision ni interférence
```

### Pilier 4 : UX & Observabilité (Rapport de Certification & Parité SSOT)
```gherkin
Fonctionnalité: Certification E2E Tooling

  Scénario: Restitution détaillée du rapport de certification
    Étant donné l'achèvement de la suite de tests E2E
    Quand le compte-rendu est généré
    Alors chaque étape du cycle tooling affiche son statut individuel et son temps d'exécution
    Et la table du guide CLI SSOT est validée sans omission de commande
```