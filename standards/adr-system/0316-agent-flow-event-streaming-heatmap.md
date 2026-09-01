# ADR-0316 : Adoption des Patterns Agent Flow (Live Event Streaming JSONL & File Attention Heatmap)

* **Statut** : 🔴 Rejeté / Retiré (Retrait de l'intégration AgentFlow externe suite à l'arbitrage utilisateur)
* **Décideurs** : Équipe Architecture mLoop, Utilisateur
* **Date** : 13 août 2026

---

## 🚀 Contexte & Problématique

L'analyse R&D du visualiseur d'orchestration **Agent Flow** (`patoles/agent-flow`) a mis en évidence 3 pratiques clés pour l'observabilité et le debugging des systèmes d'agents autonomes :
1. **Émission d'Événements Atomiques JSONL en Temps Réel** : Les sessions d'agents émettent des journaux structurés (`events.jsonl`) suivis par tailing/SSE sans imposer de couplage direct avec un visualiseur spécifique.
2. **File Attention Heatmap** : Mesure dynamique des fichiers les plus fréquemment lus, modifiés ou référencés au cours d'un cycle de vie de story.
3. **Trajectory Replay à Coût Zéro** : Possibilité d'auditer et de rejouer des trajectoires d'exécution complexes à partir de logs JSONL sans ré-exécuter le modèle.

---

## 💡 Décisions d'Architecture

1. **Intégration du `EventLogger` JSONL (`memory/events.jsonl`)** :
   - Émission d'un flux JSONL append-only à chaque transition d'état, appel d'outil CLI mLoop ou événement Herdr.
   - Schéma d'événement standardisé : `timestamp`, `event_type`, `agent_id`, `file_attention`, `details`.

2. **Mesure d'Attention dans Focus Engine (`python src/swarm.py focus`)** :
   - Génération de la métrique `file_attention_heatmap` dans la mémoire de session pour prévenir la dispersion contextuelle et les modifications hors périmètre.

---

## 📈 Conséquences

* **Positives** :
  * Observabilité temps réel compatible avec tout outil tiers (`agent-flow-app`, extensions VS Code, dashboards).
  * Traçabilité déterministe pour le Replay de trajectoire et l'analyse post-mortem.
* **Point d'Attention** :
  * Rotation périodique du fichier `memory/events.jsonl` pour maîtriser la taille du disque.
