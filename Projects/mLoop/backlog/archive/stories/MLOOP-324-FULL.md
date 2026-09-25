---
id: MLOOP-324-FULL
jira_key: ""
epic_key: EPIC-32
type: Enabler
title: Harnais de Non-Régression & Suite de Tests Automatisés (Pytest FSM + Grill Engine)
tags:
- testing
- quality-assurance
- pytest
- anti-cascade
status: DONE_TESTED
layer: fullstack
invest_score: 6/6
macrostructure: ""
ttl_cycles: 3
validated_by: 'PO (Marco)'
validated_at: '2026-09-25T08:30:33-04:00'
content_hash: ab12908dd8bdf88c
blocked_by: ["MLOOP-323-BE"]
---
# Harnais de Non-Régression & Suite de Tests Automatisés (Pytest FSM + Grill Engine)

---

## Description
**En tant qu'** Ingénieur Qualité Logicielle et Développeur Core mLoop,  
**je veux** développer une suite complète de tests automatisés hermétiques dans [`tests/test_grill_modality_decoupling.py`](file:///C:/Memory%20Loop/tests/test_grill_modality_decoupling.py) et aligner la documentation officielle dans [`standards/protocols/CLI_PIPELINE_GUIDE.md`](file:///C:/Memory%20Loop/standards/protocols/CLI_PIPELINE_GUIDE.md),  
**afin de** prouver de manière reproductible et déterministe qu'aucune combinaison de paramètres de grill ne peut provoquer de mutation de stories non sollicitée ou court-circuiter l'autorité humaine exclusive de la Gate 2.

---

## Contexte & Périmètre

### Contexte Métier
L'incident de cascade survenu lors d'EPIC-31 a mis en lumière la nécessité d'une couverture de tests rigoureuse interdisant formellement tout comportement d'auto-promotion non contrôlé. La mise en place de barrières normatives (`MLOOP-320-BE`), de prompts assainis (`MLOOP-321-BE`), de verrous mécaniques FSM (`MLOOP-322-BE`) et de sondes Vibe-Check (`MLOOP-323-BE`) doit être définitivement consolidée par un harnais de tests unitaires et d'intégration validant 100% des cas nominaux et d'abus.

### In-Scope
- Conception du module de test [`tests/test_grill_modality_decoupling.py`](file:///C:/Memory%20Loop/tests/test_grill_modality_decoupling.py) :
  - **Test 1 (Découplage Format x Scope unitaire)** : Vérifier que `--format round --story <ID>` exécute des questions groupées sans jamais altérer le statut du récit au-delà de `READY_FOR_GROOMING`.
  - **Test 2 (Découplage Format x Scope transverse)** : Vérifier que `--format atomic --scope project` ou `grill-project` opère en questions unitaires sans toucher au répertoire `backlog/stories/`.
  - **Test 3 (Sanction Fail-Closed Moteur)** : Vérifier que toute tentative d'écriture de story lors d'un `grill-project` déclenche `LifecycleAuthorityError` avec arrêt du processus.
  - **Test 4 (Verrou Gate 2 nominatif)** : Vérifier que la transition vers `READY_FOR_DEV` est rejetée avec `LifecycleAuthorityError` si `validated_by` est absent ou contient une signature de bot.
  - **Test 5 (Sonde Check 28)** : Valider que Check 28 signale un `WARNING` en Phase 2 et un `FAIL` bloquant en Phase 4 lorsqu'une cascade artificielle est simulée, et retourne `PASS` lorsque les fact dossiers sont présents.
  - **Test 6 (Résolution CLI)** : Vérifier la primauté de `--format` sur `--mode` et le bon acheminement des options.
- Fixtures hermétiques isolées basées sur `tmp_path` simulant des projets mLoop complets sans aucune dépendance sur l'espace de travail réel.
- Mise à jour de la documentation officielle dans [`standards/protocols/CLI_PIPELINE_GUIDE.md`](file:///C:/Memory%20Loop/standards/protocols/CLI_PIPELINE_GUIDE.md) et synchronisation de [`src/pipelines/guide_data.py`](file:///C:/Memory%20Loop/src/pipelines/guide_data.py) pour satisfaire le Check 15.

### Out-of-Scope
- Nouveaux serveurs MCP ou plugins Herdr.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend / fullstack)*
#### 1. Harnais Automatisé et Parité Documentaire
* **Entrée Métier** : Spécifications de tests issues du micro-grill `ADR-021` et d'[ADR-0393](file:///C:/Memory%20Loop/standards/adr-system/0393-decouplage-modalite-grill-scope-anti-cascade.md).
* **Règles d'admissibilité & Validation** : 100% de succès sur la commande `pytest tests/test_grill_modality_decoupling.py` et zéro régression sur l'ensemble de la suite `pytest tests/`.
* **Traitement & Algorithme Métier** :
  1. Implémenter les fixtures temporaires créant une arborescence de test étanche.
  2. Couvrir exhaustivement les 6 scénarios de tests unitaires et de sécurité.
  3. Valider la levée effective de `LifecycleAuthorityError` en cas de violation d'autorité.
  4. Valider le comportement bivalent de la sonde Check 28 selon la phase de cycle de vie active.
  5. Documenter la matrice $2 \times 2$ dans `CLI_PIPELINE_GUIDE.md` et aligner le dictionnaire `guide_data.py`.
* **Résultat Métier & Mutations** : Fichier `tests/test_grill_modality_decoupling.py` créé et documentation synchronisée.
* **Cas de Rejet Métier** : Tout échec de test ou toute désynchronisation du guide CLI pré-vol est bloquant.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
> *Définition déclarative des interfaces normatives de gouvernance.*

#### Matrice des Contrats API
> 📌 **Clause d'Exemption (ADR-0319 / OQ-324-01)** : Récit d'assurance qualité logicielle et de documentation pré-vol créant des suites de tests Pytest et modifiant le guide CLI (`tests/test_grill_modality_decoupling.py`, `standards/protocols/CLI_PIPELINE_GUIDE.md`, `src/pipelines/guide_data.py`). Aucune route API HTTP REST exposée, interfaces de transport réseau déclarées à définir comme sans objet externe.

| Contrat / Interface | Type | Direction | Format / Schéma | Description |
| :--- | :---: | :---: | :--- | :--- |
| `pytest tests/test_grill_modality_decoupling.py` | Commande Pytest | Interne | `test_runner` | Suite de validation du découplage et des verrous |
| `GuideParityEngine.verify` | Méthode Python | Interne | `strict=True` | Vérification de synchronisation du guide CLI |

---

## Règles d'affaires

- **Étanchéité Absolue des Tests** : Les tests automatisés ne doivent en aucun cas modifier, créer ou supprimer des fichiers dans le dossier de travail physique `Projects/mLoop`. Toute opération disque s'effectue sous `tmp_path`.
- **Invariance de la Suite Globale** : L'introduction des nouveaux tests ne doit générer aucune régression sur les tests unitaires existants du framework.
- **Conformité Stricte Check 15** : Toute nouvelle option CLI ajoutée au registre doit être immédiatement reportée dans `CLI_PIPELINE_GUIDE.md` sous peine d'échec du Vibe-Check.
- **Vérification Systématique de l'Exception d'Autorité** : Les tests doivent attester de manière formelle que `LifecycleAuthorityError` hérite de `StateTransitionError` et interrompt l'exécution.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-324-FULL_fact_dossier.md`](../../memory/evidence/MLOOP-324-FULL_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Micro-Grill MLOOP-324-FULL** : [`Projects/mLoop/docs/01-architecture/ADR-021_micro-grill_mloop-324-full__2_decisions.md`](../../docs/01-architecture/ADR-021_micro-grill_mloop-324-full__2_decisions.md)
- 📜 **Standard Système Découplage & Anti-Cascade** : [ADR-0393](../../standards/adr-system/0393-decouplage-modalite-grill-scope-anti-cascade.md)
- 🏛️ **Cadrage Macro EPIC-32** : [`Projects/mLoop/docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md`](../../docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md)
- 📋 **Constitution Agentique mLoop** : [AGENTS.md](../../AGENTS.md)
- 🧭 **Guide des Commandes CLI** : [CLI_PIPELINE_GUIDE.md](../../standards/protocols/CLI_PIPELINE_GUIDE.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Harnais de Non-Régression & Tests Pytest pour Découplage et Anti-Cascade

  # CHEMIN NOMINAL (Happy Path & Arrêt Déterministe)
  Scénario: Exécution avec succès de la suite de tests unitaires sur projet temporaire
    Étant donné une arborescence de test étanche instanciée sous tmp_path
    Quand l'exécuteur de tests lance pytest tests/test_grill_modality_decoupling.py
    Alors l'ensemble des 6 assertions de sécurité sont validées avec succès
    Et le temps total d'exécution demeure inférieur à 1500 millisecondes
    Et aucun fichier résiduel n'est créé dans le répertoire physique de travail

  # EXCEPTIONS & REJETS MÉTIER (Tentative de Cascade Non Sollicitée)
  Scénario: Validation du rejet lors d'une tentative de promotion illicite simulée
    Étant donné un test unitaire simulant un appel à mark_story_grilled avec statut READY_FOR_DEV
    Mais constatant que la méthode est bridée mécaniquement à READY_FOR_GROOMING
    Quand le scénario de test déclenche l'exécution
    Alors une exception LifecycleAuthorityError est effectivement interceptée
    Et l'assertion vérifie la présence de l'incident dans le journal d'audit de sécurité

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Anti-Rebond, Concurrence & Timeouts)
  Scénario: Résilience face aux accès concurrents sous 500 millisecondes et perte réseau
    Étant donné l'exécution de tests parallélisés via pytest-xdist
    Mais qu'un double-clic ou des lectures simultanées sous 500 millisecondes se produisent
    Quand le gestionnaire de fichiers de test accède aux répertoires temporaires
    Alors chaque processus dispose de son espace mémoire isolé sans conflit de verrou
    Et la stabilité du runner est préservée même en cas de session expirée, timeout ou coupure réseau
    Et les diagnostics de test sont restitués de manière intègre sous 500 millisecondes

  # UX, OBSERVABILITÉ & VALIDATION DES SAISIES (Validation des Entrées Incomplètes)
  Scénario: Vérification de conformité du guide CLI et détection de champs manquants
    Étant donné un test automatisé d'intégrité documentaire vérifiant CLI_PIPELINE_GUIDE.md
    Quand le test compare les arguments déclarés avec ceux de guide_data.py
    Alors zéro champ vide, données partielles ou écart de syntaxe n'est relevé
    Et le test atteste que les options format et scope sont fidèlement documentées
```