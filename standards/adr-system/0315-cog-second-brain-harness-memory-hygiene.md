# ADR-0315 : Adoption des Patterns COG (Verification Harness, Verifiers Read-Only & Memory Hygiene)

* **Statut** : Proposé
* **Décideurs** : Équipe Architecture mLoop, Agent Orchestrateur
* **Date** : 13 août 2026

---

## 🚀 Contexte & Problématique

L'analyse R&D du framework open source **COG Second Brain** (`huytieu/COG-second-brain`) a mis en évidence plusieurs patterns avancés d'auto-évolution d'agents IA, inspirés de *gstack* et *gbrain* (Garry Tan) :
1. **Économie de Tokens via Workers Asynchrones** : Les agents secondaires écrivent leurs logs bruts dans des fichiers temporaires et ne renvoient qu'un pointeur/statut au pilote.
2. **Read-Only Verifiers (Biais de Narrativisation)** : Un agent vérificateur ne doit jamais lire la synthèse rédigée par l'agent exécuteur, mais observer directement l'artefact produit à la racine.
3. **Memory Hygiene Sweeps** : Les faits persistés en mémoire doivent comporter un score de confiance et une estampille de fraîcheur (`last_verified`).

---

## 💡 Décisions d'Architecture

1. **Adoption du Moteur Memory Hygiene (`python src/swarm.py memory-hygiene`)** :
   - Mise en place d'un balayage de santé de la mémoire d'état mLoop.
   - Les preuves `memory/evidence/<STORY_ID>_evidence.json` sont estampillées avec `last_verified` et une note de confiance (`HIGH`, `MEDIUM`, `LOW`).

2. **Isolation des Verifiers (Avocat du Diable / Sentinel)** :
   - L'agent Sentinel et les sous-tâches d'audit `rubber_duck` et `wikifix` observent les fichiers Markdown/JSON bruts sur disque sans charger les résumés d'exécution contextuels.

3. **Traçabilité V-Model dans `EvidencePackEngine`** :
   - Alignement 1:1 entre chaque critère d'acceptation du Frontmatter/Gherkin et sa ligne de preuve dans l'EvidencePack.

---

## 📈 Conséquences

* **Positives** :
  * Réduction drastique des hallucinations et du "narrativisation bias" lors de la validation des récits.
  * Diminution de l'encombrement du contexte modèle.
  * Détection automatique des faits obsolètes ou périmés dans le Knowledge Graph local.
* **Point d'Attention** :
  * Nécessite l'exécution régulière du guardrail `memory-hygiene` lors des cycles de calibration mLoop (`swarm.py calibrate`).
