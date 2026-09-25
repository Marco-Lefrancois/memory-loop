# 🏛️ Épopée — `EPIC-31-FSM-ANTI-HARDCODING-AND-LIFECYCLE-HARMONIZATION` : Refactorisation de la Machine à États des Récits, Éradication du Hardcoding & Alignement Déterministe 5 Phases / 5 Gates

---

> **Référence d'Architecture** : [ADR-0391](../../../../standards/adr-system/0391-harmonisation-cycle-de-vie-recits-5-phases-fsm.md) · [ADR-0375](../../../../standards/adr-system/0375-standard-preuve-epistemique-et-tracabilite-radicale.md) (Traçabilité Radicale) · [ADR-0376](../../../../standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md) (Rigueur 360° Zéro Blindspot) · [ADR-0202](../../../../standards/adr-system/0202-modularite-interne-agents.md) (Modularité ≤ 300L) · [ADR-0386](../../../../standards/adr-system/0386-gouvernance-github-rulesets-pull-requests-et-garde-fous-phase-5-ship.md) (Gouvernance Gate 5)  
> **Composant(s)** : `Core/State` · `Pipelines/FSM` · `Pipelines/Sync` · `Pipelines/WikiFix` · `Core/Lifecycle` · `Dashboard/Backlog` · `Standards/Protocols`  
> **Origine / Déclencheur** : Audit architectural contradictoire du 25/09/2026 mettant en évidence :  
>   1. La contradiction logique `IN_DEV ➔ DONE_TESTED` avant la phase de QA (Phase 4).  
>   2. La présence de hardcoding critique dans `src/pipelines/state_machine.py` (verticaux clients `["FOOD", "COMMERCE", "SANTE"]`, constantes TTL dupliquées et divergentes, chemins en dur hors `ProjectLayout`).  
>   3. L'arbitrage PO validant le flux unifié `IN_DEV ➔ READY_FOR_QA ➔ QA_CERTIFIED ➔ DONE`, l'immuabilité absolue des récits `DONE` (tout correctif ultérieur = nouveau `BUG`/`HOTFIX`), et l'auto-livraison Gate 5 sans confirmation humaine si 100% des feux sont au vert.  
> **Statut** : `DONE` — Implémenté & 100% certifié le 25/09/2026 (5/5 récits achevés, 1669/1669 tests pytest verts, Gate 5 validée)  
> **Décideurs** : PO mLoop (Marco) / Architecte Agentique  

---

## 🎯 1. Contexte & Intention Stratégique

L'écosystème **mLoop** structure son développement en 5 phases canoniques séquentielles (ADR-0375) :
* **Phase 1 : INGEST & EXPLORE** (Amorçage & Ingestion des sources)
* **Phase 2 : PLAN & ANALYSE** (Spécifications, Grill-Me, DoR 6/6, Gate 2)
* **Phase 3 : BUILD** (Développement physique, Tournoi AST, TDD Red-Green, Gate 3)
* **Phase 4 : VALIDATE** (Assurance Qualité, `validate-sprint`, Non-régression, CEL, Gate 4)
* **Phase 5 : SHIP & SYNC** (Release, Push Git, Jira Sync, Indexation FTS5 / Graphify, Gate 5)

Jusqu'alors, le cycle de vie des récits présentait une anomalie sémantique majeure : un récit passait à `DONE_TESTED` dès la fin du dev unitaire (Phase 3), créant une contradiction ("terminé avant d'être validé en QA") et forçant un statut `SHIPPED` ambigu en Phase 5. De plus, l'audit approfondi de `src/pipelines/state_machine.py` a révélé un hardcoding inacceptable pour un framework souverain (verticaux d'un client spécifique en dur, double déclaration conflictuelle de `DEFAULT_TTL_CYCLES = 3` et `5`, arborescence en dur, chaînes magiques textuelles).

L'objectif de cette épopée est d'assainir de fond en comble la machine à états des récits, d'éradiquer tout hardcoding, et d'aligner parfaitement le cycle de vie des stories avec les 5 phases et 5 portes de mLoop.

---

## 🧭 2. Vérité Terrain & Décisions d'Architecture Actées

En application de l'**ADR-0375** (Traçabilité Radicale) et des arbitrages PO du 25/09/2026 :

1. **Nouveau Flux Unifié Déterministe** :
   $$\text{DRAFT} \longrightarrow \text{IN\_ANALYZE} \longrightarrow \text{READY\_FOR\_GROOMING} \overset{\text{Gate 2 (Humain)}}{\longrightarrow} \text{READY\_FOR\_DEV}$$
   $$\text{READY\_FOR\_DEV} \longrightarrow \text{IN\_DEV} \overset{\text{Gate 3 (DoD TDD)}}{\longrightarrow} \text{READY\_FOR\_QA}$$
   $$\text{READY\_FOR\_QA} \overset{\text{validate-sprint}}{\longrightarrow} \overset{\text{Gate 4 (Certif QA)}}{\longrightarrow} \text{QA\_CERTIFIED}$$
   $$\text{QA\_CERTIFIED} \overset{\text{Gate 5 (Auto si vert)}}{\longrightarrow} \text{DONE}$$

