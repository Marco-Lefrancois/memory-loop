# ADR-0391 : Harmonisation Déterministe du Cycle de Vie des Récits (5 Phases, Machine à États SSOT, Éradication du Hardcoding & Auto-Clôture Gate 5)

* **Statut** : ACCEPTÉ *(validé par Macro-Grill PO le 25 septembre 2026 — épopée EPIC-31)*
* **Date** : 25 septembre 2026
* **Décideurs** : Product Owner (Marco), Lead Architect mLoop, Agent Orchestrateur
* **Dépendances / Références** : [ADR-0202](0202-modularite-fichiers-source-et-documentation.md) (Modularité ≤ 300 L), [ADR-0319](0319-matrice-contrats-api-reseau-et-clause-exemption-oq.md) (Exemption OQ-XXX), [ADR-0375](0375-orchestration-canonique-5-phases-cycle-de-vie.md) (5 Phases Canoniques), [ADR-0376](0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md) (Rigueur Zéro Blindspot), [ADR-0385](0385-protocole-falsification-frontieres-architecture-immunite-cognitive.md) (Échelle de Preuve), [ADR-0386](0386-standard-recits-palier-2-dor-6-sur-6-sentinel.md) (DoR 6/6 Sentinel), [ADR-0390](0390-fact-search-indexation-arbres-niches-docs-domaine-couche.md) (Fact-Search FTS5 SSOT), [STORY_LIFECYCLE_PROTOCOL.md](../protocols/STORY_LIFECYCLE_PROTOCOL.md).

---

## 🚀 1. Contexte & Problématique

L'audit contradictoire d'architecture mené le **25 septembre 2026** sur le moteur de machine à états (`src/pipelines/state_machine.py`) et les composants périphériques mLoop a révélé plusieurs incohérences structurelles critiques :

1. **Désalignement avec les 5 Phases Canoniques (ADR-0375)** :
   La machine à états autorisait la transition directe `IN_DEV ➔ DONE_TESTED`, court-circuitant ainsi formellement la **Phase 4 (VALIDATE & QA)**. Le statut d'achèvement de développement était assimilé prématurément à une qualification globale du sprint.
2. **Fuites Métier Hardcodées & Duplication de Paramètres** :
   Le fichier `src/pipelines/state_machine.py` hébergeait des chaînes en dur issues d'anciens verticaux clients (`["FOOD", "COMMERCE", "SANTE"]`) pour localiser les revues contradictoires, ainsi qu'une double définition contradictoire de `DEFAULT_TTL_CYCLES` (3 en ligne 22 vs 5 en ligne 174).
3. **Fluff Opérationnel sur la Gate 5** :
   La Gate 5 (Phase 5 : SHIP & SYNC) imposait une validation humaine manuelle (`requires_human: True`), obligeant l'humain à une validation passive alors même que 100% des tests pré-vol, linters et audits de sécurité étaient déjà automatisés et verts.
4. **Fragmentation des Consommateurs de Statuts** :
   Les analyseurs de tables de backlog (`_sync_backlog_parser.py`), les filtres d'intégrité INVEST (`wikifix_core.py`), les hooks de nettoyage d'artefacts (`scratch_prune.py`) et le Dashboard (`dashboard/routers/backlog.py`) reposaient sur des vocabulaires incomplets ou des expressions régulières sensibles au masquage par préfixe.
5. **Règle d'Immuabilité Floue** :
   Certains protocoles laissaient entendre qu'un récit au statut terminal pouvait être rétrogradé et réédité a posteriori, compromettant l'inviolabilité historique des incréments de sprint.

---

## 💡 2. Décisions d'Architecture

### A. Chaîne Canonique Déterministe des 5 Phases (`StoryStatus`)

Le modèle `StoryStatus` (`src/state/_state_core.py`) et le graphe `ALLOWED_TRANSITIONS` (`src/pipelines/state_machine.py`) sont formellement alignés sur le cycle séquentiel en 5 phases :

```
[Phase 1 : INGEST]     DRAFT / OPEN
                              │
[Phase 2 : PLAN]       IN_ANALYZE (Mono-récit strict)
                              │
                       READY_FOR_GROOMING (IA DoR 6/6)
                              │
                       READY_FOR_DEV (Validation Humaine Exclusive)
                              │
[Phase 3 : BUILD]      IN_DEV
                              │
[Phase 4 : VALIDATE]   READY_FOR_QA
                              │ ╲ (Échec tests ➔ rétrogradation directe)
                              │  └──────────────┐
                              ▼                 ▼
                       QA_CERTIFIED          IN_DEV
                              │
[Phase 5 : SHIP]       READY_TO_SHIP
                              │
                       DONE (Clôture Définitive Immuable)
```

