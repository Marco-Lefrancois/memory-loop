# ADR-0200 : Graph Loop Architecture (Graphify & NetworkX SSOT)
## Statut : Accepté (Série 02xx - Graph Loop & Graphe de Connaissances)

---

## 1. Contexte

Dans un système complexe de spécification d'affaires, lire des fichiers Markdown de façon linéaire ou par recherche textuelle brute cause du bruit cognitif et masque les dépendances d'architecture (liens entre `ADR-*`, `RM-*`, `D-ARCH-*` et User Stories).

---

## 2. Décision

Nous officialisons la **Graph Loop Architecture** comme standard de navigation sémantique obligatoire :

1. **Graphe de Connaissances NetworkX (`graphify-out/`)** : Construction et mise à jour automatique du graphe persistant lors de chaque synchronisation (`python src/swarm.py sync`).
2. **Protocoles de Requêtes Obligatoires** :
   - `python -m graphify.cli path "<A>" "<B>"` : Analyse du plus court chemin de dépendance.
   - `graphify query "<question>"` : Extraction d'un sous-graphe ciblé.
   - `graphify explain "<concept>"` : Explication contextuelle approfondie.
3. **Priorité de Recherche** : Avant toute exploration de documentation ou interrogation de l'utilisateur, l'agent **doit impérativement** interroger le graphe sémantique local.

---

## 3. Conséquences

- **Précision Contextuelle** : Élimine les hallucinations de dépendances.
- **Économie de Tokens** : Réduit la taille des contextes injectés dans le LLM aux sous-graphes pertinents.
