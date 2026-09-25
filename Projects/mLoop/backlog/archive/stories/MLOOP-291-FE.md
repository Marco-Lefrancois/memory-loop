---
id: MLOOP-291-FE
jira_key: ""
epic_key: EPIC-29-GRILL-V2-FRONTIER-SKILLS
type: Feature
title: "Protocole Handoff & Staging des Prototypes Jetables (scratch/prototypes/)"
tags:
  - grill
  - handoff
  - ungrillables
  - prototype-staging
  - zero-build
status: SHIPPED
validated_by: "Marco (PO - Feu Vert 2026-09-24)"
validated_at: "2026-09-24"
grill_me: DONE
layer: frontend
invest_score: 6/6
macro_size: M
created_at: "2026-09-24"
ttl_cycles: 4
---

# 📖 MLOOP-291-FE : Protocole Handoff & Staging des Prototypes Jetables (scratch/prototypes/)

---

## Description
**En tant qu'** Agent mLoop ou Concepteur IHM confronté à une question d'ergonomie visuelle ou d'interaction lors d'un cadrage,  
**je veux** déclencher automatiquement le protocole Handoff en matérialisant en moins de 30 secondes un prototype jetable zéro-build (HTML5/Tailwind CDN ou SVG) dans `Projects/<projet>/scratch/prototypes/`,  
**afin de** permettre à l'utilisateur de tester visuellement l'alternative en un clic (`file:///...`) et d'éradiquer les débats textuels abstraits sans introduire de dette de build (pas de `npm install` ni de serveur applicatif lourd).

---

## Contexte & Périmètre

### Contexte Métier
L'ADR-013 (issu de l'ADR-0389) consacre le Handoff Pattern : « When you hit an ungrillable question, use the handoff pattern: grill -> prototype -> grill again ».
Tenter d'arbitrer textuellement entre un dialogue modal, un panneau coulissant ou un stepper produit des discussions stériles. La solution retenue impose :
1. Détection des questions qualifiées de `is_ungrillable` (UX, agencement, densité visuelle).
2. Suspension temporaire de la dialectique textuelle et génération immédiate d'un prototype autonome.
3. Affichage d'un lien direct `file:///...` cliquable dans la console.
4. Promotion conditionnelle : en cas d'approbation par le PO, copie propre dans `docs/05-assets/mockups/` et référencement dans le récit de livraison.

### In-Scope
- Répertoire normalisé de staging : `Projects/<projet>/scratch/prototypes/` (inclus dans `.gitignore`).
- Convention de nommage stricte : `proto_<STORY_ID>_<sujet>.<html|svg>`.
- Générateur de squelette zéro-build :
  - Page HTML5 autonome avec inclusion CDN de Tailwind CSS (`<script src="https://cdn.tailwindcss.com"></script>`) ou styles embarqués purs.
  - Maquette SVG vectorielle autonome avec labels et zones interactives stylées.
- Affichage terminal du lien direct de prévisualisation : `ZeroFluffConsole.info(f"Prototype disponible : file:///{proto_path.as_posix()}")`.
- Mécanisme de promotion : copie vers `docs/05-assets/mockups/` lors de la validation finale du récit.

### Out-of-Scope
- Création de projets React / Vite / Vue pour les prototypes de cadrage.
- Démarrage d'un serveur HTTP persistant (la consultation locale directe `file:///` suffit).

---

## Critères d'acceptation (Gherkin 4 Piliers)

### 1. Pilier Nominal (Happy Path - Génération Zéro-Build)
```gherkin
Scénario: Génération instantanée d'un prototype HTML5 lors d'une question ungrillable
  Étant donné une question de cadrage classée is_ungrillable portant sur la disposition d'un formulaire
  Quand l'agent déclenche le protocole Handoff pour le récit "MLOOP-291-FE"
  Alors un fichier "proto_MLOOP-291-FE_formulaire.html" est créé sous "scratch/prototypes/"
  Et le fichier s'ouvre directement dans un navigateur sans étape de compilation npm
  Et un lien cliquable "file:///..." est affiché dans la console en moins de 30 secondes
```

### 2. Pilier Exception & Fallback SVG
```gherkin
Scénario: Génération d'une maquette SVG vectorielle pour arbitrage de diagramme
  Étant donné une question ungrillable portant sur la hiérarchie visuelle d'un composant
  Quand l'option de rendu choisie est vectorielle
  Alors un fichier "proto_MLOOP-291-FE_hierarchie.svg" autonome est généré
  Et le fichier contient les éléments SVG valides avec styles CSS intégrés
```

### 3. Pilier Résilience & Création Automatique de l'Arborescence
```gherkin
Scénario: Création automatique du répertoire scratch de staging
  Étant donné un projet mLoop où le dossier "scratch/prototypes/" n'existe pas encore
  Quand le premier prototype Handoff est déclenché
  Alors le répertoire parent est automatiquement créé avec les permissions appropriées
  Et l'écriture du fichier ne lève aucune exception bloquante
```

### 4. Pilier Promotion & Clôture Décisionnelle
```gherkin
Scénario: Promotion du prototype validé dans les actifs officiels
  Étant donné un prototype "proto_MLOOP-291-FE_formulaire.html" validé par le Product Owner
  Quand la décision est actée dans le récit
  Alors l'artefact est promu dans "docs/05-assets/mockups/formulaire_valide.html"
  Et le récit de spécification contient le lien relatif vers cet actif permanent
```

---

### Contrats d'Échange API (Interface Python & In-Process)

#### Matrice des Contrats API
- **OQ-291 (Exemption Zéro Fausse Route)** : Exemption complète de la Matrice des Contrats API réseau — composant de rendu frontend zéro-build générant des artefacts statiques locaux (HTML5 / Tailwind CDN / SVG) sous `scratch/prototypes/`, visualisables via `file:///` sans serveur HTTP ni API réseau distante (ADR-0319).

**Contrats Python Internes :**
- `stage_prototype(project_path: Path, story_id: str, subject: str, content: str, kind: str = "html") -> Path`
- `promote_prototype(prototype_path: Path, target_dir: Path, final_name: str) -> Path`

---

## Logique Métier & Gabarit Zéro-Build

### Structure du template HTML5 (`stage_prototype`)
```html
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Prototype {{STORY_ID}} : {{SUBJECT}}</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-50 text-slate-900 p-8">
  <div class="max-w-4xl mx-auto bg-white rounded-xl shadow-md p-6 border border-slate-200">
    <div class="border-b pb-4 mb-4 flex justify-between items-center">
      <h1 class="text-xl font-bold text-indigo-700">mLoop Handoff Prototype — {{STORY_ID}}</h1>
      <span class="text-xs bg-amber-100 text-amber-800 px-2.5 py-0.5 rounded-full font-semibold">Zéro-Build Sandbox</span>
    </div>
    <!-- CONTENU DU COMPOSANT IHM PROTOTYPÉ -->
    {{CONTENT}}
  </div>
</body>
</html>
```

---

## Références
- 🏛️ **ADR Associés** : [ADR-013](../../../docs/01-architecture/ADR-013_epic-29_grill_v2_frontier_rounds_ungrillable_context.md) · [ADR-0389](../../../../standards/adr-system/0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md)
- 📂 **Spécification Source** : `docs/00-ingested/grill-me/03_skills_grill_me_aihero.md`
- 📦 **Épopée Parente** : [`EPIC-29-GRILL-V2-FRONTIER-SKILLS`](../epics/epic_grill_v2_frontier_rounds_ungrillable_context.md)