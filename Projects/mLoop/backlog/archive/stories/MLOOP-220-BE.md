---
id: MLOOP-220-BE
jira_key: ""
epic_key: EPIC-22-TOOLING-ECOSYSTEM-HARNESS
type: Feature
title: "Bridge d'Exécution & Commande CLI OpenCode (Intégration Declarative opencode.json)"
tags: [opencode, cli, runtime, tooling, backend]
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: "Marco (PO)"
validated_at: "2026-09-24"
layer: backend
origin: DIRECT_REQUIREMENT
source_ref: "KN-050"
macro_size: S
blocked_by: []
created_at: "2026-09-24"
updated_at: "2026-09-24"
---

# 📖 MLOOP-220-BE : Bridge d'Exécution & Commande CLI OpenCode (Intégration Declarative opencode.json)

---

## Description
**En tant qu'** Développeur et Opérateur mLoop,  
**je veux** disposer d'un sous-système CLI `mloop opencode` (`init`, `run`, `status`) assurant la parité entre la configuration du projet et celle d'OpenCode (`opencode.json`),  
**afin de** piloter des sessions de développement supervisées ou headless via OpenCode sans rupture de configuration ni désalignement avec les proxies LiteLLM.

---

## Contexte & Périmètre

### Contexte Métier
OpenCode CLI constitue un runtime d'exécution autonome en environnement terminal. Afin d'éviter la prolifération de fichiers de configuration hétérogènes et le risque de fuite de clés API, mLoop doit orchestrer la génération déclarative de `.opencode/opencode.json` au niveau de chaque projet (`Projects/<project>/`), en routant systématiquement les flux vers le proxy local LiteLLM (port 4000) et en injectant les règles de gouvernance mLoop.

### In-Scope
- Handler dédié `src/commands/handlers/opencode.py` (≤ 300L) raccordé au registre CLI `src/swarm.py`.
- Commande `mloop opencode init --project <proj>` générant `Projects/<proj>/.opencode/opencode.json` avec routage local LiteLLM (`http://localhost:4000`) et consignes issues de `AGENTS.md`.
- Commande `mloop opencode status` auditant la présence du binaire `opencode` dans le PATH système et la connectivité au proxy.
- Commande `mloop opencode run --project <proj> [--headless] [--prompt <str>]` pour lancer une session OpenCode avec contexte projet isolé.
- Gestion robuste des erreurs : détection de binaire manquant, refus en cas de champ vide ou de nom de projet invalide, délai d'attente réseau.

### Out-of-Scope
- Modification du code binaire ou TypeScript interne d'OpenCode CLI.
- Hébergement d'un serveur distant de proxy (LiteLLM reste géré en local).

---

## Critères d'acceptation

> **Critères mesurables (INVEST 6/6)** :
> - [ ] **CA-1** — La commande `mloop opencode init --project <proj>` génère un fichier `.opencode/opencode.json` valide ciblant `http://localhost:4000`.
> - [ ] **CA-2** — La commande `mloop opencode status` retourne un code de sortie 0 si le binaire `opencode` est disponible et diagnostique les défaillances.
> - [ ] **CA-3** — Le lancement via `mloop opencode run` propage l'isolation projet sous `Projects/<project>/`.
> - [ ] **CA-4** — Les saisies erronées (nom de projet vide, caractères interdits) sont rejetées avec message explicite.
> - [ ] **CA-5** — Le code Python implémenté sous `src/commands/handlers/opencode.py` respecte strictement le plafond modulaire de 300 lignes (ADR-0202).
> - [ ] **CA-6** — La suite de tests unitaires sous `tests/test_opencode_cli.py` est au vert avec couverture nominale et dégradée.

### Opérations Métier & Logique Backend

