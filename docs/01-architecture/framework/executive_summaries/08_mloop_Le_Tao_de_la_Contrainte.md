# mLoop - 08. Le Tao de la Contrainte (Ingénierie de Harnais)

L'ingénierie de la contrainte (*Harness Engineering*) de mLoop s'aligne philosophiquement sur les concepts clés du **Tao Te Ching** pour forger l'identité de l'agent Antigravity (Système 2).

## 1. Le Wu Wei (La Non-Action) et le Harnais Sémantique
*   **Principe (Verset 11)** : *« Le vide au centre de la roue permet au char de se déplacer. C'est le vide à l'intérieur du vase qui permet de contenir l'eau. »*
*   **Transposition mLoop** : Le harnais de contraintes (le vide structuré) a plus de valeur que l'écriture désordonnée de code (la matière). 
    *   **Non-Action (Wu Wei Linter)** : Antigravity (Cerveau) a l'obligation de refuser la sur-ingénierie et la complexité superflue. Il travaille dans les contraintes existantes du projet sans rajouter d'abstractions inutiles.
    *   **Zéro Code Source** : L'analyse reste au niveau de la planification documentaire, déléguant la production physique du code à la machine ou aux développeurs externes.

## 2. Le Pu (Le Bloc non sculpté) et l'Isolation Fonctionnelle
*   **Principe (Verset 38)** : *« Le sage s'attache au fruit et non à la fleur, au solide et non au superficiel. »*
*   **Transposition mLoop** : Le backlog doit rester à l'état de "Bloc non sculpté", c'est-à-dire purement fonctionnel.
    *   **Zéro-Code dans le Backlog** : Interdiction absolue d'inclure des détails techniques d'implémentation (imports, dépendances, code JavaScript/Python) dans les récits. Les stories décrivent le *Quoi* (scénarios de test Gherkin) et non le *Comment*.

## 3. L'Eau et la Souplesse Cognitive (Context Flow)
*   **Principe (Verset 8)** : *« Le bien suprême est comme l'eau... elle bénéficie à toutes choses sans rivaliser avec elles. »*
*   **Transposition mLoop** : Le flux de contexte doit rester fluide et léger.
    *   **Requêtes MCP Chirurgicales** : Au lieu de saturer la mémoire vive de l'agent avec des documents statiques, l'information s'écoule dynamiquement depuis le graphe sémantique via les outils MCP.
    *   **Fin de session propre (Handoff)** : Pour contrer la pourriture du contexte (Context Rot), l'agent vide sa mémoire de session à chaque fin d'itération en générant un rapport `handoff.md`, retournant à un état de pureté et d'attention maximale.

## 4. Le Soufflet (Bellows) et la Mémoire Inépuisable
*   **Principe (Verset 5 & 48)** : *« L'espace entre le Ciel et la Terre est comme un soufflet. Il est vide et pourtant inépuisable. [...] Pour acquérir le savoir, ajoutez chaque jour. Pour acquérir le Tao, éliminez chaque jour. »*
*   **Transposition mLoop** : Une mémoire vive légère couplée à un rappel sémantique puissant.
    *   **RAG Sémantique L3** : Grâce à l'indexation in-memory Graphify, la mémoire de l'agent reste vide de logs inutiles mais inépuisable en termes de recherche d'informations.
    *   **Réduction RHO** : Le mécanisme RHO (*Retrospective Harness Optimization*) élimine le besoin de gonfler les invites de règles en condensant les erreurs passées sous forme de contraintes YAML légères.

## 5. L'Orchestration Invisible : "It happened by itself"
*   **Principe (Verset 17)** : *« Quand le travail du sage est fait, le peuple dit : "Cela s'est fait tout seul". »*
*   **Transposition mLoop** : L'exécution du workflow doit s'écouler sans heurts ni interventions manuelles superflues.
    *   **Event Bus déterministe** : Le Kernel (`swarm.py`) gère les transitions de phases (Analyze -> Plan -> QA) et la validation (`wikifix`) en tâche de fond. L'humain n'est sollicité que lorsque le système rencontre une impasse ou une ambiguïté d'affaires (HITL).
