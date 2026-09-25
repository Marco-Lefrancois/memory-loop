---
created: 2026-09-22T12:13:59.717Z
source: plannotator
tags: [plannotator, memory-loop, impl, mentation, blindspot]
---

[[Plannotator Plans]]

# 🏛️ Plan d'Implémentation Zéro Blindspot — Check Vibe-Check « Directives Projet & SSOT Canonique »

**Autorité** : ADR-0376 (Audit 360° en 7 Couches) · **Déclencheur** : demande humaine (option B)
**Objectif** : Ajouter un contrôle Vibe-Check qui force la prise en compte des directives de projet (`directives/tech.md`, `directives/business.md`) et l'ancrage sur le SSOT canonique — comblant le gap qui a causé l'erreur de source du modèle sur `docs/03-models/`.

---

## 0. CONSTAT FONDATEUR (issu du balayage à froid des 7 couches)

### 0.1 Le gap est réel et non couvert
- Aucune règle (`AGENTS.md`, `.agents/rules/`, Boot Sequence ADR-0322, 20 checks Vibe-Check) n'oblige l'orchestrateur à lire `directives/`.
- Le principe « directives = Lois Fondamentales » est archi-documenté (`directives_best_practices.md`, `mloop_5_pillars_mapping.md`, personas `sentinel`/`plan`) mais **jamais encodé** comme contrôle opposable à l'orchestrateur.

### 0.2 Blindspots additionnels découverts (réponse à « manque-t-il d'autres directives ? » — OUI, 4 familles)
En lisant `Projects/BoireFrere_Segment2/directives/business.md` :
- **B1** — `§36` / `tech.md §15` : `docs/03-models/` = SSOT autoritaire ; `reference/` non autoritaire (cause racine déjà vue).
- **B2** — `§26` : Maquettes Figma = SSOT PREMIÈRE ; récit sans écran Figma = « non requis ».
- **B3** — `§27` : **CONTRADICTION** — « REC-014 (Correction) déprécié/archivé » alors que REC-014-BE (Discard) est actif au sprint.
- **B4** — `§20-24` : Immuabilité/Delta-only, bouton Max, Gating — exactement ce que les Gherkin FE boilerplate ne testent pas.

### 0.3 Contrainte de non-régression CRITIQUE (blindspot d'implémentation)
- Présence de `directives/tech.md`+`business.md` : **BoireFrere_Segment2 UNIQUEMENT** (7/8 autres projets ne l'ont pas — Metro_FOOD/SANTE/COMMERCE, Shopify n'ont que `CONTEXT.md`).
- Le vibe-check calcule `is_valid = passed_count == total_count`. Un nouveau check FAIL **bloquerait la Boot Sequence de TOUS les projets**.
- **Décision de design** : le check est **conditionnel** — s'il n'y a pas de `directives/`, statut `PASS` (rien à vérifier). S'il y en a, il vérifie leur intégrité SSOT. Sévérité `WARNING` (jamais FAIL bloquant) pour un premier palier, à l'image du Check 17 (QA).
- **Nuance** : puisque WARNING ≠ PASS dans le calcul actuel (`passed_count == total_count`), un WARNING ferait quand même chuter le score total. → Voir §6 décision d'implémentation sur le traitement du statut (option retenue : WARNING compté comme non-bloquant via ajustement du calcul `is_valid`, aligné sur l'intention du Check 17 qui est déjà passif).

---

## 1. COUCHE 1 — Blueprints (`standards/blueprints/`)
**Impact : AUCUN.** Aucun gabarit créé/modifié/rendu caduc. Le check lit des directives existantes, ne génère aucun document.
- Statut : `[NO-OP]`

---

