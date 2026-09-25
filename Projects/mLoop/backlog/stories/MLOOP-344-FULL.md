---
id: MLOOP-344-FULL
jira_key: ''
epic_key: EPIC-34-WFM-COGNITIVE-WIKI-GRAPH
type: Feature
title: Commande CLI mloop wiki-search, Intégration Grill-Me & Sonde Vibe-Check Check 30
tags:
- cli
- search
- vibe-check
- grill-me
- fullstack
status: DRAFT
grill_me: PENDING
invest_score: 6/6
layer: fullstack
macrostructure: workbench
blocked_by:
- MLOOP-340-BE
- MLOOP-341-BE
- MLOOP-342-BE
- MLOOP-343-BE
created_at: '2026-09-25'
ttl_cycles: 3
---

# Commande CLI mloop wiki-search, Intégration Grill-Me & Sonde Vibe-Check Check 30

---

## Description
**En tant qu'** Ingénieur Logiciel ou Agent Orchestrateur mLoop naviguant dans la mémoire du projet,  
**je veux** exécuter la commande CLI `mloop wiki-search --query <q>`, bénéficier de l'auto-réflexion lors des entrevues Grill-Me en Phase 2, et valider l'intégrité du graphe cognitif via le Check 30 du Vibe-Check,  
**afin d'** exploiter de manière transparente et déterministe le moteur Wiki Graph dual-layer de bout en bout du cycle de vie mLoop.

---

## Contexte & Périmètre

### Contexte Métier
Ce récit couronne l'épopée EPIC-34 en exposant les capacités du Wiki Graph dual-layer et de la recherche réflexive sous forme de commande CLI conviviale, tout en les intégrant aux processus fondamentaux de mLoop : la préparation des entrevues Grill-Me (Phase 2) et la barrière pré-vol Vibe-Check (Phase 4).

### In-Scope
- Handler de commande CLI `src/commands/handlers/wiki_search.py` (strictement $\le 300$L, `RULE-AST-01`).
- Commande CLI unifiée enregistrée dans le dispatcher Click / Swarm :
  `python src/swarm.py wiki-search --query "<texte>" [--project <nom>] [--budget 4] [--reject-mode] [--format json|text]`.
- Câblage dans le moteur Grill-Me (`src/pipelines/grill_engine.py`) pour alimenter automatiquement le panier de preuves amont.
- Création du **Check 30 dans Vibe-Check** (`src/pipelines/vibe_check.py`) :
  - Vérifie la présence des tables du Wiki Graph (`wiki_entities`, `wiki_passages`, `wiki_cross_links`).
  - Contrôle l'absence d'hyper-arêtes orphelines.
  - Valide que le ratio d'entités sans ancrage textuel reste sous le seuil d'alerte (10%).
- Rendu visuel soigné en console (table Rich avec score de complétude, nombre de passes et extraits de preuves).

### Out-of-Scope
- Interface web graphique dédiée.
- Modifications du noyau Click CLI existant.

---

## Critères d'acceptation

### Spécifications de l'Interface & UX *(fullstack)*
- **Affichage Console** : En mode texte, restitution d'un tableau formaté indiquant le statut de recherche (`Arrêt anticipé`, `Budget épuisé`), le nombre de tours réels, la note de couverture et les 3 passages les plus probants avec citation verbatim.
- **Mode JSON** : Sortie structurée JSON pure pour consommation directe par d'autres scripts ou sous-agents (`--format json`).

### Opérations Métier & Logique Backend *(fullstack)*
#### 1. Traitement de la Commande CLI (`handle_wiki_search`)
* **Entrée Métier** : Argumentaire CLI parsé (requête, options de budget, drapeau de mode Reject).
* **Règles d'admissibilité & Validation** : La requête doit comporter au moins 3 caractères ; le projet cible doit exister.
* **Traitement & Algorithme Métier** :
  1. Chargement de l'état du projet et ouverture sécurisée de `loop_mem.db`.
  2. Déclenchement de la recherche réflexive `execute_reflective_search`.
  3. Si `--reject-mode` est actif, exécution du contrôle de fondement via `audit_grounding_reject_mode`.
  4. Restitution du résultat selon le format demandé.
* **Résultat Métier & Mutations** : Code retour 0 si des preuves conformes sont trouvées, 1 si échec ou rejet sans preuve.
* **Cas de Rejet Métier** : Sortie avec code 1 et motif explicite `EVIDENCE_REJECTED` si le mode Reject échoue.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- `src.commands.handlers.wiki_search:handle_wiki_search(args, state, project_path) -> int`
- `src.pipelines.vibe_check:check_wiki_graph_integrity(project_path: Path) -> tuple[bool, str]`

#### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `handle_wiki_search` | `src.commands.handlers.wiki_search:handle_wiki_search` | Exécution CLI de la recherche réflexive | `(args, state, project_path) -> int` |
| `check_wiki_graph_integrity` | `src.pipelines.vibe_check:check_wiki_graph_integrity` | Sonde Check 30 du Vibe-Check | `(project_path: Path) -> tuple[bool, str]` |

---

## Règles d'affaires

- **Sonde Pré-Vol Bloquante** : Tout échec du Check 30 en Phase 2 ou Phase 4 bloque l'avancement du cycle de vie (`vibe-check FAIL`).
- **Transparence d'Arrêt** : La sortie console doit explicitement mentionner si la recherche s'est arrêtée par complétude anticipée ou par atteinte du budget maximal.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves** : [`memory/evidence/EPIC-34_wfm_fact_dossier.md`](../../memory/evidence/EPIC-34_wfm_fact_dossier.md)
- 📄 **Publication de Référence** : WFM (*arXiv:2609.18182*).

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Guide CLI Pipeline** : [`standards/protocols/CLI_PIPELINE_GUIDE.md`](../../standards/protocols/CLI_PIPELINE_GUIDE.md)
- 📜 **ADR Associé** : [ADR-0395](../../standards/adr-system/0395-wiki-graph-dual-layer-et-fact-search-reflexif-wfm.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Commande CLI mloop wiki-search & Check 30 Vibe-Check

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Exécution CLI réussie d'une recherche avec affichage console
    Étant donné un projet mLoop initialisé avec un Wiki Graph peuplé
    Quand l'utilisateur lance "python src/swarm.py wiki-search --query 'ADR-0392' --project MonProjet"
    Alors la commande retourne un code de sortie 0
    Et le tableau console affiche le nombre de passes et les extraits pertinents

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Échec CLI en mode Reject lorsqu'aucune preuve n'existe
    Étant donné une requête portant sur un concept fictif non documenté
    Quand la commande est lancée avec l'option "--reject-mode"
    Alors la commande s'interrompt avec un code de sortie 1
    Et le message "EVIDENCE_REJECTED : Preuve documentaire insuffisante" est affiché

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Détection par la sonde Check 30 d'un schéma corrompu ou incomplet
    Étant donné une base SQLite où la table "wiki_cross_links" a été accidentellement supprimée
    Quand le Vibe-Check exécute le Check 30
    Alors la sonde retourne un statut d'échec "FAIL"
    Et la description précise la table manquante à reconstituer

  # UX, OBSERVABILITÉ & EMPTY STATE (Spinners, Retours Écran, Logs)
  Scénario: Export au format JSON strict pour orchestration agentique
    Étant donné une recherche invoquée avec "--format json"
    Quand le flux de sortie est capturé
    Alors le résultat est un objet JSON syntaxiquement valide contenant les clés "rounds", "evidence" et "coverage"
```