* **Passerelles de rétrocompatibilité sanctuarisées** :
  - `DONE_TESTED` demeure valide et toléré comme alias historique de transition.
  - `SHIPPED` demeure reconnu comme état synchronisé de distribution.
  - La méthode tolérante `StoryStatus.from_raw(value)` résout les libellés avec emojis (`🟢 READY_FOR_DEV`), tirets nus et minuscules sans lever d'exception indue.

### B. Règle d'Or d'Immuabilité Absolue des Récits `DONE`

* Tout récit ayant atteint le statut `DONE` ou `SHIPPED` est un **incrément logiciel inviolable et scellé**.
* **Interdiction stricte** : Aucun correctif, ré-ouverture ou rétrogradation d'un récit `DONE` n'est autorisé.
* **Procédure de non-conformité ultérieure** : Toute régression, anomalie ou évolution découverte post-livraison donne lieu à la création d'un nouveau ticket dédié (`BUG`, `HOTFIX` ou nouvelle `Story`), tracé et qualifié dans son propre cycle de vie.

### C. Auto-Clôture Autonome de la Gate 5 & Auto-Commit Git (`Zero Fluff Delivery`)

* La définition de Gate 5 dans `src/core/lifecycle/_lc_models.py` est reconfigurée à **`requires_human: False`**.
* **Auto-Commit Git & Archivage Immédiat** : Tout code au statut `DONE` doit être commité vers Git et archivé automatiquement par l'agent ou le pipeline dès validation des critères.
* **Zéro Approbation Humaine Requise** : Dès lors que 100% des tests pré-vol, suites pytest (0 FAIL), linters AST et audits de cohérence sont au vert, l'agent procède directement au commit Git, au push distant (ou création de PR selon la cible) et au scellement de la Gate 5 sans solliciter d'approbation humaine passive. L'intervention humaine s'effectue par exception uniquement en cas d'échec.

### D. Assainissement Anti-Hardcoding & Topologie SSOT

* **Éradication des chaînes de verticaux** : Suppression intégrale de `"FOOD"`, `"COMMERCE"`, `"SANTE"` au profit de la résolution dynamique `_resolve_review_file(story_file)` : sous-dossier miroir relatif sous `reviews/`, repli à la racine de `reviews/`, puis recherche récursive de secours bornée.
* **SSOT TTL Paramétrable** : Définition unique de `DEFAULT_TTL_CYCLES = int(os.getenv("MLOOP_DEFAULT_TTL_CYCLES", "5"))`.
* **Typage par Énumérateurs** : Remplacement des tuples de chaînes littérales par des comparaisons s'appuyant directement sur `StoryStatus`.

### E. Harmonisation Multi-Couches des Consommateurs

* **Parser de Backlog (`_sync_backlog_parser.py`)** : Compilation de `STATUS_VOCAB_RE` ordonnée par longueur dégressive pour immuniser l'extraction contre les faux positifs de préfixes (`READY_FOR_GROOMING` avant `READY_FOR_DEV`, `READY_FOR_QA` avant `IN_QA`, etc.).
* **WikiFix (`wikifix_core.py`)** : Intégration de `READY_FOR_QA`, `QA_CERTIFIED`, `READY_TO_SHIP` dans le filtre `_tolerated` et factorisation des gardes d'intégrité sous un bloc concis respectant le plafond modulaire ≤ 300 lignes (`RULE-AST-01`).
* **Nettoyage Scratch (`scratch_prune.py`)** : Inclusion de `DONE`, `QA_CERTIFIED` et `READY_TO_SHIP` dans les statuts terminaux déclenchant la purge immédiate des répertoires de travail temporaires.
* **Dashboard (`dashboard/routers/backlog.py`)** : Ordonnancement strict de `STATUS_ORDER` selon la séquence naturelle des 5 phases.

---

## 📈 3. Conséquences & Bénéfices

* **Cohérence Systémique Totale** : Le cycle de vie des récits reflète fidèlement la réalité industrielle de l'ingénierie logicielle (spécification ➔ dev ➔ validation QA ➔ release).
* **Zéro Fluff & Vitesse d'Exécution** : Les gates d'intégration se débloquent sans friction humaine dès lors que l'intégrité déterministe est mathématiquement prouvée par les tests.
* **Souveraineté du Framework** : mLoop redevient un moteur universel, agnostique de tout domaine métier particulier ou historique client.
* **Robustesse de Synchronisation** : Zéro risque de corruption ou troncature dans les tables de sprint backlog, le rapport WikiFix ou le Dashboard.
