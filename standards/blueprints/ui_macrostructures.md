# 📐 Référentiel des Macrostructures UI & États d Interaction (SSOT)

> **Référence :** Hallmark Design System & Anti-Slop Architecture (ADR-0340)  
> **Usage :** Récits \layer: frontend\ ou \layer: fullstack\, spécifications UX dans \story_template.md\, skills \	riage\, \plan\, \impeccable\.

---

## 1. Les 21 Macrostructures UI (Catalogue Anti-Slop)

Pour empêcher la convergence des modèles d IA vers un template stéréotypé unique (Héros centré → 3 cartes → CTA → Footer), mLoop intègre un catalogue de 21 macrostructures distinctes. Chaque macrostructure définit l agencement spatial, la hiérarchie visuelle, le rythme de défilement et le placement des actions clés.

| # | Macrostructure | Description & Caractéristiques Clés | Type d écran / Cas d usage recommandé |
| :--- | :--- | :--- | :--- |
| **01** | **Bento Grid** | Grille modulaire asymétrique de tuiles de tailles variées combinant métriques, graphiques, listes et actions. | Dashboards, Hubs récapitulatifs, Portails d accueil |
| **02** | **Long Document** | Format continu type mémo, documentation dense ou journal de bord avec navigation latérale et titres en ligne. | Documentation technique, Pages légales, Rapports d analyse |
| **03** | **Marquee Hero** | En-tête plein écran ou déclaration typographique/visuelle dominante sans surcharge au-dessus du pli. | Écrans d atterrissage, Pages de présentation de produit |
| **04** | **Stat-Led** | Mise en valeur d un chiffre clé ou d un indicateur majeur au centre de la narration visuelle. | Suivi de KPI, Tableaux de bord analytiques, Bilans |
| **05** | **Workbench** | Interface guidée axée sur des vues concrètes de l outil, captures d écrans annotées ou panneaux interactifs. | Outils d administration, Simulateurs, Configurateurs |
| **06** | **Conversational FAQ** | Format questions franches et réponses concises, accordéons ordonnés et recherche contextuelle. | Support, FAQ interactive, Centres d aide |
| **07** | **Manifesto** | Typographie déclarative forte, affichage éditorial imposant et prises de position claires. | Pages À Propos, Vision produit, Chartes éthiques |
| **08** | **Photographic / Media** | Richesse visuelle plein cadre où l image ou la vidéo guide la consultation avant le texte. | Catalogues, Portfolios, Présentation de matériel/projets |
| **09** | **Quote-Led** | Mise en avant de témoignages, citations clients ou retours d expérience comme vecteur principal de crédibilité. | Preuve sociale, Avis d experts, Études de cas |
| **10** | **Specimen** | Rendu éditorial inspiré des fonderies typographiques, repères numérotés en marge gauche et ligatures soignées. | Édition, Catalogues typographiques, Revues de design |
| **11** | **Timeline / Feed** | Défilement vertical chronologique d événements, d activités ou de messages horodatés. | Historiques d audit, Flux d activité, Journal d événements |
| **12** | **Split-Screen** | Séparation binaire de l écran (ex. aperçu à gauche / formulaire ou actions à droite). | Formulaires de création, Authentification, Paramétrages |
| **13** | **Card-Stack / Carousel** | Défilement horizontal ou superposition séquentielle de cartes de contenu autonome. | Onboarding, Galeries de modèles, Wizards pas-à-pas |
| **14** | **Master-Detail** | Liste latérale de sélection (master) couplée à une vue d inspection détaillée (detail). | Gestionnaires d entités (CRUD), Boîtes de réception, Inspecteurs |
| **15** | **Wizard / Step-by-Step** | Entonnoir séquentiel avec barre de progression, validation d étape et navigation amont/aval. | Tunnels d inscription, Processus de paiement, Diagnostics |
| **16** | **Data Sheet / Matrix** | Tableaux denses de comparaison technique, matrices de fonctionnalités ou grilles tarifaires. | Comparatifs de plans, Fiches techniques, Matrices d accès |
| **17** | **Command Palette / CLI** | Interface centrée sur un champ de recherche modal (\Cmd+K\), raccourcis clavier et exécution rapide. | Outils développeurs, Navigation rapide d applications SaaS |
| **18** | **Kanban Board** | Colonnes de statut avec cartes déplaçables, badges de priorité et filtres multidimensionnels. | Gestion de tâches, Suivi d états de dossiers, Pipelines |
| **19** | **Interactive Canvas** | Espace de travail infini, nœuds interconnectés ou surfaces de glisser-déposer. | Éditeurs visuels, Constructeurs de requêtes, Outils de modélisation |
| **20** | **Metric Compare** | Disposition côte-à-côte pour confronter deux versions, scénarios ou jeux de données. | Analyse de versions (Diff), Comparateurs de simulation |
| **21** | **Minimal Spotlight** | Interface épurée focalisée sur un point d interaction unique (recherche, saisie, bouton principal). | Écrans de recherche pure, Pages de saisie rapide |

---

## 2. Règle de Diversification Multi-Écrans (Memory Log)

Pour éviter que plusieurs pages consécutives d un même projet ne soient générées avec la même structure :
1. Chaque récit \layer: frontend\ ou \layer: fullstack\ doit obligatoirement déclarer sa \macrostructure\ dans son frontmatter ou sa section UX.
2. L agent doit vérifier les récits déjà analysés dans le backlog : **deux écrans voisins ou consécutifs ne doivent jamais partager la même macrostructure**, sauf contrainte de système explicite formalisée dans un \DESIGN.md\.

---

## 3. Matrice des 8 États d Interaction pour Composants UI (Component-Scope)

Tout composant interactif d interface (bouton, champ de saisie, sélecteur, modale, carte cliquable) spécifié dans une User Story ou un design system mLoop doit obligatoirement expliciter son comportement sur les **8 états d interaction** :

\\	ext
┌─────────────────────────────────────────────────────────────┐
│ 1. DEFAULT       : État nominal au repos.                   │
│ 2. HOVER         : Survol du pointeur (transition subtile). │
│ 3. FOCUS-VISIBLE : Focus clavier (contour d accessibilité). │
│ 4. ACTIVE        : Pression / clic en cours.                │
│ 5. DISABLED      : Désactivé (indicateur visuel non-bloquant)│
│ 6. LOADING       : En cours de traitement (spinner/patience)│
│ 7. ERROR         : Anomalie de validation ou réseau.        │
│ 8. SUCCESS       : Confirmation visuelle ou validation.     │
└─────────────────────────────────────────────────────────────┘
\
---

## 4. Portes de Contrôle Anti-AI-Slop (Extrait Normatif)

* 🚫 **Zéro dégradé violet/bleu générique** : Palettes ancrées sur une teinte de marque en espace OKLCH.
* 🚫 **Zéro titre en italique** : Les balises \<h1>\ à \<h6>\ sont obligatoirement en \ont-style: normal\.
* 🚫 **Zéro transition globale \	ransition: all\** : Cibler explicitement les propriétés animées avec des easings exponentiels (\cubic-bezier(0.16, 1, 0.3, 1)\).
* 🚫 **Zéro débordement horizontal** : Imposer \overflow-x: clip\ sur \html\ et \ody\.
* 🚫 **Zéro métrique ou testimonial inventé** : Utiliser des tirets d attente (\—\) ou des données réelles issues de \docs/\.