## 2. COUCHE 2 — Protocoles (`standards/protocols/`)
- `[MODIFY]` `standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md` — non requis (ce plan EST l'application du protocole).
- `[NEW]` `standards/protocols/PROJECT_DIRECTIVES_SSOT_PROTOCOL.md` — **À DÉCIDER avec toi** : créer un protocole normatif court qui déclare la hiérarchie SSOT (`docs/03-models/` > `reference/`), l'obligation de charger `directives/` en Phase ≥ 2, et la primauté Figma. Recommandé pour que le check ait une autorité documentaire citable.
- Statut : `[NEW]` (1 fichier, ~40 lignes) — **sur ton feu vert**

---

## 3. COUCHE 3 — Architecture ADR (`standards/adr-system/`)
- `[NEW]` `standards/adr-system/0382-project-directives-ssot-boot-enforcement.md` — ADR Type 1 consignant : (a) la décision d'ajouter le 21ᵉ check, (b) la hiérarchie SSOT canonique, (c) le caractère conditionnel/non-régressif.
- `[MODIFY]` `standards/adr-system/README.md` — indexer le nouvel ADR-0382.
- Statut : `[NEW]` + `[MODIFY]` index

---

## 4. COUCHE 4 — Directives & Personas (`.agents/agents/`, racine)
- `[MODIFY]` `AGENTS.md` (+ miroirs `GEMINI.md`, `CLAUDE.md` — auto-synchronisés par Check 1) : ajouter dans §4.1 « Always do » une clause **« Chargement des Directives Projet & SSOT Canonique »** : en Phase ≥ 2, lire `directives/tech.md`+`business.md` et identifier le SSOT autoritaire AVANT tout cadrage/audit/brief de worker.
- `[MODIFY]` `Projects/BoireFrere_Segment2/AGENTS.md` : ajouter une section « SSOT Autoritaire » (le fichier projet ne liste même pas `directives/` aujourd'hui et pointe `reference/` comme « officiel » — à corriger).
- Statut : `[MODIFY]` ×2 (racine auto-mirror + projet)

---

## 5. COUCHE 5 — Skills (`.agents/skills/`)
- `[MODIFY]` `.agents/skills/grill/SKILL.md` — Étape 0 « Search-Before-Ask » : ajouter explicitement « localiser et citer le SSOT canonique via `directives/` avant de briefer un worker » (la faute exacte commise).
- `[MODIFY]` `.agents/skills/calibrate/SKILL.md` — si le check devient un point d'auto-étalonnage (optionnel).
- Statut : `[MODIFY]` ×1 (grill) obligatoire, calibrate optionnel

---

## 6. COUCHE 6 — Core & CLI Python (`src/pipelines/vibe_check.py`)
**Le cœur du changement.**
- `[MODIFY]` `src/pipelines/vibe_check.py` :
  1. Ajouter **Check 20 (nouveau)** « Intégrité des Directives Projet & SSOT Canonique » APRÈS le Check 19 (StandardsGraph), avant le calcul `passed_count`.
  2. Logique conditionnelle :
     - Si `project_dir/directives/` absent → `PASS` (message « Directives projet non applicables »). Zéro régression pour les 7 autres projets.
     - Si présent → vérifier : (a) `tech.md` ET `business.md` existent et non vides ; (b) au moins une mention du SSOT canonique (`docs/03-models/`) OU une déclaration de hiérarchie SSOT ; (c) `CONTEXT.md` présent à la racine projet.
     - En cas de manque → `WARNING` (non bloquant), jamais `FAIL`.
  3. `[MODIFY]` calcul final : ajuster `is_valid` pour que les statuts `WARNING` ne fassent PAS chuter le résultat sous 100% (aligner Check 17 + Check 20). Actuellement WARNING casse le score — bug latent à corriger proprement : `is_valid = all(c['status'] in ('PASS','WARNING') for c in checks)` et affichage « X PASS / Y WARNING / Z FAIL ».
  4. Robustesse ADR-0369 : lecture fichiers en `try/except` avec `logger.error(exc_info=True, extra={...})`, encoding utf-8, aucun accès hors `with`/context.
- **Blast radius** (codegraph) : `run_vibe_check` a 34 callers dans `project_core.py` + 10 fichiers de tests. Le changement de calcul `is_valid` est le point sensible → couvert en Couche 7.
- Statut : `[MODIFY]` 1 fichier, ~45 lignes ajoutées + 3 lignes calcul

---

## 7. COUCHE 7 — Tests & Parité (`tests/`, `CLI_PIPELINE_GUIDE.md`)
- `[NEW]` `tests/test_vibe_check_directives_ssot.py` — cas parametrize (`@pytest.mark.parametrize`) :
  1. Projet AVEC directives conformes (Boire) → PASS.
  2. Projet SANS directives (Metro_FOOD) → PASS (conditionnel, zéro régression).
  3. Projet avec `directives/` mais SSOT non déclaré → WARNING.
  4. `directives/tech.md` vide → WARNING.
  5. Non-régression : WARNING ne fait pas passer le vibe-check global à FAIL.
- `[VERIFY]` les 10 tests existants (`test_vibe_check_*.py`) restent verts (le changement `is_valid` doit être rétro-compatible : aucun test n'attendait qu'un WARNING casse le score — à confirmer par exécution).
- `[RUN]` `python src/swarm.py guide --sync` (Check 15) — non requis si aucune commande CLI ajoutée (le check est interne à `vibe-check`, pas une nouvelle commande). À confirmer : **aucune entrée `_registry.py` ajoutée** → pas de dérive guide.
- `[RUN]` `uv run pytest tests/ -q` : 100% vert obligatoire avant clôture.
- Statut : `[NEW]` 1 test + `[VERIFY]` suite complète

---

## 8. SÉQUENCE D'EXÉCUTION ATOMIQUE (après ton approbation)
1. Couche 3 (ADR-0382) + Couche 2 (protocole) — fondation documentaire.
2. Couche 6 (code `vibe_check.py`) — check + correctif calcul.
3. Couche 7 (tests) — écrire, exécuter, verts.
4. Couches 4 & 5 (AGENTS.md racine+projet, skill grill).
5. Certification : `uv run pytest` 100% + `vibe-check` sur Boire (attendu 21/21) + sur Metro_FOOD (attendu inchangé, zéro régression).
6. Walkthrough de conformité.

---

## 9. DÉCISIONS OUVERTES POUR TOI (bloquantes avant code)
1. **Périmètre couche 2** : je crée le protocole `PROJECT_DIRECTIVES_SSOT_PROTOCOL.md` (recommandé) ou je me contente de l'ADR-0382 ? 
2. **Sévérité** : WARNING non bloquant (recommandé, palier 1) — OU FAIL bloquant seulement pour les projets qui ONT des directives (plus strict) ?
3. **Correctif `is_valid`** : je corrige le traitement WARNING (aligne Check 17+20) — OK ? C'est techniquement une amélioration mais ça touche le sens du score de TOUS les projets, donc je te le signale explicitement.
4. **Blindspots B2/B3/B4** : hors périmètre de CE check (qui vérifie la *présence/prise en compte* des directives, pas leur *contenu métier*). La contradiction B3 (REC-014 déprécié vs actif) reste une **décision métier** à trancher séparément dans la revue des récits. Confirmes-tu qu'on les traite après, dans le fil de la revue REC-009→014 ?

**Aucune ligne de code ne sera écrite avant ton feu vert explicite (ADR-0376).**