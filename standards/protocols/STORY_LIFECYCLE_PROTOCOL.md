# Protocole de Gestion du Cycle de Vie des Récits (Story Lifecycle)

**Statut** : Actif — Non Négociable (ADR-0375, ADR-0391)  
**Domaine** : Machine à états des récits, autorité de transition, cycle de maturation Palier 1 ➔ Palier 2, chaînage 5 phases  
**Dernière mise à jour** : 2026-09-25 (Alignement 5 phases, auto-clôture Gate 5, immuabilité DONE — ADR-0391)  

---

## 1. Règle d'Or : Séparation des Responsabilités & Hiérarchie d'Autorité

Le cycle de vie d'un récit est régi par une hiérarchie stricte d'autorité et une séquence inviolable en 5 phases pour garantir la conformité métier et architecturale.

### 1.1 Machine à États Canonique (5 Phases Déterministes)

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

### 1.2 Tableau des Statuts & Autorités

| Statut | Phase | Autorité | Gabarit Associé | Description |
| :--- | :---: | :--- | :---: | :--- |
| `DRAFT` / `OPEN` | **1 : INGEST** | **IA / Cadrage** | `story_draft_template.md` | Ébauche initiale issue d'un T-Shirt Size, SOW ou découpage (`grill_me: PENDING`, `invest_score: 0/6`). |
| `IN_ANALYZE` | **2 : PLAN** | **IA / Humain** | `story_draft_template.md` ➔ `story_template.md` | Session contradictoire Grill-Me 1:1 active sur le récit (mono-récit strict par projet). |
| `READY_FOR_GROOMING` | **2 : PLAN** | **IA** | `story_template.md` | État maximal atteignable par l'IA. Certifie les 4 piliers Gherkin, le DoR 6/6, et l'audit Sentinel PASS. |
| `READY_FOR_DEV` | **2 : PLAN** | **Humain uniquement** | `story_template.md` | **Interdiction formelle à l'IA.** État certifiant que le récit est arbitré, complet, et prêt pour l'implémentation physique. |
| `IN_DEV` | **3 : BUILD** | **IA / Humain** | — | L'implémentation physique est en cours. Les modifications de code sont actives sous `src/`. |
| `READY_FOR_QA` | **4 : VALIDATE** | **IA** | — | Code complet et tests unitaires verts. Récit prêt pour la qualification globale du sprint (`validate-sprint`). |
| `QA_CERTIFIED` | **4 : VALIDATE** | **IA / QA** | — | Suite de tests d'intégration, linters et audits passés avec 100% de succès (Gate 4 approuvée). |
| `READY_TO_SHIP` | **5 : SHIP** | **IA** | — | Livrables pré-vol vérifiés, documentation consolidée, prêt pour synchronisation et publication. |
| `DONE` | **5 : SHIP** | **IA / Système** | — | **Clôture définitive immuable.** Gate 5 auto-validée sans intervention humaine dès lors que tout est vert. |
| `DONE_TESTED` | *Legacy* | **IA** | — | *Passerelle historique tolérée (équivalent fonctionnel READY_FOR_QA post-tests unitaires).* |
| `SHIPPED` | *Legacy* | **IA / Humain** | — | *Passerelle historique tolérée (équivalent fonctionnel DONE synchronisé).* |
| `IN_REVIEW` | *Transverse* | **IA / Humain** | `story_template.md` | Retravail / Révision d'un récit pré-implémentation suite à de nouveaux arbitrages. |

---

## 2. Déclencheurs de Transition & Portes de Gouvernance

### Phase 1 ➔ Phase 2 : Ingestion & Cadrage
* **`DRAFT` vers `IN_ANALYZE`** : Déclenché lors de la prise en charge pour le sprint courant via `python src/swarm.py grill-me --story <STORY_ID>`.
* **Gate 1** : Ingestion documentaire et cadrage validés (`requires_human: False`).

