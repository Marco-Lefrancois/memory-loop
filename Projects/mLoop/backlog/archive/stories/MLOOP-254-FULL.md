---
id: MLOOP-254-FULL
jira_key: ''
epic_key: EPIC-25-OPENCODE-ECOSYSTEM-HARNESS
type: Feature
title: "Commandes CLI mLoop d'Orchestration & Validation E2E OpenCode"
tags:
- opencode
- cli
- orchestration
- status
- sync
- fullstack
origin: SPEC_SLICING
source_ref: EPIC-25-§3
macro_size: M
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: Marco (PO)
validated_at: '2026-09-25'
layer: fullstack
blocked_by:
- MLOOP-250-BE
- MLOOP-251-BE
created_at: '2026-09-24'
updated_at: '2026-09-25'
---

# 📖 MLOOP-254-FULL : Commandes CLI mLoop d'Orchestration & Validation E2E OpenCode

## Description
**En tant que** Développeur mLoop ou Administrateur Système,  
**je veux** des commandes CLI unifiées `mloop opencode sync` (avec option `--dry-run`) et `mloop opencode status` enrichie,  
**afin de** superviser, tester de bout en bout et synchroniser en toute sécurité l'ensemble des personas, outils et configurations de l'écosystème OpenCode.

---

## Contexte & Périmètre

### Contexte Métier
L'intégration des différents modules d'OpenCode (personas miroir, outils TypeScript, protocole ACP) nécessite un point d'entrée unifié et standardisé dans le moteur CLI (`src/swarm.py`). Ce récit livre les commandes souveraines d'orchestration, garantit la fusion non-destructive des fichiers de configuration existants, et assure la validation de conformité de bout en bout.

**Décisions Grill-Me (2026-09-25) :**
- Support de l'option `--dry-run` sur `mloop opencode sync` pour permettre l'inspection préalable des changements sans écriture disque.
- **Stratégie de fusion préservatrice (Merge-Preserving)** : préservation des règles, modèles et configurations personnalisées existantes de l'utilisateur dans `.opencode/opencode.json` avec création d'une sauvegarde automatique (`.opencode/opencode.json.bak`).
- Synchronisation SSOT immédiate dans `CLI_PIPELINE_GUIDE.md` et `PHASE_MAPPING`.

### In-Scope
- Extension du handler CLI `src/commands/handlers/opencode.py` (≤ 300 lignes, ADR-0202).
- Commande `mloop opencode sync [--dry-run]` orchestrant la synchronisation des personas et des outils.
- Commande `mloop opencode status` affichant un tableau récapitulatif coloré (version OpenCode, connectivité LiteLLM, état des personas miroir, statut des outils TypeScript).
- Validation E2E (End-to-End) couvrant le cycle complet : initialisation, synchronisation, vérification et statut.
- Enregistrement des commandes dans `src/commands/_registry/` et maintien de la parité SSOT du guide CLI.

### Out-of-Scope
- Téléchargement ou mise à jour automatique forcée d'OpenCode sans accord explicite de l'utilisateur.
- Interface graphique lourde ou application Web autonome.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Commande d'Orchestration — opencode sync
* **Entrée Métier** : Nom du projet, flag optionnel `--dry-run`.
* **Traitement & Algorithme Métier** :
  - Déclenchement de la synchronisation miroir des personas (MLOOP-250-BE).
  - Déploiement des outils TypeScript natifs (MLOOP-251-BE).
  - Mise à jour préservatrice de `.opencode/opencode.json` avec backup préalable.
* **Résultat Métier & Mutations** : Affichage d'un bilan ZeroFluff des artefacts créés ou modifiés (ou simulation si `--dry-run`).

#### 2. Audit d'État — opencode status
* **Traitement** : Contrôle de la présence du binaire `opencode`, de l'état du proxy LiteLLM, et du nombre de personas/outils synchronisés.
* **Résultat Métier** : Affichage d'un diagnostic clair en console avec code de retour approprié (0 si opérationnel, 1 si composant critique manquant).

---

## Règles d'affaires

- **Préservation Absolue des Paramètres Utilisateur** : Aucun fichier de configuration utilisateur préexistant ne doit être écrasé sans sauvegarde de sécurité `.bak`.
- **Mode Dry-Run Strict** : L'option `--dry-run` garantit qu'aucun octet n'est écrit sur le système de fichiers.
- **Plafond Modulaire AST** : Tout fichier modifié ou créé sous `src/` doit respecter $\le 300$ lignes et $\le 15$ Ko (ADR-0202).

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Handler OpenCode** : `src/commands/handlers/opencode.py`
- 📂 **Guide CLI SSOT** : `standards/protocols/CLI_PIPELINE_GUIDE.md`
- 🏛️ **ADR** : [ADR-0370](../../../standards/adr-system/0370-standard-gouvernance-guide-cli-ssot.md) · [ADR-0377](../../../standards/adr-system/0377-runtimes-agents-aval-et-herdr-operationnels.md) · [ADR-0202](../../../standards/adr-system/0202-modularite-interne-agents.md)
- 📋 **Epic** : [`epics/epic_opencode_ecosystem_harness.md`](../epics/epic_opencode_ecosystem_harness.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Orchestration & Statut CLI OpenCode

  Scénario: Pilier 1 - Nominal (Happy path) : Exécution de opencode sync avec succès
    Étant donné un projet mLoop configuré
    Quand j'exécute la commande "python src/swarm.py opencode --action sync --project mLoop"
    Alors les personas et les outils TypeScript sont synchronisés
    Et un rapport de succès ZeroFluff est affiché sur la console
    Et le code de sortie est 0

  Scénario: Pilier 2 - Exceptions (Cas d'erreur) : Projet introuvable ou invalide
    Étant donné un nom de projet inexistant "ProjetInconnu"
    Quand j'exécute "python src/swarm.py opencode --action sync --project ProjetInconnu"
    Alors une erreur explicite est affichée sans trace de crash non maîtrisée
    Et le code de sortie est 1

  Scénario: Pilier 3 - Résilience (Mode Dry-Run) : Simulation sans mutation de disque
    Étant donné une demande de synchronisation avec le flag "--dry-run"
    Quand la commande est exécutée
    Alors la console liste les actions qui auraient été effectuées
    Et aucun fichier n'est créé ou modifié sur le système de fichiers

  Scénario: Pilier 4 - UX (Accessibilité & Lisibilité) : Affichage d'état opencode status
    Étant donné la commande "python src/swarm.py opencode --action status"
    Quand l'audit est exécuté
    Alors un tableau visuel résume la présence du binaire, du proxy et des personas
    Et des conseils d'installation guidés sont fournis si des composants sont absents
```
