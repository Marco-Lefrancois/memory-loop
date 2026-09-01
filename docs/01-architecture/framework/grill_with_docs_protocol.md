# 🥩 Le Protocole "Grill with Docs" (Grill Me)

Le **Grill with Docs** (ou *Grill Me*) est le processus central de la **Phase 2 : PLAN / ARCHI** du cycle Spec-Driven en 5 Phases (Spec -> Plan -> Build -> Validate -> Ship). C'est une entrevue interactive ciblée entre l'Humain et l'agent `plan` (Stratégie & Architecture).

---

## 1. Objectif du Protocole
L'objectif est d'éliminer toute ambiguïté fonctionnelle ou technique **avant** de générer les spécifications et récits du backlog. Plutôt que de rédiger au hasard, l'agent force l'utilisateur à prendre des décisions fermes sur les cas limites (*Edge Cases*), le vocabulaire métier et les contraintes d'architecture.

### 1.1 Le "Project Bootstrap Grill" (Nouveau Projet)
Lorsqu'un projet est fraîchement initialisé, l'agent exécute la commande `python src/swarm.py grill` pour calibrer les contraintes globales. Il clarifie (toujours **une question à la fois**) :
1. **L'Archétype du Projet** : S'agit-il d'un projet `software` (code source, tests), `knowledge-base` (documentation, graphes) ou `infrastructure` (scripts, CI/CD) ?
2. **La Frontière Analytique** : Quel est le livrable final attendu (un T-shirt sizing rapide, un PRD ou des stories tracer-bullet verticaux) ?
3. **Les Dépendances Inamovibles** : Y a-t-il des bibliothèques, frameworks ou contraintes externes inamovibles (ex: .NET MAUI, OneTrust SDK) ?

## 2. Le Format Strict : 1 Question + 1 Recommandation
Pour éviter d'ensevelir l'Humain sous une montagne de questions, l'agent ne pose **jamais plus d'une question à la fois**.

Chaque interaction doit comporter :
1. **Exploration Silencieuse (Search-First)** : L'agent **DOIT** chercher la réponse dans le graphe (`graphify query`) ou le code source avant de poser sa question. Si la réponse existe, la question est omise.
2. **Une question ciblée**.
3. **Une recommandation d'ingénierie** formulée par l'agent.
4. **Une illustration d'un cas limite (Edge Case)**.

## 3. L'Ubiquitous Language (CONTEXT.md)
Le cœur du Grill est la chasse au vocabulaire flou. Dès qu'un terme métier est utilisé de manière ambiguë, l'agent demande sa définition stricte et met immédiatement à jour le fichier `CONTEXT.md` à la racine du projet.

## 4. Le Processus de Cristallisation & Registre OQ
Dès que l'utilisateur répond, l'agent **cristallise immédiatement la décision** sur le disque :
1. Mise à jour de `CONTEXT.md` ou des directives `business.md` / `tech.md`.
2. Création d'un **ADR Minimaliste** (dans `docs/01-architecture/adrs/`) si la décision impacte la structure globale.
3. Si une ambiguïté métier persiste sans réponse possible immédiate, consignation formelle dans `docs/04-transverse/00-questions-ouvertes.md` sous le tag `OQ-XXX`.

À la fin de l'entrevue, l'agent produit les récits verticaux dans `backlog/stories/` prêts pour la phase 3 (BUILD) et la validation des **4 Piliers Gherkin** et des **EvidencePacks** en phase 4 (VALIDATE).
