---
id: MLOOP-314-FULL
jira_key: MLOOP-314-FULL
epic_key: EPIC-31-FSM-ANTI-HARDCODING-AND-LIFECYCLE-HARMONIZATION
type: Feature
title: "Formalisation Normative ADR-0391, Mise à Jour SSOT & Harnais de Certification E2E"
tags: [standards, adr, lifecycle, certification, qa, fullstack]
status: DONE_TESTED
layer: fullstack
invest_score: 6/6
grill_me: DONE
origin: DIRECT_REQUIREMENT
source_ref: "ADR-0391-§5"
macro_size: M
blocked_by: [MLOOP-310-BE, MLOOP-311-BE, MLOOP-312-BE, MLOOP-313-BE]
created_at: "2026-09-25T04:35:00Z"
updated_at: "2026-09-25T05:18:00Z"
---

# Formalisation Normative ADR-0391, Mise à Jour SSOT & Harnais de Certification E2E

---

## Description
**En tant que** Lead Architect et garant de la conformité mLoop,  
**je veux** formaliser l'ADR-0391, mettre à niveau `STORY_LIFECYCLE_PROTOCOL.md` et enrichir le harnais de tests déterministe pour certifier la machine à états de bout en bout,  
**afin d'** ancrer définitivement la règle d'immuabilité des récits `DONE`, l'auto-livraison Gate 5 sans validation humaine superflue, et garantir zéro régression sur l'écosystème.

---

## Contexte & Périmètre

### Contexte Métier
L'aboutissement de l'épopée EPIC-31 nécessite d'inscrire durablement les nouvelles règles dans le marbre des standards souverains de mLoop :
1. Rédaction de l'**ADR-0391** (évitant la collision avec l'ADR-0390 existante sur Fact-Search).
2. Alignement du protocole opérationnel SSOT [`STORY_LIFECYCLE_PROTOCOL.md`](../../../standards/protocols/STORY_LIFECYCLE_PROTOCOL.md) sur le graphe déterministe des 5 phases.
3. Actualisation des modèles de sprint backlog et de la règle de responsabilité.
4. Couverture E2E par les suites de tests unitaires et d'intégration garantissant la conformité intégrale du framework (1638+ tests au vert).

### In-Scope
- **Rédaction de l'ADR-0391** : formalisation des décisions actées (nouveau cycle à 5 paliers, auto-clôture Gate 5 si tout vert, immuabilité stricte des récits `DONE`, éradication du hardcoding).
- **Mise à jour normative de `standards/protocols/STORY_LIFECYCLE_PROTOCOL.md`** : schéma des 5 phases, tableau des responsabilités et règles de déclenchement.
- **Mise à jour des gabarits** : `standards/blueprints/sprint_backlog_template.md` et `project_sprint_backlog_template.md`.
- **Alignement de la légende** dans `Projects/mLoop/backlog/sprint_backlog.md` (§ Règle de responsabilité).
- **Enrichissement de la suite de tests** :
  - `tests/test_story_status.py` : tests complets du nouveau flux, éligibilité Jira/grilled, et levée d'exceptions sur transitions illicites.
  - `tests/test_sync_sprint_backlog.py` : tests d'extraction et de synchronisation des nouveaux statuts dans les tables Markdown.
  - `tests/test_state_machine_c9_gate.py` : vérification que Gate C9 s'applique de manière déterministe sur `READY_FOR_QA` et `QA_CERTIFIED`.
- **Validation globale** : exécution de la suite complète de 1638+ tests avec 100% de réussite.

### Out-of-Scope
- Altération ou migration destructive des 91 récits archivés.

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [x] **CA-1** — Le fichier `standards/adr-system/0391-harmonisation-cycle-de-vie-recits-5-phases-fsm.md` est formalisé selon le gabarit officiel.
> - [x] **CA-2** — `STORY_LIFECYCLE_PROTOCOL.md` reflète sans ambiguïté le flux des 5 phases et l'auto-livraison Gate 5.
> - [x] **CA-3** — Tous les tests de `tests/test_story_status.py` sont au vert.
> - [x] **CA-4** — Tous les tests de `tests/test_sync_sprint_backlog.py` sont au vert.
> - [x] **CA-5** — La suite complète de tests mLoop s'exécute à 100% avec succès sans régression.

