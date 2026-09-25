---
id: MLOOP-354-FULL
jira_key: ''
epic_key: EPIC-35-REFIGBENCH-ARTIFACT-HARNESS-V2
type: Feature
title: Extension CLI mloop artifact-check 5x, Enrichissement Vibe-Check Check 27 & EvidencePack 2.0
tags:
- cli
- artifacts
- vibe-check
- evidence-pack
- fullstack
status: DRAFT
grill_me: PENDING
invest_score: 6/6
layer: fullstack
macrostructure: workbench
blocked_by:
- MLOOP-350-BE
- MLOOP-351-BE
- MLOOP-352-BE
- MLOOP-353-BE
created_at: '2026-09-25'
ttl_cycles: 3
---

# Extension CLI mloop artifact-check 5x, Enrichissement Vibe-Check Check 27 & EvidencePack 2.0

---

## Description
**En tant qu'** Ingénieur Logiciel ou Agent Orchestrateur mLoop qualifiant un sprint (Phase 4 : Validate & QA),  
**je veux** exécuter la commande CLI `mloop artifact-check --file <path> --rubric-5x`, bénéficier du Check 27 enrichi dans le Vibe-Check pré-vol, et consigner le certificat 5-axes dans le sidecar EvidencePack 2.0 JSON,  
**afin d'** interdire mécaniquement la promotion d'artefacts défaillants et certifier avec une rigueur absolue la conformité topologique et causale de tous les schémas produits par mLoop.

---

## Contexte & Périmètre

### Contexte Métier
Ce récit finalise l'intégration de ReFigBench dans mLoop en fournissant l'interface opérateur unifiée (CLI), la barrière de qualification automatique en phase pré-vol (Check 27 du Vibe-Check), et le scellement des preuves de conformité dans l'EvidencePack 2.0 (conformément à l'ADR-0394). L'équipe dispose ainsi d'un garde-fou industriel infalsifiable.

### In-Scope
- Handler de commande CLI étendu `src/commands/handlers/artifact_check_v2.py` (strictement $\le 300$L, `RULE-AST-01`).
- Commande CLI :
  `python src/swarm.py artifact-check [--file <chemin>] [--project <nom>] [--rubric-5x] [--format json|text]`.
- Enrichissement du **Check 27 dans Vibe-Check** (`src/pipelines/vibe_check.py`) :
  - Exécute la porte déterministe binaire $g(P)$ (`artifact_gate.py`).
  - Exécute l'audit d'arbre d'objets natifs (`object_tree_auditor.py`).
  - Exécute le linter matriciel d'inversion causale (`causal_flow_linter.py`).
  - Calcule la note finale sur 100 via la grille 5-axes (`audit_decoupler.py`).
  - Déclare `FAIL` si le score global est $< 85$ ou si une inversion causale est détectée.
- Scellement du bloc `refigbench_audit` dans `memory/evidence/<STORY_ID>_evidence.json` (EvidencePack 2.0).
- Restitution graphique en console (Rich Table avec barres de progression pour chaque axe $T, S, L, E, V$).

### Out-of-Scope
- Rendu d'animation vidéo.
- Modification des seuils sans passer par un amendement d'ADR.

---

## Critères d'acceptation

### Spécifications de l'Interface & UX *(fullstack)*
- **Affichage Console Évolué** : Affichage d'un tableau récapitulatif présentant les 5 axes $T/20$, $S/30$, $L/15$, $E/25$, $V/10$, l'indicateur d'intégrité causale (`CONFORME` ou `INVERSION DÉTECTÉE`), et le badge final (`CERTIFIÉ QA` en vert ou `REJET ÉLIMINATOIRE` en rouge).
- **Sortie Machine JSON** : Restitution de la charge utile complète avec les identifiants d'objets audités.

### Opérations Métier & Logique Backend *(fullstack)*
#### 1. Traitement Global de Qualification d'Artefact (`handle_artifact_check_v2`)
* **Entrée Métier** : Argumentaire CLI parsé (fichier, projet, option `--rubric-5x`).
* **Règles d'admissibilité & Validation** : Le fichier cible doit exister et être un livrable reconnu.
* **Traitement & Algorithme Métier** :
  1. Passage par la porte déterministe $g(P)$.
  2. Extraction de l'arbre d'objets natifs.
  3. Confrontation matricielle d'adjacence causale.
  4. Calcul de la note 5-axes.
  5. Écriture atomique dans l'EvidencePack JSON associé.
