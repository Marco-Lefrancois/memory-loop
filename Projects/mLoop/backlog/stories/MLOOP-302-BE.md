---
id: MLOOP-302-BE
jira_key: ""
epic_key: EPIC-30-MULTIMODAL-ARTIFACT-HARNESS
type: Feature
title: "Filtre d'Ingestion Documentaire ORBIT pour Schémas d'Architecture (OrbitCaptionHarvester)"
tags: [core, ingest, orbit, captions, architecture, backend]
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by: []
created_at: "2026-09-25"
validated_by: Marco
validated_at: "2026-09-25T12:08:50.485909+00:00"

---

# Filtre d'Ingestion Documentaire ORBIT pour Schémas d'Architecture (OrbitCaptionHarvester)

---

## Description
**En tant qu'** Ingénieur Ingestion mLoop ou Modélisateur de Contexte,  
**je veux** que le pipeline d'ingestion documentaire découpe et ancre chaque schéma d'architecture extrait à l'aide de sa légende contextuelle (*caption*) et des paragraphes du texte qui le référencent (algorithme ORBIT),  
**afin d'** éliminer les extractions d'images orphelines sans sémantique et de garantir que la signification des flux architecturaux est fidèlement transmise aux agents d'analyse.

---

## Contexte & Périmètre

### Contexte Métier
Lors de l'ingestion de spécifications PDF ou Markdown complexes (dossiers d'architecture, briefs techniques), les extracteurs traditionnels découpent les images de manière brute sans conserver la légende ni le texte explicatif qui les entoure. L'étude ReFigBench a démontré que l'algorithme ORBIT (*Caption Harvesting*) permet d'atteindre une fidélité de reconstruction supérieure en associant intrinsèquement la figure à son libellé et à ses références amont/aval dans le texte.

### In-Scope
- Extension du pipeline d'ingestion dans `src/pipelines/ingest_file_processors.py` (strictement ≤ 300L, `RULE-AST-01`).
- Implémentation du composant `OrbitCaptionHarvester`.
- Extraction et ancrage contextuel des schémas : liaison déterministe entre l'image/diagramme extrait, sa légende (`Figure X: ...` ou libellé H3/H4 adjacent) et les 3 phrases amont/aval le citant.
- Génération d'une métadonnée d'ancrage normalisée sous `docs/00-ingested/` avec empreinte SHA-256 consolidée dans `source_manifest.json`.
- Filtrage des images décoratives : élimination des bannières, puces ou logos n'ayant aucune légende ni référence architecturale.

### Out-of-Scope
- Reconnaissance OCR intégrale du texte contenu dans l'image (couvert par `src/bridges/svg_ocr_bridge.py`).
- Modification des moteurs de lecture PDF bas niveau.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Moisson Contextuelle des Légendes et Figures (`harvest_orbit_figures`)
* **Entrée Métier** : Document technique brut (`document_path: Path`), flux textuel et liste des figures candidates.
* **Règles d'admissibilité & Validation** : Le document source doit être ingéré sous `docs/00-ingested/` et référencé dans le manifeste.
* **Traitement & Algorithme Métier** :
  1. Détection des blocs de figures et diagrammes.
  2. Localisation par regex sémantique des légendes associées (`Figure \d+`, `Diagramme \d+`, `Schéma : ...`).
  3. Recherche dans le texte des paragraphes d'appel citant la figure (`cf. Figure X`, `comme illustré sur la Figure X`).
  4. Création d'une fiche d'ancrage liant le fichier de figure à son bloc contextuel.
  5. Calcul et inscription du hash SHA-256 dans `source_manifest.json`.
* **Résultat Métier & Mutations** : Fiche d'ancrage `docs/00-ingested/<DOC>_figure_<ID>.json` et mise à jour de `source_manifest.json`.
* **Cas de Rejet Métier** : Figure décorative orpheline sans légende ni texte référent rejetée avec le statut `DECORATIVE_FIGURE_SKIPPED`.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- **Ingestion ORBIT CLI** : Intégrée dans `python src/swarm.py ingest --project <projet>`.
- **Méthode Python Locale** : `src.pipelines.ingest_file_processors:harvest_orbit_figures`.

#### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `harvest_orbit_figures` | `src.pipelines.ingest_file_processors:harvest_orbit_figures` | Extraction et ancrage contextuel figure/légende/paragraphe | `(doc_path: Path, figures: list) -> list[dict]` |
| `ingest --project` | `src.commands.handlers.project_ingest:handle_ingest` | Pipeline CLI d'ingestion documentaire avec moisson ORBIT | `(argparse.Namespace, LoopState, Path) -> int` |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-302-01** : Ce composant backend s'exécute dans le pipeline de prétraitement documentaire local (aucune interface HTTP/REST distante exposée). `[API de soumission à définir]` — toute exposition future via micro-service est reportée et à confirmer dans un récit dédié.

- **Admission of Limits & Résilience Système** :
  - **Absence de réseau / Timeout** : Pipeline d'ingestion 100 % local (in-memory / file system), insensible aux coupures réseau et timeouts distants (503/408).
  - **Concurrence & Anti-Rebond** : Protection contre les exécutions concurrentes ou invocations multiples rapides via écriture atomique dans `docs/00-ingested/` sans interblocage.
  - **Session & Authentification** : Composant headless sans session utilisateur ni token d'authentification (hors domaine 401/session expirée).
  - **Validation des Entrées Extrêmes** : Tout document vide (champ vide), fichier avec caractère spécial, métadonnée valeur null ou fichier binaire illisible est intercepté proprement et ignoré avec log d'anomalie sans crash.

---

## Règles d'affaires

- **Ancrage Contextuel Obligatoire** : Aucun schéma d'architecture ne peut être ingéré sous `docs/00-ingested/` sans sa légende ou son paragraphe explicatif associé.
- **Élimination du Bruit Décoratif** : Les images ne comportant aucun lien d'ancrage architectural sont écartées pour préserver la fenêtre de contexte de l'agent.
- **Traçabilité Immuable** : Chaque figure ancrée est scellée par son hash SHA-256 pour prévenir toute altération ultérieure.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-302-BE_fact_dossier.md`](../../memory/evidence/MLOOP-302-BE_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **ADR Projet** : [ADR-016 : Harnais de Fidélité Visuelle](../../docs/01-architecture/ADR-016_epic-30_harnais_fidelite_visuelle_et_integrite_artefacts_topologiques.md)
- 📜 **ADR Système** : [ADR-0392 : Standard Topologique des Artefacts](../../standards/adr-system/0392-harnais-fidelite-visuelle-integrite-artefacts-topologiques.md)
- 🔬 **Référence Scientifique** : *ReFigBench* (arXiv:2609.18844, Algorithme ORBIT).

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Filtre d'Ingestion Documentaire ORBIT pour Schémas d'Architecture (OrbitCaptionHarvester)

  # CHEMIN NOMINAL (Ancrage Réussi)
  Scénario: Ingestion réussie d'un schéma d'architecture avec sa légende et ses paragraphes d'appel
    Étant donné un document technique contenant un schéma "Figure 3 : Architecture Microservices"
    Et deux paragraphes dans le texte citant formellement la "Figure 3"
    Quand le filtre ORBIT exécute la moisson documentaire
    Alors le schéma est extrait sous docs/00-ingested/
    Et la légende ainsi que les paragraphes d'appel sont consolidés dans la fiche d'ancrage
    Et le manifeste source_manifest.json est mis à jour avec le hash SHA-256

  # EXCEPTIONS & REJETS MÉTIER (Image Décorative sans Contexte)
  Scénario: Élimination d'une image décorative sans légende ni référence
    Étant donné un document source comportant un logo ou une bannière visuelle isolée
    Sans légende explicite ni citation dans le corps du texte
    Quand le filtre ORBIT analyse le document
    Alors l'image est ignorée avec le statut "DECORATIVE_FIGURE_SKIPPED"
    Et aucun fichier polluant n'est ajouté au registre documentaire

  # RÉSILIENCE TECHNIQUE (Légende Ambigüe)
  Scénario: Résolution déterministe lors de références multiples à une même figure
    Étant donné un schéma d'architecture référencé dans plusieurs sections du document
    Quand le processeur ORBIT extrait les liens contextuels
    Alors la fiche d'ancrage agrège l'ensemble des contextes distincts sans troncature ni doublon

  # UX, OBSERVABILITÉ & LOGS (Bilan d'Ingestion)
  Scénario: Bilan de moisson dans la console lors de la commande ingest
    Étant donné la fin de l'ingestion d'un dossier documentaire
    Quand la moisson ORBIT s'achève
    Alors la console Zero-Fluff affiche le décompte exact des figures directrices ancrées et des images décoratives écartées
```