---
name: impeccable
description: "Langage de design, système de tokens et 23 commandes UX/UI éliminant le slop IA (règles OKLCH, anti-patterns, DESIGN.md). Use when designing UI components, establishing design tokens, reviewing visual layouts, or polishing frontend interfaces."
---

# Impeccable Design Language & Frontend Skill

Impeccable élève les agents de code au niveau de design UI/UX professionnel. Il formalise les design tokens, éradique les anti-patterns génériques de l'IA (*AI slop*) et applique 23 commandes de précision.

---

## 1. Les 23 Commandes Impeccable

| Commande | Rôle | Description |
| :--- | :--- | :--- |
| `/impeccable init` | **Setup** | Initialise `PRODUCT.md` et `DESIGN.md`, établit la voix de marque et les tokens. |
| `/impeccable document` | **Extraction** | Génère ou met à jour `DESIGN.md` depuis les styles actifs du dépôt. |
| `/impeccable craft` | **Build** | Cycle complet shape-then-build avec itération visuelle. |
| `/impeccable extract` | **System** | Extrait composants réutilisables, tokens de couleurs et typographie. |
| `/impeccable shape` | **UX Planning** | Planifie l'architecture UI et le wireframe avant tout code. |
| `/impeccable critique` | **Review** | Critique UX : hiérarchie visuelle, charge cognitive, clarté. |
| `/impeccable audit` | **QA** | Contrôles techniques : contraste WCAG, cibles tactiles, sémantique DOM. |
| `/impeccable polish` | **Refinement** | Finition : micro-espacements, alignements, états hover, préparation release. |
| `/impeccable bolder` | **Amplify** | Injecte du caractère et du contraste dans un layout trop timide. |
| `/impeccable quieter` | **Tone Down** | Calme une interface surchargée ou distrayante. |
| `/impeccable distill` | **Simplify** | Épure les éléments superflus pour révéler la fonction clé. |
| `/impeccable harden` | **Resilience** | Robustesse : empty states, overflow de texte, gestion d'erreurs. |
| `/impeccable onboard` | **Activation** | Expérience premier usage, guidage et affordances d'onboarding. |
| `/impeccable animate` | **Motion** | Micro-animations physiques ciblées et View Transitions. |
| `/impeccable colorize` | **Palette** | Palette harmonique stratégique adaptée à la marque (espace OKLCH). |
| `/impeccable typeset` | **Typography** | Échelle modulaire, paires typographiques 2+1, rythme vertical. |
| `/impeccable layout` | **Structure** | Grilles responsives, rythme d'espacement et flux de mise en page. |
| `/impeccable delight` | **Moments** | Micro-détails élégants et rétroactions tactiles interactives. |
| `/impeccable overdrive` | **Advanced** | Shaders canvas, vecteurs SVG lumineux ou animations avancées. |
| `/impeccable clarify` | **Copy** | Réécriture de textes d'interface ambigus, labels et micro-copies. |
| `/impeccable adapt` | **Responsive** | Adaptation mobile/tablette/desktop aux différents formats. |
| `/impeccable optimize` | **Performance** | Optimisation CWV, prévention CLS, minification SVG. |
| `/impeccable live` | **Iteration** | Itération visuelle interactive dans le navigateur en direct. |

---

## 2. Grille d'Auto-Critique Pré-Émission (6 Axes - ADR-0340)

Avant d'émettre tout livrable UI (code ou spec), évaluer de 1 à 5 sur chaque axe (**score < 3 = révision obligatoire**) :
- **P (Philosophie)** : Intention claire et assumée vs assemblage générique.
- **H (Hiérarchie)** : Distinction < 2s entre primaire, secondaire et tertiaire.
- **E (Exécution)** : Précision des bordures, contrastes OKLCH, anneaux de focus.
- **S (Spécificité)** : Sur-mesure pour le brief vs SaaS interchangeable.
- **R (Retenue)** : Élimination des décorations inutiles (orbes, auroras, padding excessif).
- **V (Variété)** : Macrostructure distincte des écrans précédents ([`standards/blueprints/ui_macrostructures.md`](../../standards/blueprints/ui_macrostructures.md)).

> **Tampon Obligatoire** : `/* Impeccable · pre-emit critique: P5 H4 E5 S4 R5 V5 */`

---

## 3. Les 16 Règles Inviolables Anti-Slop IA

1. 🚫 **Zéro dégradé violet/bleu SaaS générique** : Palettes ancrées en OKLCH.
2. 🚫 **Zéro neutre `#000000` ou `#ffffff` pur** : Toujours teinter avec l'accent de marque (min 0.005 chroma).
3. 🚫 **Zéro titre en italique** : `<h1>` à `<h6>` obligatoirement droits (`font-style: normal`).
4. 🚫 **Zéro cartes imbriquées sans distinction** : Différencier élévation et padding.
5. 🚫 **Zéro Inter / Roboto partout** : Règle typographique **2+1** (Display + Body + max 1 Outlier).
6. 🚫 **Zéro easing élastique & zéro `transition: all`** : Courbes exponentielles (`cubic-bezier(0.16, 1, 0.3, 1)`).
7. 🚫 **Zéro `hover:scale-105` systématique** : Préférer de subtiles nuances de surface ou 1px de translation.
8. 🚫 **Zéro saturation d'accent** : Couleur d'accent limitée à ~5% du viewport.
9. 🚫 **Zéro chrome redessiné** : Ne jamais dessiner de fausse barre de navigateur ni fausse coque mobile en CSS.
10. 🚫 **Contraste WCAG AA impératif** : 4.5:1 pour le texte normal, 3:1 pour les grands titres.
11. 🚫 **Cibles tactiles adaptées** : Minimum 44x44px sur mobile, 36x36px sur desktop.
12. 🚫 **Hauteur homogène input/bouton** : Même hauteur de base (min 44px), focus via `outline`.
13. 🚫 **Anti-débordement horizontal** : `overflow-x: clip` obligatoire sur `html` et `body`.
14. 🚫 **Zéro métrique fabriquée** : Remplacer les fausses métriques par des tirets (`—`).
15. 🚫 **Matrice des 8 états** : `default`, `hover`, `:focus-visible`, `:active`, `disabled`, `loading`, `error`, `success`.
16. 🚫 **Zéro token improvisé** : Couleurs et polices proviennent de `DESIGN.md` / `tokens.css`.