#### 1. Initialisation de configuration — `mloop opencode init --project <proj>`
* **Entrée Métier** : Nom du projet cible (`project_name`).
* **Règles d'admissibilité & Validation** : Le dossier `Projects/<project_name>` doit exister ; le nom ne doit pas être un champ vide ni contenir de caractère spécial illégal.
* **Traitement & Algorithme Métier** :
  1. Vérifier l'existence du répertoire projet.
  2. Créer le sous-répertoire `Projects/<proj>/.opencode/` si nécessaire.
  3. Générer le fichier `opencode.json` avec configuration provider vers `http://localhost:4000/v1` et injection des directives `AGENTS.md`.
  4. Sauvegarder de manière atomique.
* **Résultat Métier & Mutations** : Création du fichier `.opencode/opencode.json`.
* **Cas de Rejet Métier** : Répertoire projet inexistant ; champ vide ; absence de droits d'écriture sur le disque.

#### 2. Diagnostic d'environnement — `mloop opencode status`
* **Entrée Métier** : Aucune ou indicateur optionnel de projet.
* **Règles d'admissibilité & Validation** : Inspection sans effet de bord.
* **Traitement & Algorithme Métier** :
  1. Résoudre le chemin de `opencode` via `shutil.which`.
  2. Vérifier la connectivité HTTP au port 4000 de LiteLLM (délai d'attente maximum 2 secondes).
  3. Retourner le statut synthétique.
* **Résultat Métier & Mutations** : Rapport console de diagnostic.
* **Cas de Rejet Métier** : Binaire absent du PATH ; timeout de connexion au proxy local.

### Contrats d'échange API (Interface Python & In-Process)

#### Matrice des Contrats API
- **OQ-220 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — intégration locale et in-process du runtime CLI OpenCode via Python sans exposition d'endpoints HTTP distants `[API de soumission à définir]` (ADR-0319).

**Contrats d'interface CLI (commandes in-process réelles)** :
- `python src/swarm.py opencode init --project <name>`
- `python src/swarm.py opencode run --project <name> [--headless] [--prompt <text>]`
- `python src/swarm.py opencode status`

---

## Règles d'affaires

- **Souveraineté des clés & Proxy Local** : Aucun jeton API externe n'est consigné en clair dans `opencode.json` ; les appels transitent via le proxy LiteLLM local (port 4000).
- **Zéro pollution globale** : Aucune configuration OpenCode n'est écrite à la racine de Memory Loop ; tout est circonscrit à `Projects/<project>/.opencode/`.
- **Résilience aux déconnexions & Timeout** : Tout appel de diagnostic ou de synchronisation réseau vers le proxy applique un timeout explicite (2 secondes).
- **Concurrence & Anti-Rebond** : Protection contre les exécutions concurrentes lors de l'écriture de `opencode.json` par verrou de fichier.
- **Gestion des sessions** : En cas de session expirée ou d'absence de session LiteLLM active, un avertissement informatif est émis sans bloquer le diagnostic.
- **Contrôle des entrées** : Tout champ vide ou caractère spécial non supporté dans le nom de projet provoque un rejet immédiat.

---

## Décisions de cadrage Grill-Me 1:1 (scellées ADR-014)

| Réf | Question tranchée | Option retenue (A) | Ancrage SSOT |
| :--- | :--- | :--- | :--- |
| **Q1** | Intégration CLI OpenCode & Local Proxy | **Option A (Isolation Projet & Proxy Local)** : Handler dédié `src/commands/handlers/opencode.py` (≤ 300L), injection de `AGENTS.md` et routage LiteLLM port 4000. | [KN-050](file:///C:/Memory%20Loop/docs/06-knowledge/06-tooling-ecosystem/KN-050_opencode_cli_runtime.md) · [ADR-014](file:///C:/Memory%20Loop/Projects/mLoop/docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md) |

---

## Definition of Ready (DoR 6/6)
- [x] **Clarté du besoin & non-ambiguïté** : Cadrage des sous-commandes `init`, `run`, `status` validé.
- [x] **Architecture & Contrats clarifiés** : Routage LiteLLM et exemption OQ-220 formalisés.
- [x] **Critères d'acceptation 4 Piliers Gherkin** : Piliers nominal, exceptions, résilience et UX rédigés.
- [x] **Dépendances identifiées & levées** : Prérequis OpenCode identifié, mode fallback documenté.
- [x] **Estimations et découpage validés** : Taille S (1 à 2 jours), code ≤ 300L (ADR-0202).
- [x] **Session Grill-Me complétée** : Arbitrage Q1 scellé dans l'ADR-014.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-220-BE_fact_dossier.md`](../../memory/evidence/MLOOP-220-BE_fact_dossier.md) *(statut `VALIDATED`)*

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **ADR de cadrage** : [ADR-014 — Intégration Opérationnelle Tooling (EPIC-22)](../../../docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md)
- 📜 **Fiche de Savoir** : [KN-050 OpenCode CLI Runtime](file:///C:/Memory%20Loop/docs/06-knowledge/06-tooling-ecosystem/KN-050_opencode_cli_runtime.md)
- 📋 **Épopée de rattachement** : [epic_tooling_ecosystem_harness.md](../epics/epic_tooling_ecosystem_harness.md)

---

## Scénarios de test

### Pilier 1 : Nominal (Happy Path — Initialisation & Statut OpenCode)
```gherkin
Fonctionnalité: Intégration CLI OpenCode

  Scénario: Initialisation réussie de la configuration d'un projet
    Étant donné un projet existant "mLoop" sans configuration OpenCode
    Quand l'opérateur exécute "mloop opencode init --project mLoop"
    Alors le fichier "Projects/mLoop/.opencode/opencode.json" est créé avec succès
    Et le endpoint configuré cible "http://localhost:4000/v1"
    Et les directives de gouvernance sont intégrées

  Scénario: Audit du statut de l'environnement avec succès
    Étant donné le binaire "opencode" accessible sur le PATH
    Et le proxy LiteLLM actif sur le port 4000
    Quand l'opérateur exécute "mloop opencode status"
    Alors le statut indique un succès opérationnel
```

### Pilier 2 : Exceptions & Rejets Métier (Saisie Invalide & Binaire Absent)
```gherkin
Fonctionnalité: Intégration CLI OpenCode

  Scénario: Tentative d'initialisation avec champ vide ou caractère spécial interdit
    Étant donné une requête portant un nom de projet vide ou contenant des caractères invalides
    Quand la commande "mloop opencode init" est invoquée
    Alors l'exécution est rejetée avec un message d'erreur explicite
    Et aucun fichier n'est écrit sur le disque

  Scénario: Exécution alors que le binaire opencode est absent
    Étant donné un environnement où le binaire "opencode" est introuvable sur le PATH
    Quand l'opérateur lance "mloop opencode run --project mLoop"
    Alors la commande s'interrompt avec une erreur explicite invitant à l'installation
```

### Pilier 3 : Résilience & Mode Dégradé (Timeout & Concurrence)
```gherkin
Fonctionnalité: Intégration CLI OpenCode

  Scénario: Diagnostic face à un timeout ou coupure réseau du proxy LiteLLM
    Étant donné le proxy LiteLLM inaccessible ou en délai d'attente réseau
    Quand la commande "mloop opencode status" est lancée
    Alors elle n'attend pas indéfiniment et lève un avertissement de timeout après 2 secondes
    Et le mode dégradé signale l'inaccessibilité du service

  Scénario: Concurrence d'initialisation et protection anti-rebond
    Étant donné deux commandes "mloop opencode init" déclenchées en concurrence simultanée
    Quand le verrou de fichier intervient
    Alors l'écriture s'exécute de façon atomique sans corruption du fichier JSON
```

### Pilier 4 : UX & Observabilité (Clarté Console & Accessibilité)
```gherkin
Fonctionnalité: Intégration CLI OpenCode

  Scénario: Rendu ergonomique du diagnostic et focus console
    Étant donné l'opérateur consultant l'état de l'environnement
    Quand la commande "mloop opencode status" affiche le rapport
    Alors les indicateurs de statut sont restitués avec un formatage lisible
    Et les instructions de remédiation en cas de session expirée ou d'erreur 401 sont détaillées
```