# ADR-0306 : Protocole Universel d'Angles Morts, Analyse Comparative et Spikes Techniques

## 🎯 Statut
**Accepté** (Gouvernance Écosystème mLoop - 2026-07-28)

---

## CONTEXTE & PROBLEMATIQUE
Lorsqu'un agent d'analyse ou d'architecture (`plan`, `orchestrator`) prend en charge une initiative, une migration de framework, une intégration tierce ou une décision d'architecture, l'exécution aveugle des spécifications ou la simple réponse directe à la question posée comporte un risque majeur : **omettre des blocages techniques cachés (showstoppers)** qui n'apparaissent qu'en phase avancée de développement ou de déploiement en production.

Pour maximiser la valeur ajoutée agentique, les agents mLoop doivent adopter une posture **proactive, rigoureuse et comparative** en inspectant la codebase et la documentation avant d'acter toute décision.

---

## DECISION

Tout agent mLoop engagé dans une phase d'analyse ou d'architecture **doit impérativement appliquer le Protocole d'Analyse Proactive & Comparative** articulé autour de deux volets obligatoires :

### 1. Audit Proactif des 4 Vecteurs d'Angles Morts Universels
L'agent scrute la codebase du projet et la documentation de référence selon 4 axes agnostiques à la technologie :

* **Vecteur 1 : Matrice de Compatibilité Runtimes & Frameworks**
  * Inadéquation entre les exigences des dépendances et les cibles du projet (versions de SDK, compilateur, OS, cibles de build).
* **Vecteur 2 : Dépendances Transitives & Conflits "Diamants"**
  * Librairies tierces imbriquées ou partagées entrant en collision de versions avec les dépendances existantes de la codebase.
* **Vecteur 3 : Séquencement du Cycle de Vie & Race Conditions**
  * Incompatibilités dans l'ordre d'initialisation (initialisation synchrone vs callbacks asynchrones, événements de bootstrapping, interception de sessions).
* **Vecteur 4 : Contraintes d'Assemblage Debug vs Production**
  * Divergences de comportement entre l'environnement de développement local (Debug) et l'environnement de production (Release/Optimisé/Bundlé, tree-shaking, minification, stripping, NativeAOT).

---

### 2. Dimension d'Analyse Comparative & Demande Active de Baseline

* **Recherche de Divergences Inter-Codebases (Multi-App / Multi-Modules)** :
  * Si le projet comporte plusieurs applications ou modules parallèles (ex: applications sœurs d'un même portefeuille), l'agent compare systématiquement l'implémentation et les versions sur chaque codebase.
* **Réflexe de Demande Active de Base Comparative** :
  * Si l'agent constate l'absence d'un point de comparaison pour évaluer l'impact d'une règle ou d'une dépendance, il interpelle proactivement l'utilisateur : 
    > *"Existe-t-il une application de référence, une codebase comparative ou une version legacy pour valider ce comportement ?"*

---

### 3. La Trinité d'Artefacts de Gouvernance Générés

Dès qu'un risque critique, une incompatibilité ou une divergence majeure est identifié par le protocole, l'agent **doit immédiatement générer les 3 artefacts suivants** :

1. 🔴 **Question Bloquante (`OQ-XXX`)** :
   * Consignée dans `docs/04-transverse/00-questions-ouvertes.md` pour formaliser l'impasse technique ou décisionnelle.
2. ⚡ **Spike Technique (`US-SPIKE-XXX.md`)** :
   * User Story de validation technique rédigée sous blueprint avec les 4 piliers Gherkin (incluant obligatoirement un scénario de test en build Release/Production).
   * Positionnée au statut `OPEN` et inscrite en **Priorité #1 dans `sprint_backlog.md`**. Aucune Story fonctionnelle ne doit démarrer avant la validation du Spike.
3. 📝 **Mémo Technique Destiné aux Parties Prenantes** :
   * Synthèse claire, argumentée et prête à transmettre aux équipes de développement, aux architectes ou aux fournisseurs externes pour débloquer l'arbitrage.

---

## CONSEQUENCES & CONFORMITE

* **Garantie Anti-Surprise** : Les risques techniques sont neutralisés au jour 0 de l'analyse, éliminant les réécritures tardives.
* **Auto-Audit** : Tout récit ou plan d'analyse validé sans vérification des 4 vecteurs et de la dimension comparative sera considéré comme incomplet par la gouvernance `wikifix` et `sentinel`.
