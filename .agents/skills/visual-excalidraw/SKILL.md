---
name: visual-excalidraw
description: Génération de schémas d'architecture et de flux vectoriels éditables au format Obsidian Excalidraw (.excalidraw.md) ou standard (.excalidraw) (ADR-0337).
disable-model-invocation: true
---

# ✏️ Visual Excalidraw (Schémas Vectoriels Éditables Obsidian)

**Règle d'or :** Générer des schémas d'architecture, des topologies de systèmes et des parcours utilisateurs au style dessin à main levée (*hand-drawn*), directement intégrés et **100% modifiables au clic dans Obsidian** via le plugin Excalidraw.

---

## ⚡ Quand l'utiliser (*When to Use*)
- Schémas d'architecture globale pour les ADRs ou dossiers d'architecture (`docs/01-architecture/`).
- Wireframes conceptuels d'écrans et flux de navigation UI/UX sous `docs/05-assets/`.
- Cartographies conceptuelles nécessitant des annotations manuelles par l'utilisateur.

## 🚫 Quand NE PAS l'utiliser (*When NOT to Use*)
- Diagrammes de séquence API stricts ou machines à états (utiliser `visual-mermaid`).
- Toiles de Story Mapping 2D avec des dizaines de cartes (utiliser `obsidian-canvas`).

---

## 📋 Modes de Sortie & Formats

### 1. Mode Obsidian Markdown (Recommandé : `.excalidraw.md`)
Ce format permet à Obsidian d'ouvrir directement le dessin avec le plugin Excalidraw tout en conservant une sauvegarde texte :

```markdown
---
excalidraw-plugin: parsed
tags: [excalidraw, architecture]
---
==⚠ Basculez en EXCALIDRAW VIEW dans le menu More Options de ce document. ⚠==

# Excalidraw Data

## Text Elements
%%
## Drawing
```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [
    {
      "id": "rect-1",
      "type": "rectangle",
      "x": 100,
      "y": 100,
      "width": 240,
      "height": 100,
      "backgroundColor": "#1e293b",
      "strokeColor": "#38bdf8",
      "strokeWidth": 2,
      "fillStyle": "solid",
      "roughness": 1,
      "roundness": { "type": 3 },
      "seed": 1001
    },
    {
      "id": "text-1",
      "type": "text",
      "x": 120,
      "y": 135,
      "width": 200,
      "height": 30,
      "text": "Service Principal",
      "fontSize": 20,
      "fontFamily": 5,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#ffffff",
      "containerId": "rect-1"
    }
  ],
  "appState": {
    "viewBackgroundColor": "#0f172a",
    "gridSize": null
  },
  "files": {}
}
```
%%
```

### 2. Règles de Positionnement & Esthétique
- **Typographie** : `fontFamily: 5` (Excalifont) pour l'aspect carnet de croquis professionnel.
- **Palette mLoop** : Fond sombre `#0f172a` / `#1e293b`, bordures Cyan `#38bdf8` / Émeraude `#10b981` / Ambre `#f59e0b`.
- **Liaisons de boîtes** : Utiliser `containerId` sur l'élément texte pour qu'il reste centré automatiquement dans son rectangle parent.
