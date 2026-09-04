# ADR-0351 : Enforcement Déterministe du Grounding Visuel & Épistémique (OCR Ingestion, Gate FSM C9, Unification Nommage)

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-04
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Framework Backend mLoop, Convertisseur SVG (`src/converters/svg_to_md.py`, `src/converters/svg_ocr_bridge.py`), Machine à États (`src/pipelines/state_machine.py`), EvidencePack (`src/pipelines/evidence_pack.py`), Guardrail Pré-Vol (`src/pipelines/vibe_check.py`), Skills (`.agents/skills/grill/`, `.agents/skills/svg-ocr/`), Plugin Herdr (`plugins/mloop-herdr-plugin/tui_panes.py`)

---

## 1. Contexte & Problématique

Une session d'analyse de récit (`INC-004-BE`, projet BoireFrere_Segment2) a révélé que deux règles épistémiques constitutionnelles de mLoop — le **Contrat Visuel** (Maquettes = SSOT, AGENTS.md) et le **Dossier de Preuves Documentaires** (ADR-0320 §H, ADR-0326) — étaient exclusivement **déclaratives** (encodées dans des `SKILL.md`/ADR, obéies par bonne volonté de l'agent LLM) sans aucun **enforcement déterministe** dans le code Python.

Un audit factuel du code source (`src/`) a confirmé deux angles morts précis :

1. **OCR des SVG vectorisés orphelin** : le skill `.agents/skills/svg-ocr/` (rendu Chromium headless + `Windows.Media.Ocr` natif) existait et fonctionnait, mais n'était référencé nulle part dans le flux d'ingestion (`src/converters/svg_to_md.py`). Ce convertisseur détectait déjà le Mode 2 (SVG à texte vectorisé, aucune balise `<text>`/`<tspan>`) mais générait un placeholder muet (`"(Corps principal de la maquette)"`) au lieu d'invoquer l'OCR. Un agent tournant sur un modèle sans vision pouvait ainsi rédiger, valider et faire passer une story en `READY_FOR_DEV` sans jamais avoir lu le contenu textuel réel d'une maquette — en contradiction directe avec la règle « Maquettes = SSOT absolue ».

2. **Dossier de Preuves non enforced** : le seul contrôle logiciel existant (`struct_checker.py` Check C9) vérifiait uniquement l'*existence* d'un fichier disque, tournait en mode `strict=False` non-bloquant par défaut (`sync.py`), et n'était **jamais invoqué** par la Machine à États (`state_machine.py`) lors des transitions vers `READY_FOR_DEV`/`READY_FOR_GROOMING`. De plus, une divergence de nommage silencieuse existait entre le mode Herdr (`grill/SKILL.md` écrivait `<STORY_ID>_fact_search.md`) et le reste de l'écosystème (protocole normatif, gabarit, struct-check C9 : `<STORY_ID>_fact_dossier.md`) — un dossier produit en session Herdr échappait donc totalement au guardrail C9.

Cette ADR formalise la migration de ces deux garde-fous du registre **déclaratif** (prompt/skill) vers le registre **déterministe** (code testé, TDD Red-Green-Refactor).

---

## 2. Décisions d'Architecture

### 2.1 Diptyque de Grounding & Audit Épistémique

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│             DIPTYQUE DE GROUNDING — ENFORCEMENT VISUEL & ÉPISTÉMIQUE              │
├────────────────────────────────────────┬─────────────────────────────────────────┤
│ WHAT IT ACTUALLY PROVES                │ WHAT IT DOES NOT PROVE                  │
│ • Le pipeline d'ingestion invoque      │ • Ne garantit pas la disponibilité      │
│   automatiquement l'OCR sur tout SVG   │   de Chromium/Playwright ni de          │
│   Mode 2 (vectorisé), avec traçabilité │   Windows.Media.Ocr sur toute machine   │
│   is_vectorized/ocr_status persistée.  │   (dégradation gracieuse -> UNAVAILABLE)│
│ • Le gate C9 est désormais invoqué     │ • Ne bloque pas rétroactivement les     │
│   par la Machine à États (wikifix.py)  │   ~25 stories Module 1 déjà             │
│   à chaque cycle, pas seulement à la   │   READY_FOR_DEV sans dossier            │
│   demande explicite d'un `--strict`.   │   (WARNING non-bloquant en transition). │
│ • Le nommage `_fact_dossier.md` est    │ • Ne remplace pas le jugement humain    │
│   unifié partout (Herdr inclus),       │   sur la pertinence sémantique du       │
│   éliminant l'angle mort de contournement│  Dossier de Preuves (seule sa         │
│   du guardrail via le split-pane.      │   présence est vérifiée, pas son fond). │
├────────────────────────────────────────┴─────────────────────────────────────────┤
│ CLAIM BOUNDARIES                                                                 │
│ Cette ADR enforce la PRÉSENCE et la LECTURE des artefacts de grounding           │
│ (maquette OCR-isée, dossier de preuves existant), pas leur EXACTITUDE sémantique.│
│ Le jugement qualitatif reste la responsabilité du Grill / Rubber Duck / PO.      │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 AXE 1 — Pont OCR Déterministe à l'Ingestion (`svg_ocr_bridge.py`)

