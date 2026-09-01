---
name: impeccable
description: "Design language, design system generator, and 23 frontend UX/UI commands for AI coding agents. Enforces visual excellence, anti-slop rules, and DESIGN.md/PRODUCT.md SSOT."
---

# Impeccable Design Language & Frontend Skill

Impeccable is the design language that elevates AI harnesses to professional-grade UI/UX design. It establishes design tokens, eliminates generic AI frontend anti-patterns ("AI slop"), and provides 23 precision design commands.

---

## 1. The 23 Impeccable Commands

| Command | Action | Description |
| :--- | :--- | :--- |
| `/impeccable init` | **Setup** | Gathers project context, writes `PRODUCT.md` and `DESIGN.md`, establishes brand lane and tokens. |
| `/impeccable document` | **Extraction** | Generates or updates root `DESIGN.md` from active codebase styles. |
| `/impeccable craft` | **Build** | Full shape-then-build workflow with visual iteration. |
| `/impeccable extract` | **System** | Pulls reusable components, color tokens, and typography into the design system. |
| `/impeccable shape` | **UX Planning** | Plans UI architecture and wireframe layout before writing code. |
| `/impeccable critique` | **Review** | UX critique: visual hierarchy, cognitive load, clarity, and emotional resonance. |
| `/impeccable audit` | **QA / Compliance** | Technical checks: WCAG contrast, touch targets, DOM depth, responsiveness, semantics. |
| `/impeccable polish` | **Refinement** | Final polish pass: micro-spacing, alignment, hover states, glassmorphism, shipping readiness. |
| `/impeccable bolder` | **Amplify** | Injects character and visual punch into flat or timid layouts. |
| `/impeccable quieter` | **Tone Down** | Calms overly busy or overwhelming interfaces. |
| `/impeccable distill` | **Simplify** | Strips non-essential elements to reveal core functionality. |
| `/impeccable harden` | **Resilience** | Edge-case protection: empty states, text overflow, error handling, truncation. |
| `/impeccable onboard` | **Activation** | First-run experiences, empty state guidance, and onboarding affordances. |
| `/impeccable animate` | **Motion** | Adds purposeful, physics-based micro-animations and view transitions. |
| `/impeccable colorize` | **Palette** | Introduces strategic, harmonious color theory tailored to the brand. |
| `/impeccable typeset` | **Typography** | Refines font pairings, vertical rhythm, modular scales, and hierarchy. |
| `/impeccable layout` | **Structure** | Corrects grid alignment, spacing rhythm, and responsive layout flow. |
| `/impeccable delight` | **Moments** | Adds delightful micro-details and interactive tactile feedback. |
| `/impeccable overdrive` | **Advanced** | Implements advanced shaders, glowing SVG vectors, canvas, or complex animations. |
| `/impeccable clarify` | **Copy** | Rewrites ambiguous UI text, labels, tooltips, and micro-copy. |
| `/impeccable adapt` | **Responsive** | Fine-tunes mobile/tablet/desktop responsiveness and form factor adaptations. |
| `/impeccable optimize` | **Performance** | CWV optimization, layout shift prevention, SVG minification, CSS weight reduction. |
| `/impeccable live` | **Iteration** | Visual iteration and variant exploration directly in the live browser. |

---

## 2. Pre-Emit Self-Critique (6 Axes - ADR-0340)

Avant d'émettre tout livrable UI (code ou spécification), auto-évaluer le design de 1 à 5 sur chaque dimension. **Tout score < 3 impose une passe de révision immédiate.**

| Axe | Dimension | Critère d'évaluation |
| :--- | :--- | :--- |
| **P** | **Philosophie** | La page/composant a-t-il une intention claire et assumée, ou est-ce un assemblage générique ? |
| **H** | **Hiérarchie** | L'utilisateur discerne-t-il en < 2 secondes le primaire, secondaire et tertiaire ? |
| **E** | **Exécution** | Les micro-détails (épaisseurs de bordures, contrastes OKLCH, anneaux de focus) sont-ils impeccables ? |
| **S** | **Spécificité** | Le design est-il taillé sur-mesure pour ce brief précis, ou interchangeable avec n'importe quel SaaS ? |
| **R** | **Retenue** | A-t-on supprimé tout élément décoratif inutile (auroras, orbes flottants, padding excessif) ? |
| **V** | **Variété** | La macrostructure choisie diffère-t-elle structurellement des écrans précédents du projet ? |

