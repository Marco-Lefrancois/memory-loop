# Protocole de Gestion du Cycle de Vie des Récits (Story Lifecycle)

## Statut : Actif — Non Négociable

---

## 1. Règle d'Or : Séparation des Responsabilités

Le passage du statut d'un récit est soumis à une hiérarchie stricte d'autorité pour garantir la conformité métier et architecturale.

| Statut | Autorité | Description |
| :--- | :--- | :--- |
| `IN_ANALYZE` | **IA / Humain** | Cadrage initial d'un nouveau récit (mono-récit strict par projet). |
| `IN_REVIEW` | **IA / Humain** | Retravail / Révision d'un récit existant suite à de nouvelles informations. Anti-tampering suspendu, multi-récits autorisé. |
| `READY_FOR_GROOMING` | **IA** | État maximal atteignable par l'IA. Certifie que le récit respecte le gabarit, les 4 piliers Gherkin, et est prêt pour revue. |
| `READY_FOR_DEV` | **Humain uniquement** | **Interdiction formelle à l'IA.** État certifiant que le récit est arbitré, complet, et prêt pour l'implémentation physique (transition directe depuis `IN_REVIEW` autorisée). |

---

## 2. Déclencheurs de l'état `READY_FOR_GROOMING` (IA)

L'agent peut basculer un récit en `READY_FOR_GROOMING` uniquement si les conditions suivantes sont validées par le skill `sentinel` :
1.  **Structure** : Respect strict du `story_template.md`.
2.  **Qualité** : Scénarios Gherkin (4 piliers) validés.
3.  **Intégrité** : Aucun lien brisé, aucune OQ non résolue/non documentée, aucun drift par rapport au modèle SSOT.
4.  **Preuves** : `EvidencePack` généré et à jour.

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

Toute tentative par l'IA de basculer un récit en `READY_FOR_DEV` sans validation humaine est une **faute grave** et sera considérée comme une violation du contrat de délégation.
