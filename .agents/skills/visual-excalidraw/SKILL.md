---
name: visual-excalidraw
description: "Génération de schémas d'architecture et de flux vectoriels éditables au format Obsidian Excalidraw (.excalidraw.md) (ADR-0337). Use when designing conceptual sketches, wireframes, and hand-drawn architecture diagrams in Excalidraw format."
disable-model-invocation: true
---

# ✏️ Visual Excalidraw (Schémas Vectoriels Éditables Obsidian)

Générer des schémas d'architecture, des topologies de systèmes et des parcours utilisateurs au style dessin à main levée (*hand-drawn*), directement intégrés et **100% modifiables au clic dans Obsidian** via le plugin Excalidraw.

## 1. Ground Truth & Repository Anchoring (SSOT & Evidence)

Tous les schémas produits doivent refléter fidèlement l'état vérifiable du dépôt (SSOT & evidence factuelle) :
- Architecture système et ADRs : intégrer les schémas sous `docs/01-architecture/`, [standards/blueprints/](standards/blueprints/) et [Projects/](Projects/).
- Assets et wireframes : sauvegarder sous `docs/05-assets/` au format canonique `.excalidraw.md`.
- Validation des pipelines visuels : tests et scripts de génération vérifiés dans [tests/](tests/).

---

## 2. Core Execution Protocol

Suivre rigoureusement les étapes ordonnées :

### Étape 1 : Cartographie conceptuelle & Extraction
Extraire les composants réels, dépendances et flux d'échange depuis le code source ou la spécification active.

### Étape 2 : Structuration du JSON Excalidraw
Générer le bloc JSON embarqué sous la section `## Drawing` dans le format standard `.excalidraw.md` :
- Utiliser la police `fontFamily: 5` (Excalifont) pour l'aspect carnet de croquis professionnel.
- Appliquer la palette mLoop : Fond sombre `#0f172a` / `#1e293b`, bordures Cyan `#38bdf8`, Émeraude `#10b981`, Ambre `#f59e0b`.

### Étape 3 : Liaisons des conteneurs et connecteurs
Relier les blocs fonctionnels avec des flèches directionnelles explicites :
- Utiliser `containerId` sur les éléments texte pour garantir un centrage automatique et dynamique dans les conteneurs parents.

### Étape 4 : Validation de syntaxe et rendu
Vérifier l'intégrité du JSON généré et s'assurer que le fichier est lisible à la fois en texte brut et en mode visuel Obsidian.

---

## 3. Prescriptive Rules & Garde-fous

### Rules & Garde-fous (DO NOT / NEVER)
- **Règle 1** : DO NOT modifier les fichiers `.excalidraw.md` sans préserver la structure des balises `%%` et des en-têtes Obsidian.
- **Règle 2** : DO NOT injecter de coordonnées de positionnement négatives ou erratiques dans le bloc d'éléments.
- **Règle 3** : NEVER écraser un fichier schéma existant sans créer un point de sauvegarde.
- **Règle 4** : DO NOT utiliser Excalidraw pour des diagrammes de séquence stricts nécessitant un parsing textuel exact (utiliser `visual-mermaid`).

---

## 4. Gestion des erreurs, résilience et fallback

- **Comportement en cas d'erreur ou d'outil absent** : Si le plugin Obsidian Excalidraw n'est pas installé dans le coffre, le document reste 100% lisible et importable en fallback directement sur le site web `excalidraw.com`.
- **Dégradation en cas de corruption JSON** : Si le parseur JSON rencontre une erreur de syntaxe, l'agent doit immédiatement restaurer la version précédente et lever une alerte avec diagnostic du bloc corrompu.
- **Gestion des exceptions d'encodage** : Toute exception liée à l'encodage UTF-8 des caractères spéciaux ou accents doit être résolue nativement sans supprimer les libellés francophones.
