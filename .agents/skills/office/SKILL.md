---
name: office
description: "Manipulation chirurgicale de fichiers Microsoft Office (Word, Excel, PowerPoint) sans installation d'Office."
---

# Skill : Office Production (powered by OfficeCLI)


## Description
Permet à l'agent mLoop de manipuler directement des fichiers de la suite Microsoft Office (Word, Excel, PowerPoint) sans nécessiter l'installation d'Office.

## Capacités (Capabilities)
- **Extraction précise** : Lire des cellules spécifiques, des paragraphes ou des diapositives via un adressage DOM-like.
- **Édition opérationnelle** : Modifier du contenu existant ou créer des documents de zéro.
- **Rendu visuel (Look)** : Générer des aperçus HTML pour validation humaine (HITL).

## Commandes mLoop Tool
| Tool Name | Action | Paramètres |
| :--- | :--- | :--- |
| `office_read` | Lit le contenu d'un fichier | `file_path`, `query` (ex: "cell B4") |
| `office_write` | Modifie ou crée un fichier | `file_path`, `content`, `location` |
| `office_render` | Génère un aperçu HTML | `file_path`, `output_format` |

## Guardrails Stricts
1. **SSOT Protection** : Interdiction de transformer un document Office en source de vérité. Le Markdown reste le maître.
2. **Context Leak** : Toutes les opérations sont 100% locales (OfficeCLI binaire).
3. **HITL Required** : Toute modification de document "livrable" (client-facing) doit lever un flag de validation.