2. **Règle d'Immuabilité Absolue** :
   Un récit au statut `DONE` est un incrément clos, inviolable et scellé. On ne modifie jamais un récit clos. Toute anomalie ou besoin ultérieur donne lieu à la création d'un nouveau récit de type `BUG` ou `HOTFIX` dans le backlog du sprint suivant.

3. **Auto-Clôture Gate 5 (Zero-Fluff Delivery)** :
   Une fois les contrôles pré-vol au vert (Pytest 100%, Vibe-Check 0 FAIL, AST 0 violation, Anti-Leak OK, Sync Git/Jira OK), l'humain n'a pas à confirmer la livraison manuellement : Gate 5 est 100% autonome (`requires_human: False`). L'intervention humaine s'effectue par exception uniquement.

4. **Éradication Intégrale du Hardcoding** :
   Suppression des listes en dur de clients, centralisation des constantes TTL dans l'environnement/SSOT, typage systématique via `StoryStatus` et `ProjectLayout`.

---

## 🗂️ 3. Décomposition des Récits (Backlog Slicing)

L'épopée est découpée en 5 récits verticaux indépendants (INVEST) :

| Identifiant | Type | Titre | Scope & Valeur Produite | Statut |
| :--- | :---: | :--- | :--- | :---: |
| **`MLOOP-310-BE`** | Feature | **Unification du Modèle d'États `StoryStatus` & Rétrocompatibilité Tolérante** | Ajoute `READY_FOR_QA`, `QA_CERTIFIED`, `READY_TO_SHIP` dans `StoryStatus`, refactore `_GRILLED_STATUSES` sans chaînes brutes et garantit le parsing tolérant des anciens récits (`DONE_TESTED`, `SHIPPED`). | ✅ `DONE_TESTED` (48 tests) |
| **`MLOOP-311-BE`** | Tech Debt | **Assainissement Anti-Hardcoding de `state_machine.py` (Verticaux, TTL & Arborescence)** | Supprime la fuite client `["FOOD", "COMMERCE", "SANTE"]`, unifie `DEFAULT_TTL_CYCLES`, remplace les chemins en dur par `ProjectLayout` et type les gardes C9 et Sentinel via `StoryStatus`. | ✅ `DONE_TESTED` (62 tests) |
| **`MLOOP-312-BE`** | Feature | **Graphe de Transitions Déterministe & Auto-Clôture Gate 5 sans Validation Humaine** | Met à jour `ALLOWED_TRANSITIONS` pour le cycle des 5 phases, configure `GATE_DEFINITIONS[5]["requires_human"] = False` et autorise la transition automatique vers `DONE` si tout est vert. | ✅ `DONE_TESTED` (65 tests) |
| **`MLOOP-313-BE`** | Enabler | **Harmonisation Multi-Couches des Consommateurs (`_sync_backlog`, `wikifix`, `scratch_prune`, `Dashboard`)** | Met à niveau `STATUS_VOCAB_RE`, intègre les nouveaux statuts dans `wikifix_core.py` (intégrité & regex tolérance), `scratch_prune` et `STATUS_ORDER` du Dashboard. | ✅ `DONE_TESTED` (15 tests) |
| **`MLOOP-314-FULL`** | Feature | **Formalisation Normative ADR-0391, Mise à Jour SSOT & Harnais de Certification E2E** | Rédige l'ADR-0391, met à jour `STORY_LIFECYCLE_PROTOCOL.md` et livre la suite de tests de validation (1669/1669 tests verts). | ✅ `DONE_TESTED` (1669 tests) |

---

## 🛡️ 4. Matrice d'Impact en 7 Couches (ADR-0376)

1. **Blueprints / Standards** : Publication de l'ADR-0390, refonte de `STORY_LIFECYCLE_PROTOCOL.md` et des gabarits de backlog.
2. **Protocoles & FSM** : Nouveaux statuts formels, suppression des doubles définitions, modèle d'états unifié.
3. **Pipelines de Synchronisation** : Maintien de la cohérence de parsing Markdown de tables et frontmatter.
4. **Gatekeeper & Linters** : Adaptation des gardes Sentinel, intégrité SHA-256 et Preuves C9 sans faux positifs.
5. **Dashboard & API** : Ordre des colonnes de restitution ajusté sur la chaîne de valeur à 5 phases.
6. **Backlog & Données** : Règle de responsabilité clarifiée, 91 récits historiques préservés sans migration disruptive.
7. **Harnais de Tests** : 100% de couverture unitaire et d'intégration sur les transitions légales et illégales.
