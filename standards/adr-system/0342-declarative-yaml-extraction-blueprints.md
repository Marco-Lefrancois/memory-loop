# ADR-0342 : Blueprints d'Extraction Déclarative YAML & Distillation de Connaissances Typées

## 🏛️ Statut
**Accepté** — Standard Normatif mLoop Core Architecture (29 août 2026)

---

## 🎯 Contexte & Problématique
Lors de la phase initiale d'un projet (`ingest` / `triage`), les documents clients bruts (cahiers des charges, spécifications Swagger/OpenAPI, règles de conformité, matrices de flux) sont convertis en Markdown sous `docs/00-ingested/` via MarkItDown (ADR-0101).

Cependant, la distillation de ces documents vers les répertoires SSOT structurés :
* `docs/02-business-rules/` (Règles métiers univoques)
* `docs/03-models/` (Modèles de données & entités DDD)
* Spécifications d'écrans & CTA

reposait sur des prompts de triage non typés et variables d'une session à l'autre. Inspiré par le standard de templates déclaratifs YAML de **Hyper-Extract** (80+ templates sectoriels), mLoop formalise un système d'extraction déclarative strictement typé.

---

## 💡 Décision Architecturale

### 1. Gabarits d'Extraction Déclaratifs (`standards/blueprints/extractors/`)
Nous introduisons le répertoire canonique `standards/blueprints/extractors/` contenant des spécifications YAML structurées définissant :
* Le schéma cible (champs, types, contraintes).
* Les motifs d'identification sémantique dans les documents sources.
* La stratégie de déduplication et de normalisation des clés (ex: `BR-001`, `MDL-001`, `API-001`).
* Le format de sortie cible dans `docs/`.

### 2. Catalogue Initial des Extracteurs mLoop
1. `extractor_business_rules.yaml` : Extrait les règles métiers, formules de calcul, contraintes d'intégrité et codes d'erreur normalisés vers `docs/02-business-rules/`.
2. `extractor_data_models.yaml` : Extrait les entités de domaine DDD, attributs, types primitifs/scalaires et relations d'agrégats vers `docs/03-models/`.
3. `extractor_api_contracts.yaml` : Extrait les routes, verbes HTTP, codes de statut, payloads JSON et headers requis.
4. `extractor_ui_matrix.yaml` : Extrait les composants d'écran, flux de navigation CTA et matrices d'état (8 états Hallmark).

### 3. Commande CLI Dédiée : `python src/swarm.py extract`
La commande `extract` permet de distiller de manière reproductible et déterministe tout document ingéré :
```bash
python src/swarm.py extract --project <nom_projet> --template <nom_template> --source <chemin_fichier> [--target <chemin_sortie>] [--format markdown|json]
```

### 4. Contrat d'Épistémie & Traçabilité (Raw-Source Authority)
Chaque entité extraite conserve obligatoirement son ancrage de source :
* Fichier source exact (`source_file`).
* Section ou paragraphe d'origine (`source_heading`).
* Indice de confiance d'extraction et timestamp.

---

## ⚖️ Conséquences & Impacts
* **Positif** : Standardisation absolue de la structure des règles métier (`docs/02-business-rules/`) et des modèles (`docs/03-models/`).
* **Positif** : Extraction 100% reproductible sans dérive lexicale ni hallucination de champs inexistants.
* **Positif** : Interopérabilité directe avec les agents d'implémentation (Renaud, Cursor, Copilot, OpenSpec).
