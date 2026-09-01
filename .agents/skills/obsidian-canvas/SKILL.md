---
name: obsidian-canvas
description: Génération et synchronisation automatique de toiles 2D interactives Obsidian Canvas (.canvas) pour le Story Mapping et le graphe DAG de sprint (ADR-0337).
disable-model-invocation: true
---

# 🗺️ Obsidian Canvas (Toiles Spatiales 2D & Story Mapping)

**Règle d'or :** Transformer les tables linéaires de backlog et les dépendances de sprint en toiles panoramiques interactives au format officiel **Obsidian JSON Canvas (`.canvas`)**, avec disposition spatiale déterministe et codes couleurs de statut.

---

## ⚡ Quand l'utiliser (*When to Use*)
- Génération d'une vue 360° du Story Mapping (`backlog/story_mapping.canvas`).
- Visualisation interactive du graphe d'ordonnancement DAG du sprint (`backlog/sprint_dag.canvas`).
- Cartographie d'architecture reliant visuellement modules, règles d'affaires et récits verticaux.
- Invoqué via la CLI mLoop : `python src/swarm.py canvas --project <nom_projet>` ou `/loop canvas`.

## 🚫 Quand NE PAS l'utiliser (*When NOT to Use*)
- Simples diagrammes de séquence ou flux séquentiels compacts (utiliser `visual-mermaid`).
- Croquis à main levée vectoriels (utiliser `visual-excalidraw`).

---

## 📐 Spécification du Format Obsidian Canvas

Un fichier `.canvas` est un document JSON composé de `nodes` (cartes de texte, fichiers, ou groupes) et d'`edges` (flèches relationnelles) :

```json
{
  "nodes": [
    {
      "id": "group-epic-1",
      "type": "group",
      "label": "🛒 Épopée : Gestion du Panier",
      "x": 0,
      "y": 0,
      "width": 700,
      "height": 500,
      "color": "1"
    },
    {
      "id": "card-us-01",
      "type": "text",
      "text": "### [REC-001] Initialisation Panier\n**Statut :** `READY_FOR_DEV` 🟢\n\n- UI MAUI Grid\n- Endpoint GET /api/v1/cart",
      "x": 30,
      "y": 60,
      "width": 300,
      "height": 180,
      "color": "4"
    }
  ],
  "edges": [
    {
      "id": "edge-1",
      "fromNode": "card-us-01",
      "fromSide": "right",
      "toNode": "card-us-02",
      "toSide": "left",
      "label": "Dépendance"
    }
  ]
}
```

### Codes Couleurs Standards Obsidian Canvas :
- `"1"` : 🔴 Rouge / Rose (Bloqué / `ON-HOLD` / Alerte critique)
- `"2"` : 🟠 Orange (En attente d'arbitrage / `READY_FOR_GROOMING`)
- `"3"` : 🟡 Jaune (En cours d'analyse / `IN_ANALYZE`)
- `"4"` : 🟢 Vert (Validé / Prêt pour le dev / `READY_FOR_DEV`)
- `"5"` : 🔵 Cyan / Bleu (Documentation & Références SSOT)
- `"6"` : 🟣 Violet (Épopées & Groupes d'Architecture)
