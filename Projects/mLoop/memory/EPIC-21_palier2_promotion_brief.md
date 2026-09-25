# Brief de Mission Worker — Promotion Palier 2 EPIC-21 (212 → 215)

**Émetteur** : Orchestrateur principal mLoop (session Grill EPIC-21)
**Date** : 2026-09-24
**Task-type** : `build` (Auteur) — la qualité est garantie par la porte `rubber-duck` (sentinel), pas par le modèle d'auteur (ADR-0388).

---

## 1. Mission

Convertir **4 récits** du Palier 1 (brouillon) vers le Palier 2 haute-fidélité, **sans jamais** poser `READY_FOR_DEV` (statut réservé à l'humain — STORY_LIFECYCLE_PROTOCOL §1.2, faute grave §4).

| Récit | Décision grill à encoder | Fact dossier |
| :--- | :--- | :--- |
| `MLOOP-212-FE` | **ADR-007** : postMessage + `stateHandle` lecture seule ; dimensions = fact-quest 210 ; fallback URL localhost ; `UI_MIN_WIDTH_PX=320` | `memory/evidence/MLOOP-212-FE_fact_dossier.md` |
| `MLOOP-213-BE` | **ADR-008** : pending JSON-Schema regénérable ; `decision_records.jsonl` append-only dans `memory/evidence/` | `memory/evidence/MLOOP-213-BE_fact_dossier.md` |
| `MLOOP-214-BE` | **ADR-009** : hiérarchie `.agents/rules/` > skills > AGENTS.md + log `skill_rule_conflict` ; bridge dual-stack `skills/list\|get` vs `skill://`+`read_skill` ; critère budget boot ≤ 15 000 jetons (macro Q4) | `memory/evidence/MLOOP-214-BE_fact_dossier.md` |
| `MLOOP-215-FULL` | **ADR-010** : fixture Playwright `tests/mcp_ui_iframe/` (2 ressources `ui://`, 0 requête sortante, 1 interaction, 1 roundtrip `postMessage`) ; critère L51 = compteur dynamique « 0 FAIL » (jamais « 1 386 ») ; mocks stdio = in-process `StringIO` + `Popen(PIPE, timeout)` | `memory/evidence/MLOOP-215-FULL_fact_dossier.md` |

Décisions transverses déjà scellées (à refléter si pertinent) : **ADR-004** (macro, 6 décisions) sous `docs/01-architecture/`.
Ancrages code déjà établis dans les fact dossiers (Lignes X-Y) : **les réutiliser tel quels** — ne rien ré-inventer, ne rien inventer.

---

## 2. Procédure par récit (dans l'ordre 212 → 213 → 214 → 215)

1. **Lire** : le récit cible (`backlog/stories/<ID>.md`), son fact dossier, l'ADR-00X correspondant, et le gabarit **`standards/blueprints/story_template.md`** (SEUL gabarit légal Palier 2 — ADR-0375).
2. **Convertir** le corps au format haute-fidélité du gabarit : frontmatter complet, sections obligatoires séparées par `---`, **4 Piliers Gherkin** (Nominal / Exceptions / Résilience / UX) rédigés à partir des décisions ADR + faits des fact dossiers.
3. **Frontmatter** : `status: READY_FOR_GROOMING` (**PAS** `READY_FOR_DEV`), `grill_me: DONE`, `invest_score: 6/6` (après application du rubric INVEST).
4. **Terminer** le corps STRICTEMENT après `## Scénarios de test` (zéro note IA, zéro ancre `#L` dans les citations).
5. **Rubber-duck** : `python src/swarm.py rubber-duck --file Projects/mLoop/backlog/stories/<ID>.md` → rapport sous `backlog/reviews/`. Si constat bloquant : corriger puis relancer jusqu'à passage.
6. **Récit suivant.**

---

## 3. Clôture (après les 4 récits)

1. **`backlog/sprint_backlog.md`** (SSOT) : pour 212/213/214/215 → colonne Grill-me = `✅ DONE`, colonne Statut = `🟡 READY_FOR_GROOMING`, Responsable = `🤖 IA (Palier 2 atteint, feu vert humain requis)`. Mettre à jour la note « Origine » de l'épopée (ligne évoquant « récits 212-215 : Palier 1 DRAFT / grill_me PENDING »).
2. **`backlog/epics/epic_mcp_modern_suite_2026q4.md`** : statut du tableau des 6 récits 212-215 → `READY_FOR_GROOMING` ; en-tête si nécessaire.
3. **`python src/swarm.py sync --project mloop`**.
4. **Sidecar** : `memory/worker_MLOOP-212-FE.status` (ADR-0355) résumant : 4 récits convertis, 4 rubber-duck PASS, statut cible READY_FOR_GROOMING.

## 4. Interdits

- `status: READY_FOR_DEV` (humain uniquement).
- Toute édition des récits **210 / 211** (déjà validés humain — ne pas toucher).
- Écriture hors `Projects/mLoop/` ; `init` ou altération de `lifecycle_state.json`.
- Routes/payloads inventés ; liens locaux `C:\...` dans le corps des récits (liens `file:///` autorisés UNIQUEMENT dans les citations de preuves).
- Chaînage `&&` sous PowerShell.
