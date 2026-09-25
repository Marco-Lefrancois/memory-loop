---
id: MLOOP-051-BE
jira_key: '-'
epic_key: EPIC-6-OKF-ENCLAVE
type: Feature
title: Moteur de Recherche Hybride Tri-Flux et Score de Confiance
tags: [hybrid-search, rrf, vector, fts, graphify]
status: SHIPPED
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-6-OKF-ENCLAVE] Moteur de Recherche Hybride Tri-Flux et Score de Confiance (MLOOP-051-BE)

---

## Description
**En tant qu'** Agent Analyste et Sentinelle du framework mLoop,  
**je veux** interroger la base de connaissances via un moteur hybride fusionnant recherche textuelle BM25, embeddings vectoriels et relations de graphe Graphify,  
**afin d'** extraire les faits vérifiés et règles d'architecture sans hallucination ni dérive contextuelle.

---

## Contexte & Périmètre

### Contexte Métier
Le `fact-search` exige une haute précision. Une recherche purement vectorielle manque de précision lexicale, tandis qu'une recherche purement FTS5 ignore la proximité sémantique. Ce composant orchestre les trois flux et les consolide via Reciprocal Rank Fusion (RRF).

### In-Scope
- Fusion RRF (Reciprocal Rank Fusion avec $k=60$) combinant FTS/BM25, similarité vectorielle et traversée de graphe.
- Calcul d'un score de confiance $C \in [0, 1]$ basé sur la corroboration des sources.
- Dépriorisation déterministe des assertions supplantées (`superseded`).
- Mode dégradé transparent en cas d'absence d'embeddings.

### Out-of-Scope
- Indexation de bases de données cloud tierces.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Fusion des Flux de Recherche RRF
* **Entrée Métier** : Requête de recherche en langage naturel, nombre maximal de résultats `top_k`.
* **Traitement & Algorithme Métier** : Exécution concurrente des trois flux (textuel, vectoriel, graphe), attribution des rangs et calcul du score combiné $RRF(d) = \sum \frac{1}{k + r_i(d)}$.
* **Résultat Métier & Mutations** : Liste ordonnée de faits avec scores de confiance et sources citées.
* **Cas de Rejet Métier** : Requête vide rejetée avec avertissement sans crash du serveur.

---

## Règles d'affaires

- **[Fusion RRF Standard]** : La fusion des classements utilise l'algorithme Reciprocal Rank Fusion avec constante standard $k=60$.
- **[Dépriorisation des Assertions Supplantées]** : Tout fait obsolète avec lien de supersession est déclassé sous l'assertion active.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Moteur de Recherche Hybride Tri-Flux et Score de Confiance

  # CHEMIN NOMINAL
  Scénario: Recherche hybride nominale combinant texte, similarité et graphe
    Étant donné une base de connaissances mLoop synchronisée avec SQLite et le graphe
    Quand l'agent lance une recherche hybride sur un concept d'architecture
    Alors le moteur fusionne les classements textuel, vectoriel et graphe via RRF
    Et retourne une liste ordonnée de faits avec leurs scores de confiance

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Déclassement immédiat d'une règle métier supplantée
    Étant donné une ancienne règle marquée comme supplantée par une règle plus récente
    Quand une recherche hybride porte sur cette contrainte
    Alors la règle obsolète est dépriorisée en fond de classement
    Et la référence vers la règle de remplacement est explicite

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Bascule transparente en mode BM25 et graphe sans modèle vectoriel
    Étant donné l'indisponibilité du service d'embeddings vectoriels
    Quand une recherche est déclenchée
    Alors le moteur bascule sans erreur sur la fusion duale FTS5 et Graphe
    Et émet un log de diagnostic sur le mode dégradé

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Restitution de la latence et traçabilité des rangs fusionnés
    Étant donné une recherche hybride multi-sources
    Quand les résultats sont restitués à l'agent
    Alors le temps d'exécution total reste maîtrisé sous 200 millisecondes
    Et le détail de la décomposition des rangs est consigné pour audit
```