### Opérations Métier & Logique Backend

#### 1. Certification E2E du Cycle de Vie
* **Entrée Métier** : Suite de tests pytest du framework.
* **Règles d'admissibilité & Validation** : 0 test échoué, 0 régression.
* **Traitement & Algorithme Métier** : Exécution systématique des scénarios de test nominaux, d'exception, de résilience et d'intégrité de la FSM.
* **Résultat Métier & Mutations** : Rapports de test certifiés.
* **Cas de Rejet Métier** : Tout échec unitaire bloque le passage à Gate 4.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)

#### Matrice des Contrats API
- **OQ-314 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — formalisation documentaire ADR, mise à niveau de protocoles normatifs et harnais de certification pytest (`standards/adr-system/`, `standards/protocols/`, `tests/`), sans interface HTTP ni route REST distante `[API de soumission à définir]` (ADR-0319).

---

## Règles d'affaires

- **Immuabilité Absolue des Récits DONE** : Un récit scellé au statut `DONE` est un incrément inviolable. Tout travail ultérieur prend la forme d'un nouveau ticket `BUG` ou `HOTFIX`.
- **SSOT Normatif Incontestable** : `STORY_LIFECYCLE_PROTOCOL.md` et les ADRs constituent la source unique de vérité régissant les comportements des agents et des humains.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-314-FULL_fact_dossier.md`](../../memory/evidence/MLOOP-314-FULL_fact_dossier.md)
- ⚖️ **Épopée Cadre** : [`backlog/epics/epic_fsm_anti_hardcoding_and_lifecycle_refactor.md`](../epics/epic_fsm_anti_hardcoding_and_lifecycle_refactor.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Protocoles Normatifs** : [`standards/protocols/STORY_LIFECYCLE_PROTOCOL.md`](../../../standards/protocols/STORY_LIFECYCLE_PROTOCOL.md)
- 📜 **Décision d'Architecture** : [ADR-0391 — Harmonisation Cycle de Vie 5 Phases](../../standards/adr-system/0391-harmonisation-cycle-de-vie-recits-5-phases-fsm.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Formalisation Normative ADR-0391 & Certification E2E

  # CHEMIN NOMINAL (Happy Path & Documentation Normative)
  Scénario: Publication conforme de l'ADR-0391 et alignement du protocole
    Étant donné le fichier ADR-0391 rédigé sous standards/adr-system/
    Quand les validateurs de documentation parcourent les standards
    Alors le document respecte le gabarit officiel sans lien rompu
    Et STORY_LIFECYCLE_PROTOCOL.md expose fidèlement le graphe des 5 phases

  # EXCEPTIONS & REJETS (Détection de non-conformité)
  Scénario: Détection et rejet de toute tentative d'altération d'un récit scellé DONE
    Étant donné un récit existant portant le statut DONE
    Quand un script ou un agent tente d'en modifier le statut sans passer par un bug
    Alors la FSM bloque la transition
    Et un rappel à la règle d'immuabilité est consigné

  # RÉSILIENCE TECHNIQUE (Exécution de la suite complète sous timeout strict)
  Scénario: Exécution de la suite complète de 1638+ tests sans régression
    Étant donné le harnais de tests automatisés pytest
    Quand l'ensemble des suites unitaires et d'intégration est exécuté
    Alors 100% des tests passent avec succès sans délai d'attente ni timeout
    Et aucun faux positif n'est remonté

  # UX & OBSERVABILITÉ (Légende de backlog sans champ vide)
  Scénario: Alignement de la légende du sprint backlog sans valeur null
    Étant donné le fichier sprint_backlog.md
    Quand un lecteur consulte la section Règle de responsabilité
    Alors les 5 phases et les rôles associés sont explicités sans valeur null ni champ vide
    Et la table est parfaitement synchronisée sans token expiré
```
