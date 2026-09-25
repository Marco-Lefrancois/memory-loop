---
created: 2026-09-04T13:11:33.327Z
source: plannotator
tags: [plannotator, memory-loop, impl, mentation, framework]
---

[[Plannotator Plans]]

# Plan d'Implémentation Framework — Enforcement Déterministe du Grounding Visuel & Épistémique

## Objectif
Faire migrer 2 règles épistémiques mLoop du **déclaratif (SKILL.md/ADR, obéi par bonne volonté)** vers le **déterministe (code Python, enforced)** :
1. **AXE 1** — OCR des SVG vectorisés intégré au pipeline (fin de l'angle mort « maquette illisible »).
2. **AXE 2** — Dossier de Preuves : unification du nommage + gate FSM réel avant `READY_FOR_DEV`.

**Cadre** : Auto-développement framework (`C:\Memory Loop\src`, seule exception au boundary code). Criticité Niveau 3. Méthode **TDD Red-Green-Refactor** (skill `tdd`), tests existants : `tests/test_struct_checker.py`, `tests/test_svg_spatial_parser.py`, `tests/test_evidence_pack.py`.

---

## 🔴 PHASE 0 — Quick-Win : Faille C (bug de nommage silencieux)
**Problème** : mode Herdr écrit/cherche `_fact_search.md` (`grill/SKILL.md:43`, `plugins/mloop-herdr-plugin/tui_panes.py:108`) alors que tout le reste (protocole §4.1, gabarit, `struct_checker.py:532` C9, `story_template.md:86`) impose `_fact_dossier.md`. → un dossier Herdr **échappe** au guardrail C9.

**Action** : Trancher le nom canonique **`_fact_dossier.md`** partout.
- Éditer `grill/SKILL.md:43` : `_fact_search.md` → `_fact_dossier.md`.
- Éditer `plugins/mloop-herdr-plugin/tui_panes.py:108` : glob `*_fact_search.md` → `*_fact_dossier.md` (vérifier rétro-compat : accepter les deux en lecture, n'écrire que le canonique).
- Vérif : `grep -r fact_search.md` doit ne plus retourner que des lectures rétro-compatibles.
**Risque** : Faible (Type 2 réversible). Aucun test cassé attendu.

---

## 🔴 PHASE 1 — AXE 1 : OCR des SVG vectorisés à l'ingestion
**Problème** : `svg_to_md.py:193-195` détecte le Mode 2 (vectorisé, `<path>` only) mais génère un placeholder `(Corps principal de la maquette)` (ligne 519) au lieu d'extraire le texte. Le skill `svg-ocr` (render_svg.js + ocr_png.ps1) existe mais n'est **jamais invoqué par le code**.

### 1.1 — Extraction du service OCR réutilisable
- Créer `src/converters/svg_ocr_bridge.py` : fonction `ocr_vectorized_svg(svg_path) -> str | None` qui encapsule l'appel à `render_svg.js` (Chromium headless) puis `ocr_png.ps1` (Windows.Media.Ocr), avec timeout et dégradation gracieuse (retourne `None` si Chromium/OCR indisponible — ex: CI Linux).
- **Test RED** (`tests/test_svg_ocr_bridge.py`) : mock des sous-process, vérifie parsing sortie OCR + fallback `None` propre si outils absents.

### 1.2 — Branchement dans le convertisseur (Mode 2)
- Dans `svg_to_md.py`, au Mode 2 (ligne 195) : tenter `ocr_vectorized_svg()`. Si texte obtenu → l'injecter dans le `.md` ingéré (au lieu du placeholder). Si `None` → conserver le placeholder actuel MAIS marquer un flag `ocr_status: FAILED|UNAVAILABLE` dans un sidecar.
- **Garde-fou perf** : OCR uniquement si Mode 2 confirmé (jamais sur SVG `<text>`). Désactivable via variable d'env `MLOOP_SVG_OCR=0`.
- **Test RED** : SVG vectorisé fixture → assert texte OCR présent (ou placeholder + flag si OCR mocké indisponible).

### 1.3 — Traçabilité EvidencePack
- Ajouter au schéma `evidence_pack.py` un bloc `visual_contract` : `{ mockup_path, is_vectorized: bool, ocr_status: NONE|DONE|FAILED|N_A, ocr_source }`.
- **Test RED** (`tests/test_evidence_pack.py`) : build d'un pack avec maquette vectorisée → assert présence + valeurs du bloc `visual_contract`.
**Risque** : Moyen (dépendance Chromium/OCR Windows). Mitigation : dégradation gracieuse obligatoire, jamais bloquant à l'ingestion.

---

## 🔴 PHASE 2 — AXE 2 : Gate FSM réel + preuve d'assentiment
**Problème** : la transition `→ READY_FOR_DEV` (`state_machine.py:40-42`) n'invoque **jamais** C9. `struct-check` tourne en `strict=False` non-bloquant (`sync.py:333`). → on atteint `READY_FOR_DEV` sans dossier.

### 2.1 — Gate C9 bloquant sur transition critique
- Dans `state_machine.py` `validate_transition` : quand la cible ∈ `{READY_FOR_DEV, READY_FOR_GROOMING}`, invoquer `_check_c9_fact_dossier_presence(strict=True)`. Si violation BLOCKING → lever `StateTransitionError` explicite (dossier manquant/lié brisé).
- **Test RED** (`tests/test_state_machine.py` ou `test_struct_checker.py`) : transition vers READY_FOR_DEV sans dossier → assert `StateTransitionError` ; avec dossier valide → passe.

### 2.2 — Champ d'assentiment humain
- Ajouter dans l'EvidencePack : `socle_factuel_validated_by_human: bool` + `validated_at` (timestamp). C9 en mode strict exige `true` avant READY_FOR_DEV (au-delà de la simple existence fichier).
- **Test RED** : dossier présent mais `validated_by_human=false` → WARNING (non bloquant phase 2) ; documenter l'élévation future en BLOCKING.

### 2.3 — Ancrage documentaire (cohérence SSOT)
- Mettre à jour `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` (règle Contrat Visuel) : référencer `svg-ocr` + le gate C9. **Parité miroir obligatoire** (vibe-check check #1).
- Ajouter le critère « Contrat Visuel Lisible » comme 10ᵉ contrôle `vibe_check.py` (WARNING) : story `frontend|fullstack` référençant un SVG vectorisé sans `ocr_status: DONE` consigné.

---

## 🟡 PHASE 3 — ADR & Calibrage
- Rédiger l'ADR « Enforcement Déterministe du Grounding Visuel & Épistémique » via `python src/swarm.py grill --title ... --context ... --decision ...` (Type 1 : touche schéma EvidencePack + FSM + contrat nommage → remplit les 3 filtres ADR).
- **Arbitrage ADR requis** : trancher la tension **ADR-0320 §F.3** (autorise de différer la validation mécanique) vs **gate synchrone dur** avant READY_FOR_DEV. Décision proposée : gate dur sur transition READY_FOR_DEV, mais validation mécanique (`rubber-duck`) reste différable — les deux ne portent pas sur le même objet.
- `python src/swarm.py calibrate` pour synchroniser `adr-contracts.json` et vérifier la parité miroir.

---

## ✅ Validation finale (Definition of Done)
1. `python -m pytest tests/ -q` — tous les tests verts (existants + nouveaux).
2. `python src/swarm.py vibe-check --project BoireFrere_Segment2` — 11/11 maintenu (+ nouveau check éventuel).
3. `python src/swarm.py calibrate` — parité miroir AGENTS/CLAUDE/GEMINI OK, adr-contracts à jour.
4. `grep -r _fact_search.md src/ plugins/ .agents/` — zéro écriture divergente résiduelle.

---

## Ordre d'exécution & points de contrôle
1. **PHASE 0** (quick-win nommage) → commit isolé.
2. **PHASE 1** (OCR ingestion) → TDD, commit.
3. **PHASE 2** (gate FSM) → TDD, commit.
4. **PHASE 3** (ADR + calibrate) → commit.

Chaque phase est un incrément testable et commité séparément. **Aucune modification de `src/` ne démarre avant approbation de ce plan.** Commits uniquement sur demande explicite.

## Questions ouvertes avant démarrage
- **Q1 — Périmètre** : On traite les 3 phases (0+1+2+3), ou on commence par un sous-ensemble (ex: Phase 0+2 sans l'OCR, plus risqué en dépendances) ?
- **Q2 — Sévérité gate FSM** : Le gate C9 sur READY_FOR_DEV doit-il être **BLOCKING dès maintenant** ou **WARNING** pour une période de transition (éviter de bloquer les 25 stories déjà READY_FOR_DEV du Module 1 qui n'ont peut-être pas de `_fact_dossier.md`) ?
- **Q3 — Délégation** : L'implémentation touche ≥ 3 fichiers (DELEGATION GATE). La mène-t-on sur le thread principal (TDD interactif, visibilité maximale) ou délègue-t-on à un worker Herdr ?