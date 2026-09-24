---
name: markitdown
description: "Ingestion documentaire multi-formats vers Markdown normalisé sous docs/00-ingested/ et extraction d'assets vers docs/05-assets/. Use when converting office documents, PDFs, presentations, audio, or images into normalized Markdown for analysis or ingestion."
---

# Skill : MarkItDown Ingestion (powered by microsoft/markitdown)

## Description
Permet à l'agent mLoop de convertir massivement divers formats de fichiers (PDF, Office, Images, Audio, HTML) en Markdown normalisé pour l'analyse sémantique et l'ingestion LLM dans le respect strict des 5 Phases du cycle de vie (ADR-0375) et des normes de Phase 1 (ADR-0378).

## Capacités (Capabilities)
- **Conversion multi-format** : Transforme .pdf, .docx, .pptx, .xlsx, .zip, .html, .csv en Markdown normalisé.
- **Extraction structurelle** : Préserve les titres (#, ##, ###), listes, tableaux et liens dans le format Markdown de sortie.
- **Support Multimodal & Visuel** : Découplage des maquettes vectorielles et schémas vers `docs/05-assets/` (ADR-0332).
- **Source Manifest & Grounding** : Enregistrement déterministe avec hachage SHA-256 dans `docs/00-ingested/source_manifest.json` (ADR-0335).

## Commandes mLoop Tool
| Tool Name | Action | Paramètres |
| :--- | :--- | :--- |
| `markitdown_convert` | Convertit un fichier en Markdown | `input_path`, `output_path` (optionnel) |

## Guardrails Stricts
1. **Ingestion Only** : MarkItDown est un outil à sens unique (Ingestion). Ne jamais l'utiliser pour tenter de modifier un fichier binaire original.
2. **SSOT Feed & Isolation Visuelle** : Le Markdown produit doit être stocké sous `docs/00-ingested/` pour servir de matière première à la distillation, et les actifs visuels extraits (images, vecteurs) doivent être placés sous `docs/05-assets/` (ADR-0332).
3. **Interdiction de Stories (Check 13 / Anti-Ghost-Bias)** : En Phase 1 (`STAGE_1_INGEST`), aucune story ne doit être créée dans `backlog/stories/`.

## 🛡️ Résilience & Dégradation Gracieuse
Si un fichier binaire est corrompu, protégé par mot de passe ou non pris en charge par MarkItDown, consigner l'erreur dans `docs/00-ingested/source_manifest.json` avec statut d'échec explicite et poursuivre l'ingestion des autres documents sans interrompre le lot.
