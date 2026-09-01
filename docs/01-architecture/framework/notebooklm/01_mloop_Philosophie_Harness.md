# mLoop - 01. Philosophie & Ingénierie de Harnais (Harness Engineering)

## Introduction au concept de Harnais
L'écosystème mLoop (Memory Loop Autonomous Engine) repose sur le principe fondamental du **Harness Engineering**. 
Contrairement aux approches traditionnelles centrées sur le prompt engineering, mLoop considère l'intelligence brute du modèle (LLM) comme une simple commodité (le "moteur").
La véritable valeur ajoutée réside dans l'infrastructure qui l'entoure (le "harnais"), qui garantit la fiabilité, la mémoire, le respect strict des règles d'affaires et la réversibilité des actions.

## Pathologies des Agents et Solutions
Le harnais mLoop est spécifiquement conçu pour contrer deux pathologies majeures observées chez les agents autonomes :

1. **La pourriture du contexte (Context Rot)** 
   * **Problème** : L'agent se noie dans l'historique de ses propres logs, atteint la "Dumb Zone" de sa fenêtre de contexte, et perd le fil de son objectif.
   * **Solution mLoop** : Le compactage sémantique et la fin de session propre via le skill **handoff** exécuté par l'agent de l'IDE. Il génère un rapport de transition (`memory/sessions/handoff.md`) et réinitialise la mémoire vive (Session Recall) tout en effectuant des requêtes chirurgicales via les ponts MCP pour ne charger que le contexte utile.

2. **La mémoire obsolète (Stale but Confident)**
   * **Problème** : L'agent agit avec certitude en fonction d'un état passé qui a été modifié depuis (ex: un autre développeur a changé le code).
   * **Solution mLoop** : L'obligation absolue de vérification de la vérité terrain (*Ground Truth Verification*). Avant toute décision critique, l'agent force l'auto-synchronisation de l'état pour confronter ses hypothèses à la réalité du code source physique.

## Séquence d'Amorçage Obligatoire (Boot Sequence Anti-Amnésie)
Pour garantir la souveraineté du harnais, tout agent mLoop doit exécuter **au tout premier tour de parole** la séquence mécanique d'amorçage :
1. `python src/swarm.py resume --project <nom_projet>` (Restauration d'état et anti-amnésie).
2. `loop_mem_search` (Fact-Search RAG).
3. `graphify query` (Exploration des dépendances du graphe).
4. `python src/swarm.py vibe-check --project <nom_projet>` (Guardrail pré-vol 5 contrôles).
5. `python src/swarm.py focus --project <nom_projet> --story <chemin>` (Verrou d'attention sur la story active).

**Règles d'Or du Harnais** :
* **Zero Raw FS Crawl** : Interdiction stricte d'exécuter des listings récursifs (`ls -R`, `dir /s`, `find .`) ou des recherches floues avant l'exécution complète de la Boot Sequence.
* **Zero-Fail Carryover** : Si une commande CLI renvoie une erreur (Exit Code ≠ 0), l'agent a l'interdiction d'ignorer l'erreur. Il doit corriger la commande ou alerter l'humain avant toute modification.
