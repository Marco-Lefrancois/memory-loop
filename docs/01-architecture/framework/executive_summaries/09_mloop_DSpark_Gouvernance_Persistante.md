# mLoop - 09. DSpark, Decodage Spéculatif & Gouvernance d'État Persistant

## 1. Origine Technologique : DSpark & DeepSpec dans mLoop
L'évolution de l'architecture mLoop s'inspire des avancées du cadre de décodage spéculatif **DSpark** (développé par DeepSeek) et du cadre d'ingénierie des agents persistants (*Always-On Persistent State Systems*). 

Dans un environnement agentique, l'utilisation aveugle des modèles de langage à fort pouvoir de raisonnement (ex: Claude Opus, OpenAI o1) pour chaque étape intermédiaire crée un gaspillage massif de budget cognitif et augmente la latence. mLoop résout ce défi en introduisant des mécanismes d'exécution asymétrique et de gouvernance temporelle.

---

## 2. Le Pont de Speculative Drafting (Confidence Gate)
Inspiré par le mécanisme *Confidence-Scheduled Verification* de DeepSpec, le **Confidence Gate** est un module de filtrage déterministe et ultralégère placé en amont des modèles lourds.

* **Principe** : Avant d'invoquer un modèle de raisonnement lourd (ex: le Sentinel), le brouillon de spécification est soumis à une évaluation syntaxique locale rapide (< 10 ms).
* **Métrique** : Un score de confiance sur 100 est attribué en vérifiant la présence et la conformité du Frontmatter YAML, des blocs de tests Gherkin (BDD), et l'absence de termes ambigus.
* **Résultat** : En cas de score insuffisant (< 70), le brouillon est rejeté immédiatement avec un rapport d'erreurs d'auto-correction pour l'agent local, épargnant l'appel au modèle principal.

---

## 3. Le Démon de Préchargement d'Engrammes (RAM Cache)
Pour éliminer la latence d'accès au disque lors des requêtes au graphe sémantique, mLoop intègre un système de préchargement asynchrone d'engrammes en mémoire RAM.

* **Fonctionnement** : Lorsqu'un récit passe à l'état actif, le serveur MCP (`mcp_loop_mem`) précharge en mémoire vive les clusters sémantiques 1-hop de Graphify et les observations historiques de SQLite.
* **Bénéfice** : Les lectures de mémoire par l'agent s'effectuent à latence quasi-nulle (RAM Hit), annulant les temps de recherche sur disque pendant les boucles de réflexion intensive.
* **Éviction** : Un outil de purge explicite libère la mémoire vive dès qu'un récit est validé ou complété.

---

## 4. La Suite d'Évaluation AOEP-v0 (Always-On Evaluation Protocol)
Les benchmarks IA classiques mesurent l'intelligence à un instant T, mais échouent à évaluer la gouvernance dans le temps. mLoop embarque la suite d'évaluation **AOEP-v0** basée sur trois piliers :

1. **Score d'Obligation (Obligation Pass)** : Valide le strict respect des limites d'écriture définies par le *Story Constraint Contract* (SCC) et le composant `Story Guard`.
2. **Score d'Invariant Négatif (Negative Invariant Pass)** : Vérifie la "cécité sémantique" post-révocation — garantissant qu'une information supprimée ne peut plus influencer les décisions futures de l'agent.
3. **Score de Résilience Post-Crash** : Vérifie la capacité de l'état du moteur (`LoopState`) à se restaurer de manière 100 % idempotente après une interruption inopinée.

---

## 5. L'Infrastructure de Désapprentissage Agentique (Agentic Unlearning)
Le désapprentissage agentique est la capacité du harnais à purger une connaissance obsolète ou erronée sans contaminer le reste du réseau sémantique (*Deletion Propagation*).

* **Propagation en Cascade** : Lorsqu'un concept est révoqué, l'outil supprime le nœud et ses arêtes 1-hop dans `knowledge_graph.json`, désactive automatiquement les règles d'invariants dérivées dans `rho_rules.yaml` et vide le cache RAM associé.
* **Traçabilité par Tombstones** : Chaque opération de désapprentissage enregistre une "Tombstone" (pierre tombale) dans le journal d'audit de la session, garantissant la réversibilité et l'auditabilité des suppressions.
