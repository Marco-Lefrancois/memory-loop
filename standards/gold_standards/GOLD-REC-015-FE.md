---
id: REC-015-FE
jira_key: COUVBOIRE-990
epic_key: COUVBOIRE-505
type: Feature
title: Interface Panier de vente & Inventaire disponible (Desktop)
tags:
  - desktop
  - ui
  - ventes
  - inventaire
layer: frontend
status: READY_FOR_DEV
invest_score: 6/6
---

# Interface Panier de vente & Inventaire disponible (Desktop)

## Description

**En tant que** répartiteur des ventes ou gestionnaire d'inventaire,  
**je veux** consulter l'inventaire des œufs disponibles par troupeau, composer un panier de vente multi-lots avec ajustement dynamique des quantités et des caisses/tiroirs, et finaliser la vente sous un numéro de bon/référence,  
**afin de** déduire précisément les sorties de stock de la chambre froide / Grange Verte (surplus d'œufs, œufs à mayonnaise, sous-produits) et consigner les ventes en direct ou en différé.

---

## Contexte

L'opération de vente de surplus d'œufs est réalisée sur **poste de travail (Desktop / PC)** dans le bureau de réception / chambre froide.
L'interface réunit deux concepts distincts : le **panier de vente** (en haut) pour la préparation de la transaction, et l'**inventaire disponible** (en bas) pour la sélection. L'opérateur sélectionne les lots nécessaires pour honorer une commande ou pour saisir a posteriori les bons de livraison. L'interface garantit la conversion en temps réel œufs/caisses, autorise la vente partielle (conservation du reliquat en inventaire), et exige un numéro de référence (bon jaune) avant la soumission.

---

## Critères d'acceptation

### Interface et UX

#### 1. En-tête & Bandeaux Supérieurs

- **[Titre & Saisie Contextuelle]** : Bandeau affichant le titre *"Ventes"*. Contient un sélecteur interactif `Date de la vente` (type="date") positionné par défaut sur la date courante. Il modifie la date de la transaction (supporte rétroactif/anticipé).

#### 2. Panier de Vente (Haut de page)

- **[Synthèse & Jauges du Panier]** :
  - Badges de totaux ventilés par catégorie (ex: `BC 27 000`, `DJ 4 500`), jauge de volume global (`Total 31 500 œufs`) et champ texte obligatoire `# Référence`.
- **[Tableau des articles sélectionnés]** :
  - Colonnes : `# Troupeau`, `Catégorie d'œufs`, `# Buggy`, `Date de ponte`, `Quantité (Œufs)` (champ modifiable de type "number" avec rappel du max `/X`), `Caisse/Tiroir` (champ modifiable de type "number" avec rappel du max `/Y`), et bouton de retrait `[ ✕ ]`.

#### 3. Consultation de l'Inventaire Disponible (Bas de page)

- **[Filtres et Sections]** :
  - **Filtre de catégorie** : Filtre rapide (Segmented Control / Pilules) `Catégories d'œufs` (`Toutes`, `BC`, `DJ`, `PIWI`). Le filtrage est asynchrone (retour attendu < 200ms).
  - **Sections groupées par Troupeau** : Chaque troupeau disponible (ex. : `162-2694-AVX6`) agit comme un groupe distinct. L'en-tête gris du groupe affiche les sous-totaux par catégorie pour ce troupeau et le volume global d'œufs.
  - **Tableau des Buggys (Détail du regroupement)** : Sous l'en-tête du troupeau se trouve le tableau de ses lots : `# Buggy` (ex. : `CSDEPOT1`), `Catégorie d'œufs` (Badge couleur : `BC` mauve doux `#EDE9FE`/`#6D28D9`, `DJ` turquoise doux `#E0F2FE`/`#0369A1`), `Date de ponte`, `Âge œufs` (en jours, calculé dynamiquement), `Œufs` disponibles, `# Référence` (ex. : `BECO`), `# Tracking` (ex. : `22693`).
  - **Indicateurs d'état** : Bouton contextuel `[ 🛒 ]` (Chariot bleu si disponible) ou `[ ✓ ]` (Coche verte si déjà présent dans le panier).

#### 4. Matrice des 4 états Visuels

- **Empty State** : Si le panier est vide, le tableau des articles sélectionnés est remplacé par une zone Placeholder grise avec une icône de chariot et le message : *"Votre panier de vente est vide. Sélectionnez des lots dans l'inventaire ci-dessous."* Le bouton `[ Vendre ]` est désactivé.
- **Processing / Loading State** : Affichage de Shimmers lors du chargement de l'inventaire, et d'un spinner bloquant (debounce) sur le bouton `[ Vendre ]` pendant l'appel réseau.
- **Inline Error State** : Les champs de quantité (œufs et caisses) s'affichent avec une bordure rouge et un texte d'aide si la valeur saisie dépasse le stock ou est <= 0.
- **Success State** : Notification Toast verte ("Vente #125464 enregistrée avec succès") et réinitialisation automatique de la page.

### Logique et Comportement

1. **[Liaison Bidirectionnelle Œufs ↔ Caisses]** : Modifier la quantité en œufs recalcule instantanément le champ Caisse/Tiroir selon le ratio d'emballage du chariot, et inversement.
2. **[Départ Partiel et Reliquat en Stock]** : Si l'opérateur saisit une quantité inférieure au total du lot (ex. : 7 200 œufs sur 10 800), la transaction déduit 7 200 œufs. L'inventaire conservera le reliquat (3 600 œufs) une fois la page rechargée.
3. **[Verrouillage de Soumission]** : Le bouton `[ Vendre ]` reste inactif (disabled) tant qu'il n'y a pas au moins 1 lot valide dans le panier ET que le champ `# Référence` n'a pas été rempli.
4. **[Date Transactionnelle]** : La date sélectionnée dans l'en-tête sera transmise comme date effective de la vente dans le payload API.

---

## Règles d'affaires

- **[Validation stricte des intrants]** : Les champs de saisie de quantités doivent strictement empêcher les caractères non-numériques et interdire la soumission de valeurs négatives.
- **[Atomicité]** : La soumission d'une vente est une action atomique. Si un des lots échoue (ex: conflit d'inventaire réseau), la vente entière est rejetée et l'opérateur est notifié.

