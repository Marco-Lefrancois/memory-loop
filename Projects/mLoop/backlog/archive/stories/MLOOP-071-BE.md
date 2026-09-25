---
id: MLOOP-071-BE
jira_key: '-'
epic_key: EPIC-7-AGENTIC-OBSERVABILITY
status: SHIPPED
type: Feature
title: Intercepteur Boundary Tracing et Auto Offload OpaqueArtifactBus
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-7-AGENTIC-OBSERVABILITY] Intercepteur Boundary Tracing et Auto Offload OpaqueArtifactBus (MLOOP-071-BE)

## Description
**En tant que** Bus d'Exécution d'Outils et de Compétences mLoop,  
**je veux** intercepter automatiquement à la frontière d'exécution (Boundary Tracing) toute sortie d'outil dépassant 2 000 caractères ou 30 lignes,  
**afin de** persister la charge brute sous empreinte SHA-256 dans l'OpaqueArtifactBus et ne renvoyer qu'un descripteur compact au modèle, éliminant ainsi le Context Rot.

---

## Contexte
L'état de l'art mondial en observabilité agentique (notamment les travaux de recherche AgentSight et ADR-0354) démontre que charger des sorties d'outils volumineuses (résultats de crawls, scans AST, gros JSONs) sature la fenêtre de contexte et provoque des erreurs d'attention en cascade.
Ce récit implémente le wrapper déterministe `boundary_trace` dans `src/engine/artifacts/boundary_wrapper.py`. Tout résultat d'outil excédant les seuils normatifs est immédiatement persisté sur disque et substitué par un handle opaque fenêtré `mloop://artifacts/{sha256}`.

---

## Opérations API & Logique Backend

### Matrice des Opérations Backend
| Opération Métier | Contrat / Trigger | Validation & Préconditions | Succès Observable | Gestion Erreurs |
| :--- | :--- | :--- | :--- | :--- |
| **[Interception Frontière]** | `boundary_trace(tool_callable)` | Fonction callable d'outil MCP ou CLI valide | Exécution et capture de la sortie textuelle | Propagation transparente des exceptions d'outil |
| **[Auto-Offload Opaque]** | `offload_if_exceeds(output, max_chars=2000, max_lines=30)` | Sortie textuelle > 2 000 car. ou > 30 lignes | Fichier `{sha256}.dat` persisté, descripteur renvoyé | Renvoyé brut si en-deçà des seuils |
| **[Projection Fenêtrée]** | `get_artifact_slice(handle_id, start_line, end_line)` | Handle `mloop://artifacts/...` existant | Extraction des seules lignes demandées | Levée `FileNotFoundError` si handle inconnu |

---

## Règles d'affaires
* **[Seuil Physique de Déportation]** : Toute charge utile supérieure à 2 000 caractères ou 30 lignes est strictement interdite d'injection directe dans le prompt de l'agent.
* **[Immuabilité Cryptographique]** : Tout artefact déporté est nommé d'après son empreinte SHA-256 (`memory/artifacts/<prefix>/<sha256>.dat`) assurant une traçabilité inviolable.
* **[Aperçu Homogène Obligatoire]** : Le descripteur renvoyé au LLM contient au maximum 5 lignes d'en-tête et 5 lignes de pied, avec indication explicite de la commande pour extraire une tranche.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Intercepteur Boundary Tracing et Auto Offload OpaqueArtifactBus

  # 1. CHEMIN NOMINAL (Happy Path & Déportation Automatique)
  Scénario: Interception d'une sortie volumineuse et génération de handle opaque
    Étant donné un outil retournant un rapport JSON de 5 000 caractères et 120 lignes
    Quand l'outil est exécuté à travers le wrapper boundary_trace
    Alors la charge brute est automatiquement persistée sous son empreinte SHA-256
    Et le modèle reçoit un descripteur compact contenant "mloop://artifacts/"
    Et la taille du prompt reste strictement sous le seuil d'encombrement

  # 2. EXCEPTIONS & REJETS MÉTIER (Gestion des Contenus sous le Seuil)
  Scénario: Passage transparent pour les sorties courtes et concises
    Étant donné un outil retournant un statut textuel de 150 caractères sur 3 lignes
    Quand l'outil est exécuté à travers le wrapper boundary_trace
    Alors la sortie est retournée brute sans création de fichier artefact superflu
    Et aucun descripteur opaque n'est substitué

  # 3. RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Lecture Fenêtrée Résiliente)
  Scénario: Extraction fenêtrée d'une tranche spécifique d'un artefact volumineux
    Étant donné un artefact déjà persisté dans le bus sous un identifiant SHA-256 valide
    Quand l'agent demande la tranche des lignes 10 à 25 via get_slice
    Alors seules les 16 lignes ciblées sont lues depuis le disque
    Et l'intégralité du fichier n'est jamais chargée en mémoire vive

  # 4. UX & OBSERVABILITÉ (Traçabilité des Artefacts Déportés)
  Scénario: Émission de span d'observabilité lors du déport d'artefact
    Étant donné une opération de déportation automatique déclenchée par boundary_trace
    Quand l'artefact est écrit sur le disque local
    Alors un événement de type "artifact_persisted" est émis avec son hash SHA-256
    Et le span d'exécution indique le gain de tokens préservé
```