- **Nouveau module** `src/converters/svg_ocr_bridge.py` : encapsule `render_svg.js` (Chromium headless) + `ocr_png.ps1` (`Windows.Media.Ocr` natif) derrière une fonction pure `ocr_vectorized_svg(svg_path) -> Optional[str]`.
- **Contrat de dégradation gracieuse (non négociable)** : ne lève **jamais** d'exception. Toute indisponibilité (outil absent, timeout, plateforme non-Windows, `MLOOP_SVG_OCR=0`) retourne `None`.
- **Branchement dans `SvgSpatialParser`** : nouvel attribut `is_vectorized: bool`, positionné à `True` uniquement en Mode 2 (absence de `<text>`/`<tspan>`).
- **Branchement dans `parse_svg_to_md_text`** : si `is_vectorized`, invocation du pont OCR. Le texte extrait (si disponible) est injecté dans une section dédiée `## 🔍 Contrat Visuel — Texte Réel Extrait (OCR)` du Markdown ingéré ; sinon, avertissement explicite `⚠️ OCR indisponible`. Le frontmatter YAML trace `is_vectorized` et `ocr_status` (`DONE` | `UNAVAILABLE` | `N_A`).
- **Traçabilité EvidencePack** : `EvidencePackEngine._extract_visual_contract()` résout chaque source `.md` référencée par une story, détecte les spécifications UI ingérées (`document_type: "ui_specification"`), et matérialise un bloc `visual_contract: [{mockup_path, is_vectorized, ocr_status}]` — liste vide si aucune maquette n'est référencée (pas d'invention de contrat visuel pour une story headless).

### 2.3 AXE 2 — Gate C9 Réel sur la Machine à États

- **Nouvelle méthode** `StateMachineEngine.validate_fact_dossier_gate(story_file, strict=False)` : réutilise la logique de détection C9 (lien valide dans `## Références` ou fichier canonique `memory/evidence/<STORY_ID>_fact_dossier.md`), mais rattachée à la FSM plutôt qu'au seul rapport `struct-check` consultatif.
- **Sévérité en période de transition (décision actée avec le PO)** :
  - `strict=False` (défaut) : dossier manquant → `WARNING` via `ZeroFluffConsole`, la transition se poursuit (`return True`). Évite de bloquer rétroactivement les stories Module 1 déjà `READY_FOR_DEV` sans dossier historique.
  - `strict=True` (CI/audit explicite) : dossier manquant → `StateTransitionError` (BLOCKING).
- **Branchement dans `wikifix.py`** : à chaque audit de cohérence, pour tout récit en statut `READY_FOR_GROOMING`/`READY_FOR_DEV`/`IN_DEV`/`IN_QA`/`DONE`/`ACCEPTED`, `validate_fact_dossier_gate` est désormais invoqué systématiquement (aligné sur le pattern existant `validate_content_integrity`/`validate_sentinel_approval`), au lieu de dépendre exclusivement d'un `struct-check --strict` manuel.
- **Champ d'assentiment humain (traçable, non encore bloquant)** : `EvidencePack.socle_factuel_validated_by_human: bool` + `socle_factuel_validated_at: Optional[str]`, par défaut `False`/`None`. Réservé à une élévation future en `BLOCKING` une fois le flux de validation explicite outillé (hors périmètre de cette ADR).

### 2.4 Unification du Nommage Canonique `_fact_dossier.md`

- Correction de `grill/SKILL.md` (mode Herdr) : `<STORY_ID>_fact_search.md` → `<STORY_ID>_fact_dossier.md` (et son miroir `tools/export/grill-with-docs-kit/SKILL.md`).
- Correction de `plugins/mloop-herdr-plugin/tui_panes.py` : le glob de découverte cherche désormais en priorité `*_fact_dossier.md`, avec rétro-compatibilité en lecture seule sur l'ancien nom `*_fact_search.md` pour les dossiers déjà produits.

