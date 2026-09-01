---
name: archify
description: Création et validation de diagrammes d'architecture, workflows, séquences et flux de données interactifs vectoriels (HTML standalone, SVG zoomable, vues filtrées, animations de flux trace).
license: MIT
metadata:
  version: "2.16"
  author: tt-a1i / Memory Loop
---

# Archify — Diagrammes d'Architecture Interactifs mLoop

Créer des diagrammes interactifs standalone (.html) vectoriels et zoomables à partir d'une spécification déclarative JSON IR typée.

## 🚀 Commandes Rapides

```bash
# 1. Validation de la spécification JSON IR (9 contrôles qualité Showcase)
python tools/archify/archify_runner.py validate <chemin_json> --quality showcase

# 2. Compilation et livraison du diagramme HTML
python tools/archify/archify_runner.py deliver <chemin_json> <chemin_html> --quality showcase --open

# 3. Commande CLI Swarm mLoop
python src/swarm.py archify --file <chemin_json> --output <chemin_html>
```

## 📐 Types de Diagrammes Supportés

| Type | Cas d'Usage mLoop |
|---|---|
| `architecture` | Composants, services Azure/Dataverse, frontends Canvas/Model-driven, persistance |
| `workflow` | Processus métier, gates d'approbation, pipelines CI/CD, orchestration d'agents |
| `sequence` | Chaînes d'appels API, cycle de requêtes, événements asynchrones Service Bus |
| `dataflow` | Pipelines de données, flux d'ingestion MarkItDown, synchronisations Jira/Git |
| `lifecycle` | Machines à états, transitions de statuts de stories (IN_ANALYZE, READY_FOR_DEV) |

## 🛡️ Règles Clés de Rédaction JSON IR

1. **Positions & Tailles explicites** : Chaque composant requiert `pos: [x, y]` et `size: [w, h]`.
2. **Types de composants normalisés** : `frontend`, `backend`, `database`, `cloud`, `security`, `messagebus`, `external`.
3. **Variantes de connexion** : `default`, `emphasis`, `security`, `dashed`.
4. **Vues interactives (`views`)** : Définir 2 à 4 vues ciblées avec `focus: ["id_1", "id_2"]` pour permettre à l'utilisateur de filtrer les sous-parcours.
5. **Cartes explicatives (`cards`)** : Définir les 3 fiches de synthèse avec `dot: "cyan"|"emerald"|"rose"`.
6. **Zéro croisement de lignes** : Organiser les composants en colonnes/lignes parallèles et utiliser `via` ou `labelAt` pour éviter tout chevauchement.

---

## ⚡ 7 Principes Cardinaux de Causalité & Processus (Anti-Hallucination de Flux)

Pour tout diagramme de pipeline, de cycle de vie ou de workflow séquentiel :

1. 🚫 **Interdiction du Faux Parallélisme (No Fake Parallelism)** : Ne JAMAIS relier horizontalement des composants intermédiaires simplement pour remplir les lignes d'une grille. Si une étape dépend de la complétion d'une phase, elle ne peut démarrer que lorsque le livrable de cette phase est produit.
2. 🏛️ **Pattern Canonique Stage-Gate (Entrée ➔ Moteur ➔ Livrable)** : Dans chaque phase :
   - **Haut (Row 1)** : Porte d'Entrée / Matière initiale (*Entry Gate*).
   - **Milieu (Row 2)** : Moteur de transformation / Traitement (*Core Engine*).
   - **Bas (Row 3)** : Livrable validé / Sortie (*Exit Gate & Deliverable*).
   - **Passage de témoin (Baton Pass)** : La phase $N+1$ démarre STRICTEMENT depuis le livrable de sortie (Row 3) de la phase $N$.
3. 👆 **Protocole du Test du Tracé au Doigt (Finger-Traceability)** :
   - Poser mentalement son doigt sur le tout premier composant.
   - Suivre les flèches : le chemin doit être 100% continu, sans saut magique, sans cul-de-sac et sans contournement de prérequis.
   - Aucun livrable ne peut exister sans ses sources réelles (ex: un SOW ne peut pas précéder l'ingestion).
4. 🧠 **Sémantique > Géométrie (Au-delà du Linter)** :
   - Un score `PASS 100%` du linter géométrique Archify valide uniquement l'absence de collisions SVG. Il ne garantit pas la vérité du flux métier.
   - L'agent a l'obligation formelle de valider la logique causale fonctionnelle avant de livrer.