* **Résultat Métier & Mutations** : Code retour 0 si certifié, 1 si rejet.
* **Cas de Rejet Métier** : Sortie avec code 1 en cas d'inversion causale ou de score inférieur à 85.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
- `src.commands.handlers.artifact_check_v2:handle_artifact_check_v2(args, state, project_path) -> int`
- `src.pipelines.vibe_check:check_multimodal_artifact_integrity_v2(project_path: Path) -> tuple[bool, str]`

#### Matrice des Contrats API
| Méthode | Route / Point d'Entrée | Finalité | Contrat |
| :--- | :--- | :--- | :--- |
| `handle_artifact_check_v2` | `src.commands.handlers.artifact_check_v2:handle_artifact_check_v2` | Audit CLI 5-axes d'artefact | `(args, state, project_path) -> int` |
| `check_multimodal_artifact_integrity_v2` | `src.pipelines.vibe_check:check_multimodal_artifact_integrity_v2` | Check 27 enrichi dans Vibe-Check | `(project_path: Path) -> tuple[bool, str]` |

---

## Règles d'affaires

- **Intransigeance de la Certification QA** : Aucun récit comportant un livrable d'architecture ne peut franchir la Gate 4 (`QA_CERTIFIED`) sans certificat 5-axes scellé dans son EvidencePack.
- **Transparence d'Inversion** : En cas d'inversion causale, la commande CLI doit explicitement nommer les deux nœuds et la direction attendue.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves** : [`memory/evidence/EPIC-35_refigbench_fact_dossier.md`](../../memory/evidence/EPIC-35_refigbench_fact_dossier.md)
- 📄 **Publication de Référence** : ReFigBench (*arXiv:2609.18844*).

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Guide CLI Pipeline** : [`standards/protocols/CLI_PIPELINE_GUIDE.md`](../../standards/protocols/CLI_PIPELINE_GUIDE.md)
- 📜 **ADR Associé** : [ADR-0396](../../standards/adr-system/0396-audit-artefacts-5-axes-et-anti-inversion-causale-refigbench.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Extension CLI mloop artifact-check 5x & Vibe-Check Check 27

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Audit CLI complet d'un schéma d'architecture avec note 5-axes certifiée
    Étant donné un schéma SVG valide conforme à l'architecture
    Quand l'utilisateur lance "python src/swarm.py artifact-check --file schema.svg --rubric-5x"
    Alors la commande s'exécute avec succès et retourne le code 0
    Et le tableau console affiche les scores T=19, S=29, L=14, E=24, V=9 avec total 95/100
    Et l'EvidencePack JSON est enrichi du certificat d'audit scellé

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Rejet CLI lors de l'analyse d'un schéma comportant une flèche inversée
    Étant donné un diagramme où une dépendance essentielle a été inversée
    Quand la commande d'audit est déclenchée
    Alors la sortie affiche une alerte rouge "CAUSAL_FLOW_INVERSION_DETECTED"
    Et la note S est à 0 et le code de sortie est 1
    Et le statut final indique "REJET ÉLIMINATOIRE"

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Timeouts, Idempotence, Concurrence)
  Scénario: Blocage du Vibe-Check Check 27 sur défaillance d'intégrité d'un livrable
    Étant donné un projet contenant un livrable d'architecture non certifié
    Quand la sonde Vibe-Check exécute le Check 27
    Alors le résultat global est "vibe-check FAIL"
    Et la transition de story vers READY_FOR_DEV ou QA_CERTIFIED est bloquée

  # UX, OBSERVABILITÉ & EMPTY STATE (Spinners, Retours Écran, Logs)
  Scénario: Restitution d'un rapport JSON complet pour intégration pipeline CI/CD
    Étant donné une exécution avec "--format json"
    Quand le flux de sortie est analysé
    Alors le JSON contient les sous-scores, le ratio matriciel et le hash SHA-256 de l'artefact
```
