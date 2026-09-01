---
id: REC-XXX-PRO
jira_key: PROJECT-XXX
epic_key: EPIC-XXX
status: IN_ANALYZE
invest_score: 0/6
type: feature
layer: fullstack
---
# [TITRE_DU_RECIT] - Analyse Haute Fidélité

## 📝 Description
**En tant qu'** [Persona],  
**je veux** [Action précise],  
**afin de** [Valeur métier mesurable].

## 🌐 Contexte & Flux
[Décrire la place de ce récit dans le processus global. Référencer le workflow métier ou le diagramme de séquence si applicable.]

---

## 💾 Contrat de Données (Input)
> **Note mLoop** : Définit les sources de vérité nécessaires pour afficher cet écran.

| Entité Dataverse | Champs requis | Rôle / Usage |
| :--- | :--- | :--- |
| `boire_reception` | `status`, `name`, `total_qty` | Entête et état global |
| `boire_buggy` | `id`, `code`, `is_validated` | Liste de sélection |

---

## 🎮 Liste Call to Actions
> **Note mLoop** : Zéro CTA orphelin. Se référer au `standards/INTERACTION_MANIFESTO.md`.

| Élément UI | Trigger | Action & Destination | Feedback (État Final) | Permission / Rôle |
| :--- | :--- | :--- | :--- | :--- |
| **Bouton [Action]** | Clic | Appel `POST /api/...` | Spinner -> Toast Succès | `Operator` |
| **Lien [Détail]** | Clic | Nav vers `Screen_Detail` | Animation Slide-in | `Tous` |
| **Case [Option]** | Change | Mise à jour état local | Indication visuelle | `Supervisor` |

---

## ✅ Critères d'acceptation

### Interface et UX (Maquettes Figma)
* **[États de l'écran]** : Description des états (Initial, Chargement, Vide, Erreur).
* **[Feedback Visuel]** : Comportement des indicateurs (Taxonomie des erreurs : Bloquant, Avertissement, Info).

### Logique et Validations Métier
1. **[Règle X]** : Détail du calcul ou de la contrainte.
2. **[Exception Y]** : Comportement en cas de donnée invalide.

---

## 📏 Definition of Ready (mLoop DoR)
> **Auto-audit obligatoire avant passage en READY_FOR_GROOMING**

- [ ] **Données** : Les entités et champs sources sont identifiés.
- [ ] **Interactions** : Le tableau D-A-F-E est complet (Action + Feedback).
- [ ] **Permissions** : Les rôles requis pour chaque action critique sont définis.
- [ ] **Gherkin** : Les 4 piliers de test sont couverts (Nominal, Exception, Technique, UX).
- [ ] **Liaison** : Toutes les règles `RM-XXX` citées sont liées à un scénario ou un critère.
- [ ] **Audit** : Commande `python src/swarm.py wikifix` exécutée avec succès.

---

## 🧪 Scénarios de test (Gherkin 4 Piliers)
> **Note mLoop** : Se référer au `standards/GHERKIN_GUIDELINES.md`.

```gherkin
# language: fr
Fonctionnalité: [Nom] PRO (US-XXX)

  # PILIER 1 : CHEMIN NOMINAL (Happy Path)
  Scénario: [NOM] - Succès de l'action principale
    Étant donné [Contexte idéal]
    Quand [Action déclenchée]
    Alors [Résultat persistant et visuel attendu]

  # PILIER 2 : EXCEPTIONS MÉTIER (Business Rules)
  Scénario: [NOM] - Rejet pour [Règle RM-XXX]
    Étant donné [Condition d'échec métier]
    Quand [Action déclenchée]
    Alors [Rejet typé et message d'erreur contextualisé]

  # PILIER 3 : CAS LIMITES TECHNIQUES (Resilience)
  Scénario: [NOM] - Gestion de l'Idempotence / Outbox
    Étant donné [Condition technique instable ou doublon]
    Quand [Action déclenchée]
    Alors [Maintien de la cohérence système]

  # PILIER 4 : COMPORTEMENT UX & NAVIGATION
  Scénario: [NOM] - Feedback UI et Transition
    Étant donné [État spécifique de l'interface]
    Quand [Action utilisateur]
    Alors [Indicateur visuel correct et redirection fluide]
```