> **Tampon Obligatoire dans les livrables CSS/Composants** :  
> `/* Impeccable · pre-emit critique: P5 H4 E5 S4 R5 V5 */`

---

## 3. The Extended Anti-Pattern Detector Rules (Hallmark Anti-AI Slop)

Lors de la conception, de la révision ou de la spécification de toute UI, interdiction stricte de ces défauts de génération IA :

1. 🚫 **No generic purple-to-blue SaaS gradients**: Palettes ancrées sur une teinte de marque en espace OKLCH.
2. 🚫 **No pure `#000000` or `#ffffff` neutral grays**: Toujours teinter les neutres avec la teinte d'ancrage de la marque (minimum 0.005 chroma).
3. 🚫 **No italic headers**: Les titres `<h1>` à `<h6>` et display type sont obligatoirement droits (`font-style: normal`). L'italique est réservé à l'emphase au sein des paragraphes de texte courant.
4. 🚫 **No unsemantic nested cards**: Ne jamais imbriquer une carte dans une autre carte sans distinction sémantique.
5. 🚫 **No default Inter / Roboto everywhere**: Appliquer la règle typographique **2+1** (1 Display face + 1 Body face + max 1 Outlier pour les métriques/wordmark).
6. 🚫 **No bounce / elastic easing curves & No `transition: all`**: Utiliser des easings exponentiels fluides (`cubic-bezier(0.16, 1, 0.3, 1)`) et cibler explicitement chaque propriété animée.
7. 🚫 **No `hover:scale-105` systématique**: Privilégier des rétroactions subtiles (changement de teinte de surface, micro-translation de 1px).
8. 🚫 **No accent footprint overload**: La couleur d'accent ne doit pas dépasser ~5% de la surface du viewport (accent d'emphase, jamais de remplissage).
9. 🚫 **No re-drawn UI chrome**: Ne jamais dessiner de fausses barres de navigateur (boutons feux tricolores) ni de fausses coques de smartphone en CSS.
10. 🚫 **No unreadable low-contrast text**: Respecter WCAG AA (4.5:1 pour le texte normal, 3:1 pour les grands titres).
11. 🚫 **No undersized touch targets**: Minimum 44x44px sur mobile / tactile, 36x36px sur desktop.
12. 🚫 **No input/button vertical height mismatch**: Inputs et boutons d'un même formulaire partagent la même hauteur de base (min 44px) avec un contour de focus `outline` (jamais de variation de `border-width`).
13. 🚫 **No horizontal overflow / mandatory clipping**: Appliquer obligatoirement `overflow-x: clip` sur `html` et `body` pour garantir la résilience mobile à 320, 375, 414 et 768px sans briser les sticky headers.
14. 🚫 **No fabricated metrics or testimonials**: Interdiction d'inventer des métriques (*"+47% conversion"*, *"50,000+ teams"*) sans preuve factuelle dans `docs/` ; utiliser des placeholders explicites (`—`).
15. 🚫 **No dead states on interactive components**: Tout composant interactif doit implémenter la **matrice des 8 états** (`default`, `hover`, `:focus-visible`, `:active`, `disabled`, `loading`, `error`, `success`) et générer sa page de prévisualisation isolée `.preview.html`.
16. 🚫 **No mid-render token improvisation**: Toutes les couleurs et polices référencent des tokens nommés dans `DESIGN.md` / `tokens.css`.

---

## 4. Standard SSOT Artifacts

### `PRODUCT.md`
Capture l'intention produit, la cible utilisateur, la tonalité émotionnelle et la famille de macrostructure globale.

### `DESIGN.md`
Capture les design tokens et règles du système :
- **Color Palette (OKLCH)**: Teinte d'ancrage, neutres teintés, accent (< 5%), badges sémantiques.
- **Typography Scale (2+1)**: `--font-display`, `--font-body`, `--font-outlier`, hiérarchie H1-H6 (100% roman).
- **Macrostructures**: Référence aux 21 macrostructures SSOT ([`standards/blueprints/ui_macrostructures.md`](file:///c:/Memory%20Loop/standards/blueprints/ui_macrostructures.md)).
- **Component 8-State Matrix**: Matrice nominale pour boutons, inputs, modales et sélecteurs.
- **Motion Guidelines**: Durées, cubic-beziers exponentiels, support strict de `prefers-reduced-motion`.
