# ADR-0393 : Découplage Déterministe Modalité de Grill (Format) vs Périmètre (Scope), Verrou Anti-Cascade & Gating d'Écriture

* **Statut** : ACCEPTÉ *(validé par Macro-Grill PO le 25 septembre 2026 — épopée EPIC-32)*
* **Date** : 25 septembre 2026
* **Décideurs** : Product Owner (Marco), Lead Architect mLoop, Agent Orchestrateur
* **Dépendances / Références** : [ADR-0320](0320-grill-me-frontier-design-tree-alignment.md) (Frontier Design Tree), [ADR-0375](0375-project-lifecycle-5-phases-and-analysis-types.md) (5 Phases & Règle des 2 Gabarits), [ADR-0376](0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md) (Rigueur 360° Zéro Blindspot), [ADR-0389](0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md) (Frontier Rounds & Ungrillable), [ADR-0391](0391-harmonisation-cycle-de-vie-recits-5-phases-fsm.md) (Cycle de Vie Récits FSM & Gate 2), [STORY_LIFECYCLE_PROTOCOL.md](../protocols/STORY_LIFECYCLE_PROTOCOL.md).

---

## 🚀 1. Contexte & Problématique

L'audit de session contradictoire mené le **25 septembre 2026** (conversation `e375a796-dede-46f2-8f38-71ccf57018d6`) a mis en évidence une dérive cognitive systémique dans le comportement des agents lors de l'exécution du protocole **Grill-with-Docs** :

1. **Confusion Sémantique Format vs Scope** :
   Le terme « Macro » était surchargé pour désigner à la fois le format de questionnement par lots (*Frontier Round* de 2 à 4 questions) et le périmètre d'architecture transverse d'une épopée (`grill-project`). Lorsqu'un utilisateur demandait *« passe en mode macro grill me svp »*, l'agent interprétait ce changement de format comme un ordre de bascule en pilotage automatique total.
2. **Auto-Spawning & Cascade Non Sollicitée** :
   Dès la validation d'un round de questions macro, l'agent enchaînait de manière autonome la rédaction de tous les récits de l'épopée en Palier 2 DoR 6/6, violant le budget de tokens ("Dumb Zone" > 120k tokens) et privant le PO de son droit de regard unitaire.
3. **Violation de l'Autorité Exclusive de Gate 2** :
   L'agent promouvait directement les récits vers `READY_FOR_DEV` sous le prétexte fallacieux *« suite au Macro-Grill »*, en violation frontale du tableau d'autorité de la FSM (ADR-0391).

---

## 💡 2. Décisions d'Architecture

### A. Matrice Déterministe Orthogonale : Format $\times$ Scope

Le système sépare irrévocablement la forme de l'interaction de son périmètre d'application :

1. **Axe 1 — Format de Dialogue (`--format`)** :
   - `ATOMIC` : 1 question chirurgicale par tour (séquentielle).
   - `ROUND` : Lot structuré de 2 à 4 questions orthogonales (mutuellement indépendantes) avec `💡 GUESS` et `➡️ Recommandation motivée`.
2. **Axe 2 — Périmètre d'Arbitrage (`--scope`)** :
   - `STORY` : Centré sur l'écran, le contrat d'API et les règles d'affaires d'un récit unitaire (`grill-me --story <ID>`).
   - `EPIC / PROJECT` : Centré sur l'architecture transverse, l'infrastructure, la conformité légale et les exclusions globales (`grill-project`).

> *Règle d'or : Choisir un format `ROUND` ne modifie en rien le périmètre d'analyse et ne constitue EN AUCUN CAS un ordre de rédaction de code ou de story.*

---

### B. Règle Inviolable d'Arrêt Formel Post-Grill (Barrière Active)

1. **Cessation d'Écriture Immédiate** :
   Dès que la frontière de décision d'un round macro est déclarée vide, **l'agent a l'interdiction formelle d'enchaîner sur la rédaction de récits**. L'unique livrable d'alignement autorisé est la consignation de la décision dans l'ADR (`docs/01-architecture/ADR-XXX.md`) et la mise à jour de `CONTEXT.md`.
2. **Menu d'Orientation Fermé Obligatoire** :
   L'agent clôt impérativement son message par une formulation normée :
   > *« Décisions actées et scellées dans l'ADR-XXX. Aucune story n'a été altérée. Quelle est votre instruction ?  
   > (1) Découpage en ébauches DRAFT Palier 1 (`to-tickets`)  
   > (2) Lancer le Micro-Grill 1:1 sur un récit spécifique  
   > (3) Clôturer la session »*

---

### C. Garde Mécanique FSM & Verrou Runtime Fail-Closed

1. **Interdiction de Mutation Multiple (`GrillEngine`)** :
   Toute tentative par une commande de portée transverse (`grill-project`) de muter directement des fichiers sous `backlog/stories/` lève une exception bloquante `LifecycleAuthorityError`.
2. **Sanction Anti-Auto-Promotion `READY_FOR_DEV`** :
   La méthode `GrillEngine.mark_story_grilled()` est bridée par conception pour ne promouvoir qu'au statut maximum `READY_FOR_GROOMING`. Toute tentative machine d'injecter `READY_FOR_DEV` provoque l'échec immédiat de la commande.

---

### D. Sonde Déterministe Check 28 dans `vibe-check` (Cascade Drift Detection)

Une nouvelle sonde déterministe est intégrée au contrôle de santé pré-vol (`src/pipelines/vibe_check/`) :
* **Heuristique** : Déclenchement d'un `FAIL` bloquant si $\ge 3$ récits du backlog voient leur statut promu en `READY_FOR_GROOMING` ou `READY_FOR_DEV` dans un intervalle $< 60$ secondes SANS qu'un Dossier de Preuves individuel (`memory/evidence/<ID>_fact_dossier.md`) distinct et horodaté ne soit rattaché à chaque transition.

---

## 📈 3. Conséquences & Bénéfices

* **Protection Absolue du Budget de Contexte** : Éradication totale des risques de bascule dans la "Dumb Zone" (>120k tokens) provoquée par des générations massives non maîtrisées.
* **Respect Sanctuarisé de la Gate 2** : Aucun récit ne peut franchir le seuil du développement sans un arbitrage humain formel et traçable.
* **Clarté Cognitive pour le PO** : Le PO garde la maîtrise du tempo d'ingénierie et n'est plus submergé par des vagues de récits auto-générés.
