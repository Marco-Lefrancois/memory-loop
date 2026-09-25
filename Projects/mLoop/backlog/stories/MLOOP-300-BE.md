---
id: MLOOP-300-BE
jira_key: ''
epic_key: EPIC-30-MULTIMODAL-ARTIFACT-HARNESS
type: Enabler
title: Porte Déterministe d'Artefacts & Anti-Raster Paste pour Livrables Visuels (DeterministicArtifactGate)
tags:
- core
- gate
- artifacts
- safety
- backend
status: DONE_TESTED
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by: []
created_at: '2026-09-25'
ttl_cycles: 3
validated_by: Marco
validated_at: "2026-09-25T12:08:50.485909+00:00"

---

# Porte Déterministe d'Artefacts & Anti-Raster Paste pour Livrables Visuels (DeterministicArtifactGate)

---

## Description
**En tant qu'** Orchestrateur mLoop ou Responsable QA validant les livrables d'architecture et de maquettage,  
**je veux** disposer d'une porte de validation déterministe $g(P) \in \{0, 1\}$ qui contrôle l'ouverture du fichier, son unicité de rendu et l'absence d'usurpation par collage d'image raster brute (plafond maximal de 80 % de surface matricielle sans arêtes vectorielles éditables),  
**afin de** rejeter mécaniquement et immédiatement les faux artefacts produits par les agents avant toute consommation inutile de jetons par un juge ou relecteur LLM.

---

## Contexte & Périmètre

### Contexte Métier
Dans le cadre de l'Universal Dev Handoff, mLoop certifie la conformité des artefacts d'architecture (diagrammes Archify, schémas vectoriels SVG, toiles Canvas) transmis aux ingénieurs et aux agents d'implémentation avals. L'étude scientifique ReFigBench (arXiv:2609.18844) a démontré que les LLMs ont une propension systémique à simuler la complétude visuelle d'un schéma complexe en incrustant une capture bitmap (PNG/JPEG) plate en lieu et place d'un véritable graphe vectoriel éditable. La porte déterministe agit comme un coupe-circuit binaire infranchissable en amont des revues cognitives.

### In-Scope
- Implémentation du module `src/pipelines/artifact_gate.py` (strictement ≤ 300L, `RULE-AST-01`).
- Moteur d'évaluation déterministe `evaluate_artifact_gate(file_path: Path) -> ArtifactGateResult`.
- Contrôle d'ouverture (*Openability*) : vérification de bonne formation syntaxique XML/SVG ou JSON sans corruption.
- Règle de canvas unique (*Single-Artifact Constraint*) : présence d'exactement un schéma ou canvas principal sans prolifération anarchique de calques invisibles.
- Détection Anti-Raster Paste : calcul déterministe du ratio de surface couverte par des balises `<image>` ou données matricielles base64 (`image/png`, `image/jpeg`, `image/webp`) par rapport au `viewBox` global. Rejet strict si ratio > 80 % en l'absence d'arêtes ou nœuds vectoriels (`path`, `rect`, `polygon`, `circle`).
- Émission du motif standardisé `RASTER_PASTE_DETECTED` ou `CORRUPT_ARTIFACT`.

### Out-of-Scope
- Vectorisation ou re-génération automatique du schéma rejeté.
- Audit sémantique qualitatif du texte ou des polices de caractères.
- Traitement de formats propriétaires binaires non documentés (ex. Photoshop `.psd`).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend)*
#### 1. Évaluation Déterministe d'Intégrité de Fichier (`evaluate_artifact_gate`)
* **Entrée Métier** : Chemin de fichier (`file_path: Path`), type MIME attendu ou détecté, tolérance optionnelle.
* **Règles d'admissibilité & Validation** : Le fichier doit exister sur disque, être accessible en lecture et posséder une extension reconnue (`.svg`, `.html`, `.json`).
* **Traitement & Algorithme Métier** :
  1. Parsing structurel sécurisé (DOM XML sandboxed via defusedxml ou parser AST standard sans exécution de scripts).
  2. Calcul de l'aire du `viewBox` ou des dimensions du canvas.
  3. Somme des aires des éléments graphiques matriciels (`<image>`, data-URI base64).
  4. Comptage des éléments vectoriels géométriques éditables (`<path>`, `<rect>`, `<circle>`, `<line>`, etc.).
  5. Si l'aire matricielle dépasse 80 % de l'aire totale et que le compte d'éléments vectoriels est inférieur à 3, l'évaluation bascule à invalide ($g(P) = 0$).
* **Résultat Métier & Mutations** : Objet `ArtifactGateResult(is_valid: bool, reason: str, raster_ratio: float, vector_elements_count: int, checksum: str)`.
* **Cas de Rejet Métier** : Rejet binaire avec code `RASTER_PASTE_DETECTED` pour usurpation bitmap, ou `CORRUPT_ARTIFACT` si le document est mal formé.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- **Évaluation Déterministe Locale** : Fonction Python locale `src.pipelines.artifact_gate:evaluate_artifact_gate`.
- **Intégration CLI** : Invocable directement via `python src/swarm.py artifact-check --file <path>`.

#### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `evaluate_artifact_gate` | `src.pipelines.artifact_gate:evaluate_artifact_gate` | Évaluation déterministe locale de conformité d'artefact vectoriel | `(file_path: Path) -> ArtifactGateResult` |
| `handle_artifact_check` | `src.commands.handlers.artifact_check:handle_artifact_check` | Commande CLI d'audit unitaire ou global | `(argparse.Namespace, LoopState, Path) -> int` |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-300-01** : Ce composant backend opère exclusivement en local en CLI et pipeline interne (aucune interface HTTP/REST distante exposée). `[API de soumission à définir]` — toute exposition future via micro-service est reportée et à confirmer dans un récit dédié.

- **Admission of Limits & Résilience Système** :
  - **Absence de réseau / Timeout** : Composant 100 % local (in-memory / file system), insensible aux timeouts réseau et indisponibilités distantes (503/408).
  - **Concurrence & Anti-Rebond** : Protection contre les exécutions concurrentes ou invocations multiples rapides via isolation de lecture-seule sans verrou bloquant.
  - **Session & Authentification** : Composant headless sans session utilisateur ni token d'authentification (hors domaine 401/session expirée).
  - **Validation des Entrées Extrêmes** : Tout fichier vide (champ vide), chemin avec caractère spécial, valeur null ou payload corrompu est intercepté proprement et renvoie `is_valid = Faux` avec code `CORRUPT_ARTIFACT`.

---

## Règles d'affaires

- **Seuil Infranchissable de Raster Paste** : Tout livrable contenant plus de 80 % de surface couverte par des images matricielles sans connecteurs ni boîtes vectorielles déclarées est rejeté de manière binaire ($g(P) = 0$).
- **Frugalité d'Inférence LLM** : Tout artefact échouant à la porte déterministe est bloqué immédiatement ; aucune invocation d'agent Sentinel ni de relecture LLM n'est autorisée sur un fichier en échec $g(P) = 0$.
- **Résilience Déterministe** : Tout fichier corrompu, tronqué ou illisible renvoie un résultat négatif propre sans faire planter le processus parent (`Zero Crash Policy`).

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-300-BE_fact_dossier.md`](../../memory/evidence/MLOOP-300-BE_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 📜 **ADR Projet** : [ADR-016 : Harnais de Fidélité Visuelle & Intégrité des Artefacts Topologiques](../../docs/01-architecture/ADR-016_epic-30_harnais_fidelite_visuelle_et_integrite_artefacts_topologiques.md)
- 📜 **ADR Système** : [ADR-0392 : Standard Topologique des Artefacts](../../standards/adr-system/0392-harnais-fidelite-visuelle-integrite-artefacts-topologiques.md)
- 🔬 **Référence Scientifique** : *ReFigBench: Benchmarking Scientific Figure Reconstruction as Editable PowerPoint Artifacts* (arXiv:2609.18844, Section 3).

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Porte Déterministe d'Artefacts & Anti-Raster Paste (DeterministicArtifactGate)

  # CHEMIN NOMINAL (Happy Path & Validation Vectorielle)
  Scénario: Validation avec succès d'un schéma d'architecture vectoriel éditable
    Étant donné un fichier SVG d'architecture généré par Archify comportant 6 composants vectoriels et 5 connecteurs
    Et que la surface occupée par des images matricielles est de 0 %
    Quand la porte déterministe evaluate_artifact_gate est exécutée sur le fichier
    Alors le résultat indique is_valid = Vrai
    Et la raison est "ARTIFACT_CONFORME"
    Et le ratio raster calculé est inférieur à 0.80

  # EXCEPTIONS & REJETS MÉTIER (Anti-Raster Paste)
  Scénario: Rejet binaire immédiat d'un schéma usurpé par un collage d'image PNG
    Étant donné un fichier SVG contenant une balise image couvrant 95 % du viewBox
    Et ne contenant aucun connecteur vectoriel ni boîte déclarative
    Quand la porte déterministe evaluate_artifact_gate est exécutée sur le fichier
    Alors le résultat indique is_valid = Faux
    Et le motif d'échec est "RASTER_PASTE_DETECTED"
    Et aucun appel au moteur de relecture cognitive n'est déclenché

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Fichier Corrompu)
  Scénario: Rejet propre d'un livrable corrompu ou syntaxiquement invalide
    Étant donné un fichier d'artefact tronqué ou contenant un balisage XML invalide
    Quand la porte déterministe analyse le document
    Alors la fonction intercepte l'erreur sans lever d'exception non gérée
    Et le résultat indique is_valid = Faux avec le motif "CORRUPT_ARTIFACT"

  # UX, OBSERVABILITÉ & LOGS (Traçabilité Déterministe)
  Scénario: Journalisation structurée des métriques d'intégrité de l'artefact
    Étant donné l'évaluation d'un artefact soumis à la porte
    Quand l'analyse géométrique et syntaxique s'achève
    Alors un journal structuré consigne l'empreinte SHA-256, le ratio raster et le décompte vectoriel
    Et les métriques sont restituées dans la console Zero-Fluff
```