---
id: MLOOP-130-BE
jira_key: ''
epic_key: EPIC-13-CODE-GRAPH-INTELLIGENCE
type: Spike
title: 'Spike PoC Graft vs CodeGraph : Benchmark Empirique Croisé (pull vs push, tokens/call)'
tags: [core, benchmark, code-intelligence]
origin: SPEC_SLICING
source_ref: DOSSIER-GRAFT-§4/Extraits-12-17
macro_size: S
status: SHIPPED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by: ''
created_at: '2026-09-21'
promoted_at: '2026-09-21'
content_hash: 3730f2230732b90b
---

# Spike PoC Graft vs CodeGraph : Benchmark Empirique Croisé (pull vs push, tokens/call)

---

## Description
**En tant qu'** Architecte du framework mLoop,
**je veux** exécuter un benchmark empirique croisé reproductible confrontant Graft (Trail/Nanonets) et CodeGraph mLoop sur un corpus de code tiers neutre,
**afin de** trancher sur preuve — et non sur doctrines auto-déclarées — les choix d'architecture de l'épopée EPIC-13 avant tout développement.

---

## Contexte & Périmètre

### Contexte Métier
Aucun des deux moteurs de contexte de code ne publie de benchmark mutuellement comparable : les gains revendiqués par chaque camp sont auto-déclarés avec des protocoles de mesure différents. Le seul protocole publié (benchmark à trois bras de Graft : à froid, push, pull) conclut qu'un mode « pull » (outils consultables à la demande) bat le mode « push » (injection contextuelle) en justesse — un résultat contre-intuitif qui, s'il se confirme, oriente toute la couche de contexte de l'épopée. Le spike produit une preuve indépendante, reproductible et opposable avant que les récits aval ne s'engagent.

### In-Scope
- Protocole de benchmark reproductible : dépôt tiers neutre (~30-40 fichiers) cloné dans le bac à sable dédié, liste figée de ~10 corrections de bugs historiques du dépôt servant de vérité terrain, graine aléatoire consignée avant tout run
- Exécution des deux moteurs (Graft et CodeGraph) en trois bras de mesure (à froid, push, pull) sur le même corpus et les mêmes questions de navigation
- Mesure de quatre métriques communes : jetons par appel, nombre d'appels d'outils, latence, justesse de rappel (fichiers identifiés par l'agent vs fichiers réellement touchés par le correctif humain)
- Rapport d'arbitrage consigné dans le dossier de preuves, avec tableau croisé et recommandation argumentée pour l'épopée

### Out-of-Scope
- Toute modification du code source du framework (exécution en bac à sable isolé, dépôt principal et moteur intacts)
- Toute décision d'intégration définitive Graft/CodeGraph (l'arbitrage appartient aux récits aval et, le cas échéant, à une ADR postérieure fondée sur les preuves)
- Comparaison avec les benchmarks officiels des éditeurs (protocoles non comparables, exclus du périmètre)

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*

#### 1. Exécution d'un Run de Benchmark
* **Entrée Métier** : le dépôt tiers cloné dans le bac à sable, la liste figée des corrections historiques retenues, la configuration des deux moteurs et le numéro de graine du run.
* **Règles d'admissibilité & Validation** : le corpus et la graine sont consignés avant le premier run ; les agents de test sont à froid (aucune exposition antérieure au corpus) ; les deux moteurs sont évalués sur l'ensemble identique de questions ; aucun run ne démarre sans sa fiche de protocole pré-remplie.
* **Traitement & Algorithme Métier** : exécution des trois bras (à froid, push, pull) pour chaque moteur sur la liste de bugs ; collecte des compteurs par question ; comparaison des fichiers identifiés par l'agent aux fichiers du correctif humain ; agrégation par moteur et par bras.
* **Résultat Métier & Mutations** : un tableau croisé (moteur × bras × métrique), un verdict argumenté consigné dans le rapport d'arbitrage, consommé tel quel par les récits aval de l'épopée.
* **Cas de Rejet Métier** : un run est invalide et exclu du verdict si le corpus a été modifié entre deux runs, si la graine n'est pas consignée, ou si un moteur est indisponible pour un bras entier (aucun verdict partiel admis sur un sous-ensemble incomplet).

### Contrats d'échange API
- N/A — Spike local sans interface d'échange ; le livrable est le rapport d'arbitrage.

---

