# 🏆 Hub des Récits Références (Gold Standards) - Framework mLoop

Ce répertoire contient le **Récit Étalon Canonique (`STORY_GOLD_STANDARD.md`)** servant de benchmark de qualité universel pour l'ensemble des agents d'analyse (`plan`, `orchestrator`) et de validation (`sentinel`, `validate`) du framework mLoop.

---

## 📐 Conformité au Gabarit Officiel Unique (`story_template.md`)

Conformément à l'ADR-0303 et au validateur de calibrage (`calibrate.py`), tout récit dans mLoop doit suivre l'ordre immuable des **8 sections du Gabarit Unique** :
1. `## Description`
2. `## Contexte`
3. `## Critères d'acceptation` (`### Interface et UX`, `### Logique et Comportement`, `### Liste Call to Actions`)
4. `## Règles d'affaires`
5. `## Maquettes` (Figma / Captures / Mermaid)
6. `## Contrats d'échange API`
7. `## Notes Techniques pour l'implémentation`
8. `## Scénarios de test` (Gherkin 4 Piliers)

---

## 🎯 Grille des 6 Critères d'Excellence Métier & Ergonomique

Pour qu'un récit soit qualifié de **Gold Standard** (INVEST Score > 95%), il doit satisfaire l'intégralité des 6 critères ci-dessous :

### 1. Typage Explicite des Champs & Contrôles UI
- Aucun champ de saisie ne doit être décrit de façon générique ("Un champ de saisie").
- Spécifier le type exact (`type="number"`, `textarea`, `dropdown`, `chips/cards`, `stepper [-]/[+]`).
- Préciser les déclencheurs matériels (ex: affichage forcé du pavé numérique mobile pour `type="number"`).

### 2. Micro-Interactions & Raccourcis Métiers
- Description explicite des raccourcis d'efficacité utilisateur (ex: bouton `[Max]` calculant le reliquat du stock).
- Préciser les jauges de capacité, calculs et résumés en temps réel (`onChange` / `onBlur`).

### 3. Matrice Complète des 4 États UI
- **Empty State** : Comportement visuel lorsque les données sont vides ou non sélectionnées (bouton de confirmation grisé/inactif).
- **Processing / Loading State** : État d'attente lors de la soumission (inputs `disabled`, spinner circulaire sur le bouton).
- **Inline Error State** : Gestion visuelle des erreurs de saisie (contour rouge du champ, message d'erreur explicite sous le champ).
- **Success State** : Feedback de confirmation (Toast flottant vert, redirection).

### 4. Ergonomie & UX Mobile/PDA
- Spécification de l'ergonomie physique (ex: auto-scroll pour positionner la zone de saisie en haut de l'écran afin d'éviter qu'elle ne soit masquée par le clavier virtuel).

### 5. Tableau Exhaustif Call to Actions (CTA)
- Chaque élément interactif de l'écran doit figurer dans la table CTA avec la structure stricte :  
  `| Élément UI | Trigger | Action (Navigation/API) | Feedback & État Final |`

### 6. Blindage Gherkin Strict sans Scaffolding (ADR-0301)
- Présence exacte des **4 piliers de test** (Nominal, Exceptions/Rejets RM-XXX, Résilience/Mode dégradé, UX/Observabilité).
- **Zéro commentaire d'échafaudage** (`# PILIER 1 : CHEMIN NOMINAL` doit être retiré du bloc Gherkin rédigé final).
- **Titre métier pur** sur la ligne `Fonctionnalité:` (interdiction d'y inclure des références entre parenthèses).
- **Règles d'affaires pures (Règle #7)** : Aucun identifiant éphémère (`RM-REC-007-01`) dans les titres des règles d'affaires.

---

## 🔍 Fichiers Étalons Références
- **[GOLD-REC-015-FE.md](file:///c:/Memory%20Loop/standards/gold_standards/GOLD-REC-015-FE.md)** : Récit canonique Frontend UI/Desktop d'après le cas réel modèle **`REC-015-FE`** (Panier de vente & Inventaire disponible).




