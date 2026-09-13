---
name: svg-optimize
description: Optimisation et minification des fichiers vectoriels SVG (SVGO, suppression métadonnées). Use when minifying SVG mockups, cleaning vector paths, or reducing visual asset file sizes in docs/05-assets/.
---

# 🎨 Skill : Optimisation Vectorielle SVG (`/svg-optimize`)

Ce skill régit la minification et l'optimisation des fichiers graphiques vectoriels `.svg` déposés dans les actifs documentaires versionnés (`docs/05-assets/maquettes/`, `docs/05-assets/diagrams/` - ADR-0332) ou les ressources UI.

---

## 🛠️ Utilisation CLI

```powershell
# Optimiser tous les fichiers SVG sous docs/05-assets/ d'un projet
python src/swarm.py svg-optimize --project <nom_projet>

# Optimiser un dossier ou un fichier spécifique
python src/swarm.py svg-optimize --project <nom_projet> --input "docs/05-assets/maquettes"
```

---

## 💡 Réductions Obtenues
- Nettoyage des métadonnées d'éditeurs (Inkscape, Illustrator, Figma, Sketch).
- Fusion et minification des chemins géométriques (`paths`).
- Réduction du poids moyen de 30% à 70% sans aucune perte visuelle.
