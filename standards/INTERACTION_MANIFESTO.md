# Manifeste de l'Interaction mLoop - Standard CTA & Intentions

L'objectif de ce manifeste est d'éliminer les zones d'ombre lors de la transition entre l'analyse fonctionnelle et le développement physique. Un élément d'interface sans intention d'action définie est considéré comme une erreur d'analyse.

## La Règle d'Or : Le Cycle D-A-F-E

Chaque élément interactif (Bouton, Lien, Case à cocher, Sélection de liste, Toggle) doit être documenté selon le cycle **D-A-F-E** :

### 1. [D]isponibilité (Pre-conditions)
*   **Visibilité** : Sous quelles conditions l'élément est-il affiché ?
*   **Activabilité** : Sous quelles conditions l'élément est-il cliquable ? (ex: "Bouton grisé si le formulaire est invalide").

### 2. [A]ction (Intention)
*   **Nature** : Quelle est l'action déclenchée ?
*   **Cible** : Navigation (vers quel écran ?), Appel API (quel endpoint ? quel payload ?), ou Logique Locale (calcul, filtre).

### 3. [F]eedback (Réaction UI)
*   **État Transitoire** : Que voit l'utilisateur pendant l'action ? (ex: Spinner sur le bouton, Overlay de chargement).
*   **État Final (Succès)** : Message de confirmation (Toast, Notification) ou changement visuel immédiat.

### 4. [E]rreur (Résilience)
*   **Gestion des échecs** : Que se passe-t-il si l'action échoue ? (ex: Message d'erreur spécifique, maintien de l'état précédent).

---

## Standard de Nomenclature des CTA

Pour faciliter la lecture, l'analyste doit utiliser des termes d'action normalisés :
*   **Valider/Confirmer** : Soumission définitive de données avec changement d'état.
*   **Enregistrer (Brouillon)** : Persistance locale ou serveur sans changement d'état fonctionnel.
*   **Annuler/Fermer** : Retour à l'état précédent sans persistance.
*   **Sélectionner** : Mise en mémoire d'un choix pour une action ultérieure.

## Exigence mLoop : Zéro "CTA Orphelin"

Lors de la rédaction des critères d'acceptation, l'analyste a l'interdiction de citer un élément UI sans son tableau de contrat associé (voir `story_template.md`).

---

## Modulation par Complexité de Composant (Anti-Remplissage)

Le cycle D-A-F-E et la matrice d'états s'appliquent à la **hauteur de la richesse réelle du composant**, en cohérence avec le Triage Bimodal (`STORY_AUTHORING_FRAMEWORK.md`, Mode FULL vs LIGHT) :

- **Composant riche** (formulaire multi-champs, liste alimentée par API, carte cliquable, wizard multi-étapes) : documenter le cycle D-A-F-E complet et la matrice des 8 États d'Interaction dans leur intégralité.
- **Composant simple** (champ unique + bouton, écran `minimal-spotlight`, action directe sans état intermédiaire) : ne documenter que les **états et étapes du cycle qui portent une décision UX ou métier réelle**. Un état natif générique (survol, pression tactile, contour de focus) sans règle métier spécifique associée est considéré comme du remplissage et doit être omis.

**Interdiction formelle** : décrire un état d'interaction uniquement pour satisfaire un compte de 8 lignes, sans qu'il n'apporte d'information exploitable pour le développeur (ex : « Aucun message d'erreur applicable » n'est pas un état, c'est une négation — à retirer plutôt qu'à lister).

