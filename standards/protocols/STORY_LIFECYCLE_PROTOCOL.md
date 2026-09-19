# Protocole de Gestion du Cycle de Vie des Récits (Story Lifecycle)

**Statut** : Actif — Non Négociable (ADR-0375)  
**Domaine** : Machine à états des récits, autorité de transition, cycle de maturation Palier 1 ➔ Palier 2  

---

## 1. Règle d'Or : Séparation des Responsabilités & Hiérarchie d'Autorité

Le cycle de vie d'un récit est régi par une hiérarchie stricte d'autorité pour garantir la conformité métier et architecturale.

| Statut | Autorité | Gabarit Associé | Description |
| :--- | :--- | :---: | :--- |
| `DRAFT` | **IA / Cadrage** | `story_draft_template.md` | Ébauche initiale issue d'un T-Shirt Size, SOW ou découpage de spécification (`grill_me: PENDING`, `invest_score: 0/6`). |
| `IN_ANALYZE` | **IA / Humain** | `story_draft_template.md` ➔ `story_template.md` | Session contradictoire Grill-Me 1:1 active sur le récit (mono-récit strict par projet). |
| `IN_REVIEW` | **IA / Humain** | `story_template.md` | Retravail / Révision d'un récit existant suite à de nouvelles informations. Anti-tampering suspendu. |
| `READY_FOR_GROOMING` | **IA** | `story_template.md` | État maximal atteignable par l'IA. Certifie que le récit respecte le gabarit, les 4 piliers Gherkin, le DoR 6/6, et est prêt pour revue. |
| `READY_FOR_DEV` | **Humain uniquement** | `story_template.md` | **Interdiction formelle à l'IA.** État certifiant que le récit est arbitré, complet, et prêt pour l'implémentation physique. |

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

---

## 3. Protocole de Révision Post-Validation (`IN_REVIEW`)

Lors de l'arrivée de nouvelles informations critiques avant le démarrage du développement (`not IN_DEV`) :
1. **Rétrogradation** : Le récit passe de `READY_FOR_DEV` ou `READY_FOR_GROOMING` vers `IN_REVIEW`.
2. **Édition Libre** : L'anti-tampering est suspendu pour permettre la mise à jour des critères et des 4 Piliers Gherkin.
3. **Re-Validation** :
   - Par l'IA : passage en `READY_FOR_GROOMING` après nouvel audit Sentinel (`python src/swarm.py rubber-duck`).
   - Par l'Humain : passage direct en `READY_FOR_DEV` après validation des modifications (nouveau hash SHA-256 estampillé automatiquement).

---

## 4. Sanction de non-conformité

Toute tentative par l'IA de basculer un récit en `READY_FOR_DEV` sans validation humaine explicite est une **faute grave** et constitue une violation du contrat de délégation.