### Phase 2 : Maturation & Spécification Fine
* **`IN_ANALYZE` vers `READY_FOR_GROOMING` (IA)** :
  1. Gabarit haute-fidélité [`story_template.md`](../blueprints/story_template.md) complété.
  2. Scénarios Gherkin conformes aux 4 piliers (Nominal, Exception, Résilience, UX).
  3. Preuves documentaires (`EvidencePack`) scellées et à jour.
  4. INVEST Score 6/6 certifié par audit Sentinel Rubber Duck (`Trust >= 90%`, 0 bloquant).
* **`READY_FOR_GROOMING` vers `READY_FOR_DEV` (Humain)** :
  - **Gate 2 (DoR)** : Déclenché par arbitrage humain explicite uniquement. Interdiction formelle à l'IA de s'auto-promouvoir en `READY_FOR_DEV`.

### Phase 3 : Développement Physique
* **`READY_FOR_DEV` vers `IN_DEV`** : Déclenché au premier commit de code de la story.

### Phase 4 : Qualification & Recette QA
* **`IN_DEV` vers `READY_FOR_QA`** : Déclenché dès que l'implémentation physique est achevée et que les tests unitaires locaux du composant sont au vert.
* **`READY_FOR_QA` vers `QA_CERTIFIED`** : Déclenché lorsque la suite complète `validate-sprint` et les tests d'intégration passent à 100% (Gate 3 & Gate 4 approuvées).
* **Rétrogradation directe `READY_FOR_QA` vers `IN_DEV`** : En cas d'échec de test ou d'anomalie de qualification, le récit repasse directement en `IN_DEV` pour correction sans nécessiter de réouverture Sentinel.

### Phase 5 : Distribution & Clôture Définitive
* **`QA_CERTIFIED` vers `READY_TO_SHIP`** : Préparation des manifestes, synchronisation documentaire.
* **`READY_TO_SHIP` vers `DONE` (Auto-Clôture Gate 5 & Auto-Commit Git)** :
  - Dès lors que 100% des tests pré-vol, suites pytest, linters AST et contrôles de sécurité sont verts (0 FAIL), la Gate 5 s'auto-clôture de manière 100% autonome (`requires_human: False`, ADR-0391).
  - Le code au statut `DONE` est **automatiquement commité vers Git, poussé/synchronisé et archivé par l'agent ou le pipeline**. Aucune approbation humaine n'est requise si tous les feux sont au vert. L'humain n'intervient que par exception.

---

## 3. Règle d'Or d'Immuabilité Absolue des Récits `DONE`

1. **Inviolabilité Historique** : Un récit scellé à `DONE` (ou `SHIPPED`) constitue un incrément logiciel archivé et inviolable.
2. **Interdiction de Réouverture** : Il est formellement interdit de rétrograder, rouvrir ou rééditer un récit `DONE`.
3. **Traitement des Anomalies Post-Livraison** : Tout défaut, régression ou besoin correctif découvert ultérieurement doit obligatoirement faire l'objet d'un **nouveau ticket de type `BUG` ou `HOTFIX`**, disposant de sa propre traçabilité, de ses propres critères INVEST et de son propre cycle de vie.

---

## 4. Protocole de Révision Pré-Implémentation (`IN_REVIEW`)

Lors de l'arrivée de nouvelles informations critiques **avant** le démarrage du développement physique :
1. **Rétrogradation** : Le récit passe de `READY_FOR_DEV` ou `READY_FOR_GROOMING` vers `IN_REVIEW`.
2. **Édition Libre** : L'anti-tampering est suspendu pour permettre la mise à jour des critères et scénarios Gherkin.
3. **Re-Validation** :
   - Par l'IA : passage en `READY_FOR_GROOMING` après nouvel audit Sentinel (`python src/swarm.py rubber-duck`).
   - Par l'Humain : passage en `READY_FOR_DEV` après validation des modifications.

---

## 5. Sanction de non-conformité

- Toute tentative par l'IA de basculer un récit en `READY_FOR_DEV` sans validation humaine explicite constitue une **violation critique du contrat d'autonomie**.
- Toute tentative de réouverture silencieuse d'un récit `DONE` sans création d'un ticket `BUG`/`HOTFIX` est rejetée par la FSM (`StateTransitionError`).
