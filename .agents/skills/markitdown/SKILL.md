---
name: markitdown
description: "Ingestion documentaire MarkItDown (PDF, Office, Images, Audio, HTML) vers Markdown normalisé. Use when converting raw binary documents, PDFs, or Office files into clean Markdown for ingestion."
---

# Skill : MarkItDown Ingestion (powered by microsoft/markitdown)


## Description
Permet à l'agent mLoop de convertir massivement divers formats de fichiers (PDF, Office, Images, Audio, HTML) en Markdown normalisé pour l'analyse sémantique et l'ingestion LLM.

## Capacités (Capabilities)
- **Conversion multi-format** : Transforme .pdf, .docx, .pptx, .xlsx, .zip, .html, .csv en Markdown.
- **Extraction structurelle** : Préserve les titres, listes, tableaux et liens dans le format Markdown de sortie.
- **Support Multimodal** : Capable de gérer des transcriptions audio et des descriptions d'images (si configuré avec un client LLM Vision).

## Commandes mLoop Tool
| Tool Name | Action | Paramètres |
| :--- | :--- | :--- |
| `markitdown_convert` | Convertit un fichier en Markdown | `input_path`, `output_path` (optionnel) |

## Guardrails Stricts
1. **Ingestion Only** : MarkItDown est un outil à sens unique (Ingestion). Ne jamais l'utiliser pour tenter de modifier un fichier binaire original.
2. **SSOT Feed** : Le Markdown produit doit être stocké dans `docs/00-ingested/` pour servir de matière première à la distillation, et les actifs visuels extraits (images, vecteurs) doivent être placés sous `docs/05-assets/` (ADR-0332).
