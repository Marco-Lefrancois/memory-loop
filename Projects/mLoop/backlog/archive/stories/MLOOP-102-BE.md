---
id: MLOOP-102-BE
jira_key: ''
epic_key: EPIC-10-SOVEREIGN-EXCELLENCE
type: Feature
title: Consolidation du Flux Vectoriel RHO et Recherche Hybride sur Embeddings Locaux
tags:
- memory
- vector
- embeddings
- search
status: SHIPPED
layer: backend
invest_score: 6/6
created_at: '2026-09-21'
---

# Consolidation du Flux Vectoriel RHO et Recherche Hybride sur Embeddings Locaux

---

## Description
**En tant qu'**Opérateur du framework mLoop,
**je veux** disposer d'un flux vectoriel RHO consolidé et d'une recherche hybride (BM25 + Vector + Graph) fonctionnant sur des embeddings locaux (mxbai-embed-large),
**afin de** bénéficier d'une recherche sémantique souveraine sans dépendance API externe.

---

## Contexte & Périmètre

### Contexte Métier
Le système de mémoire RHO (Reusable Hypothesis Outcomes) produit des solutions d'erreurs documentées. Cependant, la recherche vectorielle actuelle dépend d'embeddings distants (OpenAI, Cohere). Pour des raisons de souveraineté et de coût, il faut consolider le flux vectoriel RHO et migrer vers des embeddings locaux (mxbai-embed-large via Ollama ou ONNX).

### In-Scope
- Consolidation du pipeline RHO (production, indexation, recherche)
- Intégration d'embeddings locaux (mxbai-embed-large)
- Recherche hybride BM25 + Vector + Graph
- Tests de performance et de qualité

### Out-of-Scope
- Refonte du système RHO existant
- Nouveau modèle d'embeddings
- Interface utilisateur

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Pipeline RHO Consolidé
- Le pipeline RHO produit des vecteurs d'embeddings locaux
- L'indexation est automatique après production d'une solution RHO
- La recherche vectorielle fonctionne hors-ligne (pas d'API externe)

#### 2. Recherche Hybride
- La recherche combine BM25 (texte) + Vector (sémantique) + Graph (relations)
- Le score de pertinence est un weighted average configurable
- Les résultats sont triés par pertinence décroissante

#### 3. Embeddings Locaux
- mxbai-embed-large est utilisé via Ollama ou ONNX Runtime
- Le modèle est chargé une seule fois au démarrage
- La latence d'embedding est < 100ms par chunk

---

## Règles Métier
- **RM-102-01** : La recherche hybride doit fonctionner sans connexion réseau (mode dégradé)
- **RM-102-02** : Le score de pertinence est normalisé entre 0 et 1
- **RM-102-03** : Les embeddings locaux sont stockés dans SQLite (pas de dépendance externe)

---

## Scénarios de test

### Pilier 1 — Chemin Nominal
```gherkin
Scénario : Recherche hybride avec embeddings locaux
  Étant donné une mémoire RHO avec 100 solutions indexées
  Quand l'utilisateur recherche "erreur de timeout"
  Alors les résultats combinent BM25 + Vector + Graph
  Et le top 3 contient des solutions pertinentes
```

### Pilier 2 — Exceptions & Rejets
```gherkin
Scénario : Mode dégradé sans réseau
  Étant donné un serveur Ollama indisponible
  Quand l'utilisateur lance une recherche
  Alors la recherche utilise uniquement BM25
  Et un avertissement est émis
```

### Pilier 3 — Résilience & Mode Dégradé
```gherkin
Scénario : Index vectoriel corrompu
  Étant donné un index vectoriel corrompu
  Quand l'utilisateur lance une recherche
  Alors l'index est reconstruit automatiquement
  Et la recherche retourne des résultats (BM25 uniquement pendant la reconstruction)
```

### Pilier 4 — UX & Observabilité
```gherkin
Scénario : Latence d'embedding acceptable
  Étant donné un chunk de 512 tokens
  Quand l'embedding local est calculé
  Alors la latence est inférieure à 100ms
```
