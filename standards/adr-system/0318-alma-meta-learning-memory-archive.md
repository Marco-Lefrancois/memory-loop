---
id: 0318
validation_rules: []
---

# ADR-0318 : Adoption des Patterns ALMA (Meta-Learned Memory Archive & Dynamic Strategy Selection)

* **Statut** : Proposé
* **Décideurs** : Équipe Architecture mLoop, Agent Orchestrateur
* **Date** : 13 août 2026

---

## 🚀 Contexte & Problématique

L'analyse R&D du projet **ALMA** (`zksha/alma` — *ICLR 2026 Workshop Oral: MemAgents*) démontre que les structures de mémoire codées en dur (logs texte simples ou schémas fixes) sous-performent par rapport à une **mémoire auto-évolutive (Meta-Learned Memory Architecture)** :
1. **Archive de Designs Mémoire (`memo_archive/`)** : Les stratégies de mise à jour et de recherche en mémoire sont archivées par hash SHA avec leurs scores de succès.
2. **Auto-Adaptation du Profil Mémoire selon la Tâche** : L'agent sélectionne dynamiquement la stratégie mémoire optimale (ex: Trajectory Retrieval vs Dynamic Cheatsheet vs Context Breakdown) en fonction de la complexité du domaine métier.
3. **Réflexion Méta-Agent sur les Échecs** : Analyse des logs d'erreurs pour proposer de nouvelles mutations de structure mémoire.

---

## 💡 Décisions d'Architecture

1. **Création de l'Archive de Strategies Mémoire (`memory/memo_archive/`)** :
   - Ajout du dossier `Projects/<project>/memory/memo_archive/` pour conserver les profils de mémoire validés (ex: `default_maui.json`, `api_sso.json`, `ads_tracking.json`).

2. **Intégration du profil `memory_profile` dans `MemoryHygieneAgent` (`src/pipelines/memory_hygiene.py`)** :
   - Évaluation dynamique de la stratégie mémoire la plus efficace pour chaque récit et génération des recommandations d'optimisation contextuelle dans `SESSION_MEMORY_HEALTH.md`.

3. **Commande CLI `python src/swarm.py memo-search`** :
   - Nouvelle commande permettant de rechercher et d'injecter automatiquement la meilleure stratégie de mémoire archivée dans le `LoopState` avant les phases `plan` et `build`.

---

## 📈 Conséquences & 6 Piliers d'Impact

* **Performance & Précision RAG** : Réduction du bruit contextuel et gain d'attention sur les éléments clés de la story.
* **Auto-Apprentissage Continu** : Chaque session réussie ou échouée enrichit l'archive `memo_archive/`.
* **Statut Stateless & Déterministe** : Les profils sont enregistrés sous forme de schémas JSON légers sous version control.
