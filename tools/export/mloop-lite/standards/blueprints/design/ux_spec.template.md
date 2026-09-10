# 🎨 Spécification UX/UI & Matrice des 4 États — <ECRAN / COMPOSANT>

## 1. Intention de l'Écran & Objectif Utilisateur
* Quel est l'objectif principal de l'utilisateur sur cet écran ?

## 2. Matrice des 4 États Obligatoires
| État | Comportement Visuel & Contenu | Call-to-Action (CTA) |
|---|---|---|
| **Vide (Empty State)** | Illustration bienveillante + message invitant à créer un premier élément | Bouton « Créer » bien visible |
| **Chargement (Loading)** | Skeleton screens discrets (éviter les spinners bloquants) | Interactions temporairement désactivées |
| **Succès (Happy Path)** | Liste ordonnée des données, hiérarchie visuelle claire | Actions secondaires discrètes |
| **Erreur (Error State)** | Bannière explicative non technique avec action de remédiation | Bouton « Réessayer » ou « Contacter le support » |

## 3. Règles d'Accessibilité (WCAG 2.1 AA)
* Contraste minimum texte / fond : 4.5:1.
* Navigation complète au clavier supportée.
