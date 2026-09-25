---
dossier_id: MLOOP-170-BE_fact_dossier
story_id: MLOOP-170-BE
dossier_status: CURRENT
created_at: "2026-09-22"
sources_hashes:
  epic_modular_refactoring_ast_debt.md: "pending"
  vibe_check.py: "pending"
---

# Dossier de Preuves Documentaires — MLOOP-170-BE

## 🧭 1. Sources Physiques & Matrice de Vérité

| Source | Type | Rôle | Statut |
| :--- | :---: | :--- | :--- |
| `backlog/epic_modular_refactoring_ast_debt.md` (§1) | Épic | Cadrage EPIC-17, récit pilote | ✅ CURRENT |
| `src/pipelines/vibe_check.py` | Code | Cible monolithique (880 lignes, 2 déf. top-level) | ✅ Vérifié 22/09 |
| `standards/adr-system/` (ADR-0202, ADR-0381) | ADR | Plafond 300 lignes (RULE-AST-01), red-green | ✅ Référencé |
| Grill-Me Micro 1:1 du 2026-09-22 | Séance | 4 arbitrages PO verbatim (OQ-170-01→04) | ✅ Acté |

## 🔬 2. Faits Extraits & Verbatims (Passage-Level Grounding)

> Extrait 1 — `vibe_check.py` (audit structurel 22/09/2026) :
> « vibe_check.py = **880 lignes** ; structure = 2 définitions top-level (`detect_project_lifecycle_stage` L10, `run_vibe_check` L129 — le reste est le corps monolithique de `run_vibe_check` avec 28 mentions de familles de checks) »
> ➔ Fait établi : monolithe ≥ 880 lignes, violation RULE-AST-01 (plafond 300), corps unique L129→fin.

> Extrait 2 — Cadrage EPIC-17 (§1 — Récit Pilote) :
> « **19 fichiers** référencent `vibe_check` sous `src/` + `tests/` »
> ➔ Fait établi : surface de callers = 19 — contrat de rétrocompatibilité strict obligatoire.

> Extrait 3 — Arbitrages Grill-Me 1:1 (22/09/2026, PO) :
> « OQ-170-01 : Orchestrateur fin + un module par famille de contrôles, imports explicites — pas d'auto-découverte magique (pattern registry proscrit) »
> « OQ-170-04 : Tests existants immobiles ; tests miroir neufs uniquement pour chaque famille extraite »
> ➔ Fait établi : pattern d'extraction = package `vibe_check/` + orchestrateur fin + ré-exports `__init__.py`, **pas** de registry dynamique.

> Extrait 4 — Clause exemption ADR-0319 (ajoutée 22/09 pour débloquer le Sentinel) :
> « refactoring modulaire interne de `src/pipelines/vibe_check.py` — **aucune route HTTP n'est consommée ni exposée**… `[API de soumission à définir]` — jamais inventée »
> ➔ Fait établi : composant 100% interne, exemption OQ-170 déclarée et validée par Rubber Duck.

## 🗄️ 3. Périmètre Structurel

- **Cible** : `src/pipelines/vibe_check.py` (880L) → package `src/pipelines/vibe_check/`.
- **Signature publique gelée** : `run_vibe_check(project_name, target_file=None, stage=None) -> dict` (+ structure de retour byte-compatible).
- **Rétrocompatibilité** : `__init__.py` ré-exporte l'API — les 19 callers restent inchangés.
- **Tests** : ~10 fichiers existants immobiles ; miroirs neufs par famille (`tests/vibe_check/<famille>_test.py`).
- **Non impacté** : les 38 autres fichiers en dette (lots suivants, MLOOP-172-BE), RULE-AST-02/03.

## 🎯 4. Contrats Déclaratifs Cibles

- **Aucune route HTTP** — exemption `OQ-170` + mention `[API de soumission à définir]` (Zéro Fausse Route).
- **Contrats Python internes** : signature `run_vibe_check` gelée, structure de retour dict gelée.

## 🏁 5. Évaluation de la Frontière Active (Admission of Limits)

- **Ce que le dossier PROUVE** : volume exact (880L), surface callers (19), 4 arbitrages PO, contrainte de signature, exemption API.
- **Ce qu'il ne PRUVE PAS** : le découpage exact par famille (28 mentions identifiées mais non listées ici), la compatibilité byte réelle après extraction (testée en Phase 3), le comportement des 19 callers sous charge.
- **Frontière** : ce dossier couvre le **cadrage** (Phase 2) — l'exécution red-green et la comparaison de sortie appartiennent à MLOOP-170-BE (Phase 3).
