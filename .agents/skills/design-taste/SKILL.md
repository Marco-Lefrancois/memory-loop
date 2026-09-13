---
name: design-taste
description: Framework Frontend & UI Anti-Slop pour mLoop (dials 1-10, tokens OKLCH). Use when refining frontend styling, eliminating generic AI design cliches, or establishing bespoke visual identity.
---

# 🎨 design-taste : Framework Frontend & UI Anti-Slop mLoop

> **Origine :** Standard dérivé de `Leonxlnx/taste-skill` (v2)  
> **Périmètre :** Interfaces web, Dashboards (`Projects/mLoop-Dashboard/`), Plannotator, Landing pages et composants UI interactifs.  
> **Principe Cardinal :** L'agent lit le contexte avant de coder, choisit une direction esthétique intentionnelle et refuse tout boilerplate générique.

---

## 0. INFERENCE DU BRIEF ("Read the Room")

Avant d'écrire la moindre ligne de CSS ou de composant, **déduisez ce que l'utilisateur ou le projet requiert réellement**. La majorité du code d'interface généré par IA échoue parce que le modèle applique un esthétisme par défaut au lieu d'analyser le contexte.

### 0.A Les 6 Signaux Analysés
1. **Type d'interface** : Dashboard opérationnel, landing SaaS, portfolio, outil interne, documentation, portail B2B.
2. **Vocabulaire de tonalité** : "minimaliste", "calme", "Linear-style", "Awwwards", "brutaliste", "dense", "Apple-y", "ludique", "sérieux B2B".
3. **Signaux de référence** : URLs citées, maquettes existantes, produits benchmarkés.
4. **Audience cible** : Développeur/tech vs acheteur B2B vs grand public. L'audience dicte le design, pas les préférences du modèle.
5. **Assets existants** : Palette de couleurs de la marque, typographies, logos, tokens Tailwind déjà configurés.
6. **Contraintes strictes** : Accessibilité WCAG AA, densité d'information, lisibilité en mode sombre/clair, temps de chargement.

### 0.B Déclaration Obligatoire "One-Line Design Read"
Avant toute génération de code UI, l'agent formule explicitement en une ligne :
> **"Reading this as: `<page kind>` for `<audience>`, with a `<vibe>` language, leaning toward `<design system or aesthetic family>`."**

*Exemple :*
> *"Reading this as: Telemetry Dashboard for mLoop engineers, with a Linear-style high-density language, leaning toward Tailwind utilities + Lucide + monospace accents + restrained micro-interactions."*

---

## 1. DISCIPLINE ANTI-DEFAULT (Interdictions Formelles)

L'agent a l'interdiction d'utiliser les réflexes paresseux des LLMs :
- 🚫 **Bannir l'AI-Purple** : Interdiction des dégradés violet/indigo génériques (`from-purple-600 to-indigo-600`) sauf demande explicite du client.
- 🚫 **Bannir les cartes Bento 3 colonnes symétriques et prévisibles** : Varier la taille, l'asymétrie et la hiérarchie visuelle.
- 🚫 **Bannir les textes centrés sur 6 lignes** : Les titres longs centrés nuisent à la lisibilité. Aligner à gauche avec une forte ancre visuelle.
- 🚫 **Bannir les Hero sections 100vh stéréotypées** : Pas de formule automatique "Titre géant + sous-titre mou + 2 boutons côte à côte".
- 🚫 **Bannir les ombres portées baveuses** : Utiliser des bordures subtiles (`border border-border/50`) et des ombres ultra-fines calibrées (`shadow-[0_1px_2px_rgba(0,0,0,0.05)]`).

---

## 2. LES CURSEURS NUMÉRIQUES DÉCLARATIFS (Dials 1-10)

L'agent calibre sa génération selon 3 curseurs numériques :

```markdown
- DESIGN_VARIANCE: [1-10]  (1 = conventionnel/centré · 10 = asymétrique/expérimental)
- MOTION_INTENSITY: [1-10] (1 = simples hovers CSS · 10 = scroll scrubbing, pinning, spring physics)
- VISUAL_DENSITY: [1-10]   (1 = très aéré/spatieux · 10 = console télémétrique dense)
```

- **Dashboards & Outils Internes (mLoop Core)** :
  `DESIGN_VARIANCE: 4 | MOTION_INTENSITY: 2 | VISUAL_DENSITY: 8`
- **Portails & Landing Pages** :
  `DESIGN_VARIANCE: 8 | MOTION_INTENSITY: 6 | VISUAL_DENSITY: 4`

---

## 3. RÈGLES DE TYPOGRAPHIE & COULEURS

1. **Hiérarchie Typographique Éprouvée** :
   - Titres : Familles géométriques ou sans-serif modernes (Inter, Geist, Plus Jakarta Sans, SF Pro).
   - Code/Données/Chiffres : Monospace précis (JetBrains Mono, Geist Mono, Fira Code) avec `tabular-nums` pour aligner les chiffres.
2. **Système de Couleurs & Contraste** :
   - Fond sombre : Ne jamais utiliser de noir absolu `#000000` sauf style OLED strict. Préférer un fond teinté `#0B0F17` ou `#090A0F`.
   - Contraste WCAG AA systématique sur le texte secondaire (`text-muted-foreground`).

---

## 4. RÈGLE STRICTE FULL-OUTPUT ENFORCEMENT (`output-skill`)

Inspiré de `research/laziness/` de taste-skill :
- ❌ **Interdiction formelle de tronquer** : Ne jamais insérer `// TODO: implement remaining items`, `/* rest of code here */` ou des ellipses.
- ❌ **Pas de mock incomplet** : Si un composant a 5 onglets, implémentez les 5 onglets ou découpez la livraison en sous-fichiers modulaires autonomes.
- ✅ **Livraison intégrale** : Chaque fichier généré doit être syntaxiquement complet, compilable et prêt pour la production.

---

## 5. CHECKLIST PRÉ-VOL UI (Pre-Flight Check)

Avant de déclarer une tâche UI terminée, vérifier :
1. [ ] Le *Design Read* a-t-il été énoncé et respecté ?
2. [ ] Les dégradés clichés et les grilles bento monotones ont-ils été évités ?
3. [ ] Le responsive (mobile 375px, tablette 768px, desktop 1280px+) fonctionne-t-il sans débordement horizontal (`overflow-x`) ?
4. [ ] Les chiffres et tableaux utilisent-ils `font-mono tabular-nums` ?
5. [ ] Aucun commentaire d'omission (`TODO`, `placeholder`) n'est présent ?