## Décisions de Cadrage (Grill-Me 1:1 — 21/09/2026)
| # | Décision | Arbitrage & Rationale |
| :---: | :--- | :--- |
| 1 | **Corpus** : dépôt tiers neutre (~30-40 fichiers, bibliothèque OSS connue) | Seul protocole « à froid » défendable — le code du framework est contaminé par les analyses de cadrage de la session |
| 2 | **Vérité terrain** : corrections de bugs historiques du dépôt tiers | Zéro biais circulaire — fichiers réellement touchés par le correctif humain ; plus fort que le proxy « fichiers modifiés » de Graft |
| 3 | **Environnement** : bac à sable dédié sous le dossier scratch/ du projet | Clones jetables, dépôt principal et moteur intacts ; le worktree éphémère reste réservé aux spikes touchant le moteur |
| 4 | **Forme du verdict** : rapport d'arbitrage consigné dans le dossier de preuves | ADR différée et conditionnelle — rédigée après exécution uniquement si une décision transversale consolidée émerge ; une ADR pré-écrite inverserait le flux fondé sur les faits |

---

## Definition of Ready (DoR)

### 1. Documents Sources & Traçabilité
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/ANALYSE-GRAFT-TRAILHQ_fact_dossier.md`](../../memory/evidence/ANALYSE-GRAFT-TRAILHQ_fact_dossier.md)
- 📦 **EvidencePack** : [`memory/evidence/MLOOP-130-BE_evidence.json`](../../memory/evidence/MLOOP-130-BE_evidence.json)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **ADR d'Architecture** : [ADR-0204 — Architecture de Graphe à Double Moteur (Graphify/CodeGraph)](../../../../standards/adr-system/0204-dual-engine-graph-architecture-graphify-codegraph.md)
- 🧠 **Nœud de Connaissance** : [KN-020 — Dual Engine Graph (CodeGraph & Graphify)](../../../../docs/06-knowledge/03-graph-engineering/KN-020_dual_engine_graph_codegraph_graphify.md)

### 3. Paquet OpenSpec (Handoff Développeur)
- N/A — Spike : le livrable est le rapport d'arbitrage, non un paquet de handoff. La spécification d'exécution est le protocole consigné dans le dossier de preuves.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Benchmark empirique croisé Graft vs CodeGraph

  # PILIER 1 — NOMINAL (Happy Path & Persistance)
  Scénario: Exécution nominale du benchmark complet sur le corpus tiers
    Étant donné un dépôt tiers neutre cloné dans le bac à sable dédié
    Et une liste figée de dix corrections de bugs historiques servant de vérité terrain
    Et une graine aléatoire consignée dans la fiche de protocole du run
    Quand l'opérateur exécute les trois bras de mesure pour chacun des deux moteurs
    Alors chaque question de navigation produit ses compteurs de jetons, d'appels d'outils et de latence
    Et la justesse de chaque agent est calculée contre les fichiers du correctif humain
    Et le tableau croisé final est consigné dans le rapport d'arbitrage
    Et le verdict est référencé par les récits aval de l'épopée

  # PILIER 2 — EXCEPTIONS & REJETS MÉTIER
  Scénario: Rejet d'un run dont la graine ou le corpus n'est pas conforme
    Étant donné un run de benchmark préparé sur le corpus tiers
    Mais que la graine du run n'a pas été consignée avant exécution
    Ou que le corpus a été modifié depuis le run précédent
    Quand l'opérateur tente de comptabiliser le run dans le verdict
    Alors le run est marqué invalide et exclu de toute agrégation
    Et le motif de rejet est consigné dans le rapport d'arbitrage
    Et aucun verdict partiel n'est admis sur un sous-ensemble de bras incomplet

  # PILIER 3 — RÉSILIENCE TECHNIQUE (Timeouts, Mode Dégradé)
  Scénario: Indisponibilité ou temporisation d'un moteur pendant un run
    Étant donné un run en cours d'exécution sur les deux moteurs
    Mais qu'un moteur devient indisponible ou dépasse sa temporisation d'exécution
    Quand la temporisation maximale du moteur est atteinte
    Alors le run est interrompu proprement sans altérer les mesures déjà consignées
    Et le moteur défaillant est signalé explicitement dans la fiche du run
    Et le bras incomplet est exclu du verdict plutôt que complété par estimation

  # PILIER 4 — OBSERVABILITÉ & REPRODUCTIBILITÉ
  Scénario: Traçabilité complète de chaque run pour reproductibilité
    Étant donné un run de benchmark terminé avec succès
    Quand l'opérateur consulte la fiche du run dans le rapport d'arbitrage
    Alors il retrouve la graine, l'empreinte du corpus et la version des deux moteurs
    Et les compteurs par question sont restituables question par question
    Et un tiers peut rejouer le run à l'identique à partir de la seule fiche consignée
```