### 2.5 10ᵉ Contrôle Vibe-Check : « Contrat Visuel Lisible »

- Nouveau check dans `run_vibe_check()` (`src/pipelines/vibe_check.py`) : parcourt `docs/00-ingested/maquettes/*.md`, détecte les frontmatters `is_vectorized: true` sans `ocr_status: "DONE"`, et déclenche un `FAIL` (non-bloquant à ce stade — le score global du vibe-check inclut ce contrôle mais son échec n'interrompt pas le pipeline).

### 2.6 Arbitrage ADR-0320 §F.3 vs Gate Synchrone

ADR-0320 §F.3 autorise explicitement de différer/batcher la **validation mécanique** (`rubber-duck`, transition `READY_FOR_DEV`). Cette ADR **ne contredit pas** ce principe : le gate C9 introduit ici porte sur la **présence physique** du Dossier de Preuves (un contrôle structurel bon marché), pas sur la validation mécanique complète (`rubber-duck`, EvidencePack qualitatif) qui reste différable. Les deux gates sont orthogonaux et coexistent.

---

## 3. Conséquences

### Positives
- Un agent sans vision ne peut plus atteindre `READY_FOR_DEV` sur une story frontend référençant une maquette vectorisée sans qu'un signal (`ocr_status: UNAVAILABLE`, check Vibe-Check `FAIL`) ne le rende visible.
- Le Dossier de Preuves cesse de dépendre à 100% de la discipline de l'agent : la FSM elle-même émet un avertissement systématique, et un mode strict permet un audit CI bloquant.
- La divergence de nommage Herdr/non-Herdr est éliminée ; plus aucun dossier ne peut échapper silencieusement au guardrail.

### Risques / Négatifs
- Dépendance à Chromium (Playwright global) et `Windows.Media.Ocr` (Windows uniquement) pour l'OCR effectif — dégradation gracieuse obligatoire, jamais bloquante à l'ingestion.
- Le gate C9 reste en `WARNING` par défaut (non `BLOCKING`) : une régression volontaire pourrait passer inaperçue tant que le mode `strict` n'est pas exécuté explicitement. Ce compromis est assumé pour éviter de bloquer le Module 1 (25 stories déjà `READY_FOR_DEV`).
- Le champ `socle_factuel_validated_by_human` est déclaratif à ce stade (toujours `False` par défaut) : il ne constitue qu'une fondation pour un futur gate BLOCKING, pas encore un enforcement actif.

---

## 4. Alternatives Considérées

| Alternative | Rejetée car |
| :--- | :--- |
| Rendre le gate C9 `BLOCKING` immédiatement sur `READY_FOR_DEV` | Aurait cassé rétroactivement les ~25 stories Module 1 déjà validées sans dossier historique ; arbitré avec le PO en faveur d'une période de transition WARNING. |
| Utiliser un service OCR cloud (Google Vision, Azure Computer Vision) | Violerait la règle « Zéro Binaire Externe Non Configuré » (AGENTS.md) ; `Windows.Media.Ocr` est natif, gratuit, sans clé API. |
| Générer le Dossier de Preuves automatiquement par le code (template rempli mécaniquement) | Hors périmètre de cette ADR : le contenu sémantique du dossier (extraits verbatim, faits établis) requiert un jugement qualitatif de l'agent, non mécanisable sans risque de contenu creux/Goodhart. |

---

## 5. Références

- ADR-0320 : Grill-Me, Frontier Design Tree & Alignement Métier (§H Restitution Inconditionnelle, §F.3 Différé de validation mécanique).
- ADR-0326 : Fact-Search Obligatoire, Preuves Visibles en 4 Couches & Revue Sémantique.
- [`standards/protocols/DOSSIER_DE_PREUVES_PROTOCOL.md`](../protocols/DOSSIER_DE_PREUVES_PROTOCOL.md)
- [`.agents/skills/svg-ocr/SKILL.md`](../../.agents/skills/svg-ocr/SKILL.md)
- Tests : `tests/test_svg_ocr_bridge.py`, `tests/test_svg_spatial_parser.py`, `tests/test_evidence_pack.py`, `tests/test_state_machine_c9_gate.py`, `tests/test_vibe_check_visual_contract.py`.
