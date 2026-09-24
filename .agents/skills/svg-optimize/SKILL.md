---
name: svg-optimize
description: Optimisation et minification des fichiers vectoriels SVG (SVGO, suppression métadonnées). Use when minifying SVG mockups, cleaning vector paths, or reducing visual asset file sizes in docs/05-assets/.
---

# 🎨 Skill : Optimisation Vectorielle SVG (`/svg-optimize`)

Ce skill régit la minification et l'optimisation des fichiers graphiques vectoriels `.svg` déposés dans les actifs documentaires versionnés (`docs/05-assets/maquettes/`, `docs/05-assets/diagrams/` - ADR-0332) ou les ressources UI.

---

## 🛠️ Protocole d'Optimisation en 4 Étapes

1. **Analyse Préalable** : Identifier les fichiers SVG cibles sous `docs/05-assets/` et vérifier qu'ils ne sont pas verrouillés.
2. **Exécution Déterministe** :
   ```powershell
   # Optimiser tous les fichiers SVG sous docs/05-assets/ d'un projet
   python src/swarm.py svg-optimize --project <nom_projet>

   # Optimiser un dossier ou un fichier spécifique
   python src/swarm.py svg-optimize --project <nom_projet> --input "docs/05-assets/maquettes"
   ```
3. **Contrôle d'Intégrité Géométrique** : Vérifier que l'attribut `viewBox` est strictement préservé pour éviter tout décalage d'affichage dans les liseuses.
4. **Validation du Gain** : Enregistrer le différentiel de taille (octets gagnés) dans les logs.

---

## 🛡️ Règles & Garde-Fous Stricts
- **Préservation Visuelle** : Interdiction formelle de tronquer les coordonnées au point d'altérer la lisibilité des textes ou icônes.
- **Préservation des Identifiants** : Ne pas supprimer les `id` et classes CSS utilisés par les tests d'interaction.
- **Zéro Mutation Destructive** : Conserver une copie de sauvegarde si le fichier original n'est pas encore versionné dans Git.

## 🛡️ Résilience & Dégradation Gracieuse
Si l'outil SVGO ou le parser XML rencontre une erreur de syntaxe sur un fichier SVG mal formé, consigner l'erreur dans `memory/logs/` et ignorer ce fichier pour ne pas bloquer le traitement du lot.