---

## Maquettes

- 🖥️ **Écran Ventes (Panier & Inventaire)** : Maquette [Figma (Lien Officiel)](https://www.figma.com/design/oZyAh3zavoL5aVixNDloGr/Boires---Maquettes?node-id=2923-37218&t=aWaaziWSkFwj7Shd-4)

---

## Contrats d'échange API

Le Frontend consomme les endpoints exposés par le récit `REC-015-BE`.

| Finalité | Méthode | Route API |
| :--- | :--- | :--- |
| Obtenir l'inventaire | `GET` | `/api/v1/inventaire/disponible` |
| Soumettre la vente | `POST` | `/api/v1/ventes` |

---

## Notes Techniques pour l'implémentation

- Utiliser un mécanisme de debounce sur le clic du bouton "Vendre" pour prévenir toute frappe multiple accidentelle avant la résolution réseau.
- Injecter systématiquement le jeton Bearer d'authentification de session dans les requêtes API.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Interface Panier de vente et Inventaire disponible Desktop

  Scénario: Validation du parcours nominal de vente (Nominal)
    Étant donné que l'utilisateur est sur l'écran "Ventes" avec un inventaire chargé
    Et que le panier est initialement vide (Placeholder visible)
    Quand l'utilisateur clique sur "Ajouter au panier" pour un lot de 10 800 œufs
    Et qu'il saisit la référence "125464"
    Et qu'il clique sur "Vendre"
    Alors l'API "POST /api/v1/ventes" est appelée
    Et un toast de succès vert s'affiche
    Et le panier est réinitialisé à l'état vide

  Scénario: Blocage de vente avec quantité excessive (Exceptions)
    Étant donné un lot dans le panier disposant de 10 800 œufs maximum
    Quand l'utilisateur modifie la quantité d'œufs à "15 000"
    Alors le champ prend une bordure rouge
    Et le bouton "Vendre" est désactivé

  Scénario: Résilience face à un conflit réseau ou API indisponible (Résilience)
    Étant donné un panier valide prêt à être soumis
    Quand l'utilisateur clique sur "Vendre"
    Mais que l'API backend répond avec un code HTTP 500 ou 409
    Alors le spinner de chargement s'arrête
    Et un message d'erreur est affiché (ex: "Erreur réseau, veuillez vérifier l'inventaire")
    Et les données du panier sont conservées à l'écran pour une tentative ultérieure

  Scénario: Affichage adaptatif de l'état vide (UX)
    Étant donné que le panier de vente ne contient aucun lot
    Quand la page est rendue
    Alors le tableau des articles sélectionnés est remplacé par une zone grise
    Et l'icône de chariot vide est affichée avec le message "Votre panier de vente est vide."
```
