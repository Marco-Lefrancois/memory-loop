---
id: MLOOP-040-BE
jira_key: '-'
epic_key: EPIC-5-INGESTION-OFFICE
type: Feature
title: Pipeline MarkItDown et Conversion Locale Sandboxed Anti-Doublons
tags: [ingest, markitdown, conversion, sandbox, sha256, adr-0101]
status: SHIPPED
layer: backend
invest_score: 6/6
macrostructure: "workbench"
---
# [EPIC-5-INGESTION-OFFICE] Pipeline MarkItDown et Conversion Locale Sandboxed (MLOOP-040-BE)

---

## Description
**En tant qu'** Agent d'Ingestion ou Développeur alimentant la base de connaissances du projet,  
**je veux** disposer d'un pipeline local et sandboxed de conversion multimodale (`MarkItDownPipeline`) avec registre persistant SHA-256,  
**afin de** convertir en Markdown standardisé les documents bruts (PDF, Office, texte) déposés dans `reference/` sans dépendance réseau externe et sans retraitement redondant.

---

## Contexte & Périmètre

### Contexte Métier
Conformément à l'ADR-0101, mLoop abandonne toute dépendance à des services RAG distants pour l'ingestion initiale. Les documents clients déposés dans `reference/` sont convertis localement en Markdown dans `docs/00-ingested/`. Le pipeline vérifie l'empreinte cryptographique SHA-256 dans `memory/ingest_registry.json` pour garantir l'idempotence et la performance.

### In-Scope
- Composant `MarkItDownPipeline` dans `src/converters/markitdown_converter.py`.
- Calcul d'empreinte SHA-256 et registre persistant `memory/ingest_registry.json`.
- Conversion multimodale locale avec mécanisme de fallback résilient pour fichiers texte/données.
- Injection de frontmatter YAML enrichi dans le markdown produit.
- Traitement unitaire (`convert_file`) et par lot (`convert_directory`).
- Suite de tests unitaire dédiée dans `tests/test_markitdown_pipeline.py`.

### Out-of-Scope
- Affichage visuel bureautique ou rendu HTML (élagué selon TOMBSTONE ADR-0362).

---

## Maquettes & Diagrammes

```mermaid
flowchart LR
    A[Fichier Brut: reference/*.pdf, *.docx, *.txt] --> B[MarkItDownPipeline]
    B --> C{SHA-256 dans ingest_registry.json?}
    C -->|Oui - Déjà traité| D[Retour Fichier Existant (Idempotence)]
    C -->|Non - Nouveau| E[Extraction Locale Sandboxed]
    E --> F[Génération Frontmatter YAML]
    F --> G[docs/00-ingested/*.md]
    G --> H[Mise à jour ingest_registry.json]
```

---

## Spécifications & Contrats d'Interface

### Classes & Méthodes Backend
- `MarkItDownPipeline(project_path: Path)` : Constructeur lié au projet cible.
- `convert_file(file_path: Path, output_dir: Path = None) -> Path` : Conversion unitaire sandboxed avec registre SHA-256.
- `convert_directory(input_dir: Path, output_dir: Path = None) -> List[Path]` : Traitement par lot.

---

## Critères d'acceptation

### Règles d'affaires

- **RM-001 Détection Anti-Doublons Déterministe** : Tout document dont le hash SHA-256 est déjà répertorié dans `memory/ingest_registry.json` ne doit pas être réextrait; le chemin du fichier markdown existant est immédiatement renvoyé.
- **RM-002 Confinement Sandboxed Local** : La conversion doit s'exécuter intégralement en local sans aucun appel réseau ou service externe.
- **RM-003 Frontmatter YAML Enrichi** : Chaque document Markdown généré sous `docs/00-ingested/` doit contenir un frontmatter YAML déclarant le nom de la source, la date de conversion et l'empreinte SHA-256.

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Pipeline MarkItDown et Conversion Locale Sandboxed

  # CHEMIN NOMINAL
  Scénario: Conversion locale réussie d'un nouveau document texte brut
    Étant donné un document source présent dans reference sans empreinte préalable
    Quand le pipeline de conversion MarkItDown traite le fichier
    Alors un document Markdown enrichi est généré dans docs/00-ingested
    Et le hash SHA-256 est consigné dans memory/ingest_registry.json

  # EXCEPTIONS & REJETS MÉTIER
  Scénario: Détection et court-circuit d'un fichier déjà ingéré
    Étant donné un document source dont l'empreinte SHA-256 figure déjà au registre
    Quand la conversion du fichier est à nouveau sollicitée
    Alors le pipeline réutilise le markdown existant sans recalcul
    Et aucune nouvelle écriture redondante n'est effectuée

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ
  Scénario: Résilience face à un format non pris en charge
    Étant donné un fichier binaire inconnu ou corrompu
    Quand le pipeline tente la conversion
    Alors une exception contrôlée ou un retour d'échec propre est journalisé
    Et le registre anti-doublons demeure intègre

  # UX, OBSERVABILITÉ & EMPTY STATE
  Scénario: Traitement d'un répertoire d'ingestion vide
    Étant donné un répertoire source ne contenant aucun document admissible
    Quand la conversion de répertoire est lancée
    Alors la liste retournée est vide sans provoquer d'erreur système
```
