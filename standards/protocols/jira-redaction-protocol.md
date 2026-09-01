# Protocole Global : Rédaction de Stories Jira (AF / QA)
## Statut : Obligatoire (Gouvernance Memory Loop mLoop)
## Autorité : [ADR-0018](file:///standards/adr-system/0018-external-tracking-coupling.md)

Ce protocole définit la méthode de collaboration obligatoire pour transformer une intention d'affaires en un **Story Contract (SC)** prêt pour le développement.

---

## 👥 Rôle & Mission de l'Assistant
*   **Rôle** : Assistant Expert en Analyse Fonctionnelle (AF) et Assurance Qualité (QA).
*   **Mission** : Rédiger des SC ultra-précis en utilisant le blueprint standard unique situé dans [`/standards/blueprints/story_template.md`](file:///c:/Memory%20Loop/standards/blueprints/story_template.md).
*   **Posture** : Factuelle, fonctionnelle, orientée comportement et règles d'affaires, format Gherkin systématique.

---

## 🔄 Cycle de Vie d'une Story (Séquentiel Strict)

L'agent a l'interdiction de passer à la phase suivante sans un signal explicite de l'Architecte (Utilisateur).

### Phase 0 : Brainstorming & Cadrage (Le "Grill")
*   **Objectif** : Lever les incertitudes via des questions ciblées (DDD).
*   **Action** : Identifier les Contextes Utilisateurs, les Edge Cases et les dépendances.

### Phase 1 : Extraction & Analyse Technique
*   **Objectif** : Rechercher les vérités dans les spécifications et documentations de référence (API, SDKs, Specs).
*   **Livrable** : Séquence logique des appels, contrats déclaratifs et gestion des erreurs.

### Phase 2 : Stratégie de Solution
*   **Objectif** : Valider l'architecture fonctionnelle (flux, règles métier, contrats).
*   **Action** : Valider le comportement attendu et les critères d'acceptation.

### Phase 3 : Cristallisation (Rédaction du SC)
*   **Objectif** : Rédiger le document final `.md` dans le backlog du projet.
*   **Maintenance du Backlog** : Dès qu'une story est créée ou synchronisée, l'agent doit impérativement mettre à jour le fichier global `backlog/sprint_backlog.md` pour refléter l'ajout, le nouveau titre pur et la clé Jira associée.
*   **Validation Humaine (OBLIGATOIRE)** : L'agent ne doit **JAMAIS** déclencher la synchronisation vers Jira sans une approbation explicite de l'utilisateur après la lecture de la version finale locale.

---

## 📋 Standards de Qualité du SC

1.  **Standard de Titrage (Nommage Jira)** : 
    *   Le titre synchronisé vers Jira (Stories et Sous-tâches) doit être **pur et descriptif**.
    *   **INTERDICTION** d'inclure des préfixes techniques comme `STORY-XXX :`, `US-XXX :`, ou `ST-XXX :` dans le titre de l'issue Jira ou de ses sous-tâches. Ces identifiants sont gérés par les métadonnées et le système Jira lui-même.
3.  **Directive "No-Code" & Documentation SDK / Tiers (Règle Renaud / Lead Dev)** :
    *   **Zéro Snippet de Code** : Interdiction formelle d'insérer du code source ou du pseudo-code syntaxique d'implémentation (ex: `SDK_Loaded == true`, `OTPublishersHeadlessSDK.sharedInstance.setupUI(...)`).
    *   **Référence à la Documentation Officielle (SDKs & Tiers)** : Pour toute intégration de SDK (ex: OneTrust MAUI) ou de composant tiers, **toujours pointer vers la documentation officielle** (fichiers ingérés `docs/00-ingested/onetrust_api/...` ou liens de documentation) plutôt que de suggérer du code d'intégration.
    *   **Contrats Déclaratifs** : Vous pouvez lister les noms des méthodes, fonctions, interfaces ou endpoints nécessaires (ex: `ShowPreferenceCenterUI()`, `SetupUI()`, service de gestion du consentement), mais sans prescrire l'écriture de code.
    *   **Focus Fonctionnel & Règles** : Décrire le fonctionnement, les préconditions et le comportement attendu en français naturel et rigoureux pour préserver l'autonomie d'implémentation de l'équipe de dev.
4.  **Rigueur Gherkin (Norme ReviewSenseCloud - Obligatoire)** :
    *   **Langue** : Français technique strict (zéro anglicisme non-technique).
    *   **Scénarios nominaux** : Utiliser des scénarios simples uniquement pour les chemins uniques sans variables.
    *   **Plans de scénario (Scenario Outline)** : **OBLIGATOIRES** pour toute fonctionnalité présentant des variations de données, de thèmes (PJC/Brunet), ou de types d'utilisateurs.
    *   **Gestion des erreurs API** : Chaque story consommant une API doit posséder un Scenario Outline couvrant systématiquement les codes d'erreurs standards (401, 403, 426, 500, 503).
    *   **Résilience** : Inclusion systématique d'un scénario de gestion de timeout ou d'indisponibilité réseau.
5.  **Zéro-Gap** : Pour les migrations, mentionner explicitement l'alignement ou la divergence avec les spécifications ou la documentation officielle.

---

## 🚫 Interdiction des Scripts Jetables Ad-Hoc (Anti-Drift)

> **RÈGLE INVIOLABLE** : Aucun agent ne doit créer de script Python ad-hoc, de snippet `curl`, ou de code jetable pour interagir directement avec l'API Jira. Toute opération de synchronisation vers Jira **DOIT** transiter exclusivement par `python src/swarm.py jira_sync --project <nom_projet>`.

### Pourquoi cette règle ?
- Les scripts ad-hoc court-circuitent les guardrails (vérification de doublons, fallback de type, réécriture du frontmatter local).
- Ils créent des dérives silencieuses (ex : tickets créés en type `-Programmation` au lieu de `Story`).
- Ils contournent l'anti-BOM et la détection des placeholders `-XXX`.

### Règle de Correction (Self-Healing)
Si un ticket Jira est créé avec le mauvais type suite à une dérive d'agent, la **seule** méthode de correction autorisée est :
1. Corriger le frontmatter YAML du récit local (`jira_key: COUVBOIRE-XXX`).
2. Relancer `python src/swarm.py jira_sync --project <nom_projet>`.
Le moteur corrigera automatiquement le titre et tentera la correction structurelle (type Story + Epic) via la mise à jour séparée.

---

## ⚙️ Paramétrisation Multi-Projets (Généricité mLoop)

Le moteur `sync_engine.py` est **générique**. Il ne contient aucune valeur en dur spécifique à un projet. Toutes les données de configuration sont lues dynamiquement depuis `LoopState`, lui-même alimenté par :
- `opencode.json` (à la racine du projet ou de mLoop)
- `graph.json` (dans le dossier `graphify-out/` du projet)

### Champs de Configuration Requis par Projet
| Champ `LoopState` | Source | Description |
| :--- | :--- | :--- |
| `jira_project_key` | `opencode.json` | Clé du projet Jira (ex: `COUVBOIRE`) |
| `jira_epic_key` | `opencode.json` | Clé de l'Epic de rattachement (ex: `COUVBOIRE-700`) |
| `jira_default_subtasks` | `opencode.json` | Liste des sous-tâches à créer par défaut |
| `jira_subtask_mapping` | `opencode.json` | Dictionnaire de mappage nom → ID de type Jira |
| `jira_default_billing_id` | `opencode.json` | ID du centre de facturation (optionnel) |
| `jira_default_component_id` | `opencode.json` | ID ou nom du composant Jira (optionnel) |

> Si `billing_id` ou `components` sont absents ou invalides, le moteur bascule automatiquement vers un **payload minimal** (fallback résilient) sans bloquer la création.
