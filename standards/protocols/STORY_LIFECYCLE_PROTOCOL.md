# Protocole de Gestion du Cycle de Vie des Récits (Story Lifecycle)

**Statut** : Actif — Non Négociable (ADR-0375)  
**Domaine** : Machine à états des récits, autorité de transition, cycle de maturation Palier 1 ➔ Palier 2  
**Dernière mise à jour** : 2026-09-21 (Ajout des statuts IN_DEV, DONE_TESTED, SHIPPED)

---

## 1. Règle d'Or : Séparation des Responsabilités & Hiérarchie d'Autorité

Le cycle de vie d'un récit est régi par une hiérarchie stricte d'autorité pour garantir la conformité métier et architecturale.

### 1.1 Machine à États Complète

```
DRAFT → IN_ANALYZE → READY_FOR_GROOMING → READY_FOR_DEV → IN_DEV → DONE_TESTED → SHIPPED
                              ↑                  ↑             ↑
                              │                  │             │
                         IN_REVIEW ◄─────────────┘             │
                              │                                │
                              └────────────────────────────────┘
                              (révision post-implémentation possible)
```

### 1.2 Tableau des Statuts

| Statut | Autorité | Gabarit Associé | Description |
| :--- | :--- | :---: | :--- |
| `DRAFT` | **IA / Cadrage** | `story_draft_template.md` | Ébauche initiale issue d'un T-Shirt Size, SOW ou découpage de spécification (`grill_me: PENDING`, `invest_score: 0/6`). |
| `IN_ANALYZE` | **IA / Humain** | `story_draft_template.md` ➔ `story_template.md` | Session contradictoire Grill-Me 1:1 active sur le récit (mono-récit strict par projet). |
| `IN_REVIEW` | **IA / Humain** | `story_template.md` | Retravail / Révision d'un récit existant suite à de nouvelles informations. Anti-tampering suspendu. |
| `READY_FOR_GROOMING` | **IA** | `story_template.md` | État maximal atteignable par l'IA. Certifie que le récit respecte le gabarit, les 4 piliers Gherkin, le DoR 6/6, et est prêt pour revue. |
| `READY_FOR_DEV` | **Humain uniquement** | `story_template.md` | **Interdiction formelle à l'IA.** État certifiant que le récit est arbitré, complet, et prêt pour l'implémentation physique. |
| `IN_DEV` | **IA / Humain** | — | L'implémentation physique est en cours. Les modifications de code sont actives. |
| `DONE_TESTED` | **IA** | — | L'implémentation est terminée et tous les tests unitaires/passent. La revue de code est terminée. |
| `SHIPPED` | **IA / Humain** | — | Le récit est livré en production (ou intégré au framework mLoop). Artefacts synchronisés (Git, Jira, NotebookLM). |

---

## 2. Déclencheurs de Transition

### A. De `DRAFT` vers `IN_ANALYZE`
* Déclenché lors de la prise en charge du récit pour le sprint courant.
* Commande associée : `python src/swarm.py grill-me --story <STORY_ID>`.
* L'agent examine les « Zones d'ombre » (Section 5 de `story_draft_template.md`) et engage l'entrevue 1:1.

### B. De `IN_ANALYZE` vers `READY_FOR_GROOMING` (IA)
L'agent bascule le récit vers `READY_FOR_GROOMING` uniquement si les conditions suivantes sont satisfaites et auditées par `sentinel` :
1. **Structure** : Récit converti au format haute-fidélité [`story_template.md`](../blueprints/story_template.md).
2. **Qualité Gherkin** : Scénarios Gherkin conformes aux 4 piliers (Nominal, Exception, Résilience, UX).
3. **Intégrité** : Toutes les questions ouvertes de l'ébauche ont été résolues, aucun lien brisé.
4. **Preuves** : `EvidencePack` sidecar généré et à jour.
5. **INVEST Score** : Score 6/6 audité.

### C. De `READY_FOR_GROOMING` vers `READY_FOR_DEV` (Humain)
* Déclenché par validation humaine explicite uniquement.
* Interdiction formelle à l'IA de basculer ce statut.

### D. De `READY_FOR_DEV` vers `IN_DEV`
* Déclenché automatiquement lors du premier commit de code pour le récit.
* Le développeur (humain ou agent) commence l'implémentation physique.

### E. De `IN_DEV` vers `DONE_TESTED`
* Déclenché lorsque l'implémentation est terminée et que la suite de tests est entièrement verte.
* Critères :
  1. Tous les fichiers du récit sont modifiés/créés.
  2. `python -m pytest tests/` passe à 100% (hors tests e2e pré-existants connus).
  3. `python src/swarm.py guide --sync` retourne "parité OK" si des modifications CLI ont été faites.

### F. De `DONE_TESTED` vers `SHIPPED`
* Déclenché lors de la synchronisation finale (Git push, Jira sync, NotebookLM export).
* Critères :
  1. Code committed et pushed.
  2. Jira synchronisé (si applicable).
  3. EvidencePack à jour.
  4. Story archivée dans le sprint_backlog.md.

---

## 3. Protocole de Révision Post-Validation (`IN_REVIEW`)

### 3.1 Révision avant implémentation (`not IN_DEV`)
Lors de l'arrivée de nouvelles informations critiques avant le démarrage du développement :
1. **Rétrogradation** : Le récit passe de `READY_FOR_DEV` ou `READY_FOR_GROOMING` vers `IN_REVIEW`.
2. **Édition Libre** : L'anti-tampering est suspendu pour permettre la mise à jour des critères et des 4 Piliers Gherkin.
3. **Re-Validation** :
   - Par l'IA : passage en `READY_FOR_GROOMING` après nouvel audit Sentinel (`python src/swarm.py rubber-duck`).
   - Par l'Humain : passage direct en `READY_FOR_DEV` après validation des modifications.

### 3.2 Révision après implémentation (`IN_DEV` ou `DONE_TESTED`)
Lorsqu'un bug critique ou une incohérence est découvert après implémentation :
1. **Rétrogradation** : Le récit passe de `IN_DEV` ou `DONE_TESTED` vers `IN_REVIEW`.
2. **Correction** : Le code est modifié pour résoudre le problème.
3. **Re-Test** : La suite de tests doit repasser à 100%.
4. **Re-Progression** : Le récit repasse par `IN_DEV` ➔ `DONE_TESTED` ➔ `SHIPPED`.

---

## 4. Sanction de non-conformité

Toute tentative par l'IA de basculer un récit en `READY_FOR_DEV` sans validation humaine explicite est une **faute grave** et constitue une violation du contrat de délégation.

---

## 5. Correspondance avec les Épisodes Existantes

| Épisode | Statut Utilisé | Statut Protocole |
|:---|:---|:---|
| EPIC-1 à EPIC-7 | `SHIPPED` | `SHIPPED` ✅ |
| EPIC-8 à EPIC-11 | `DONE_TESTED` | `DONE_TESTED` ✅ |
| EPIC-12 (Phase 4) | `DONE` | → À migrer vers `DONE_TESTED` ou `SHIPPED` |

> **Note de migration** : Les récits `DONE` existants dans le backlog doivent être promus vers `DONE_TESTED` si les tests passent, ou `SHIPPED` si déjà synchronisés.
