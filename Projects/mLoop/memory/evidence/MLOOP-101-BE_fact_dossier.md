---
story_id: MLOOP-101-BE
dossier_status: VALIDATED
created_at: 2026-09-20T11:35:00Z
updated_at: 2026-09-20T12:45:00Z
sources_hashes:
  lexicon_resolver.py: 0F7CEBCDA9CD1D367079BCC8406CE04B9294A593ADB5E59C628E535B2044DC6B
  token_ledger.py: BAD589CFB58D12E197442D73B1B399C7627700C835A7A4D148B7E74C850B89FF
  file_lock.py: 8B133E5CC91EB51CF5955B6B306CA293A3F08EF690E995001FE7FAA5BE353CB9
  context_guard.py: 1CD14A25E903DADCA883A733E5875D49284460510E093ECD52AD4AEA8B165C16
  opencode_meter.py: 81EC7D3D0842BC6E6AB3119CF11ADC0C9B686A5B62984387707698F8B6745D30
  context_monitor.py: E7BA37D2F985077D08080D6775450B5EFD5432F36E1AB8E9D80F3A48307C1DCF
  lexical_guard.py: 9DA41E52609DAEB08BA188425CCC9AB98486A31A999B624E50F8EE25709799AE
  antigravity_meter.py: DDF8CCCCF93331BE67D8FB3589190F3BEF03A678F4A7C950FC4FCBDF9855B3CD
  project.py: F1BD3B3294D3198B7AE1C2D45490D273526C161461625E5A81A1565C14FF47BE
  0202-modularite-interne-agents.md: 670B0754488FEA26FB0CF86E51FE8E81000FFA23EFC1F6FA92DAC4943CAB1169
---

# 🐣 Dossier de Preuves Documentaires & Cadrage — `MLOOP-101-BE` (Rénovation Modulaire du Résolveur Lexical et Grand Livre de Jetons)

> **Titre Fonctionnel Pur** : Rénovation Modulaire du Résolveur Lexical et Grand Livre de Jetons
> **Epic Jira** : `EPIC-10-SOVEREIGN-EXCELLENCE` (Excellence Souveraine, Rénovation Modulaire & Temps Réel)
> **Couche** : `backend`
> **Récit Précédent / Dépendances** : aucune (MLOOP-105-BE `DONE_TESTED` pour le domaine hooks Git ; MLOOP-100-BE indépendante)

---

### 📂 1. Sources Physiques & Maquettes SSOT (Liens Directs Cliquables)

> ⚠️ *Note Headless* : Récit de refactoring framework pur — `N/A - Composant Headless`. Sources primaires : code physique + ADR.

| Source SSOT | Nature | Lien Repo Local (`file:///...`) |
| :--- | :--- | :--- |
| **ADR-0202** | Décision structurante (plafonds 300L / 15 Ko) | [0202-modularite-interne-agents.md](file:///C:/Memory%20Loop/standards/adr-system/0202-modularite-interne-agents.md) |
| **Story cible** | Spécification 4 Piliers Gherkin | [MLOOP-101-BE.md](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-101-BE.md) |
| **Baseline déterministe** | Sortie `python src/swarm.py code-check --all` (AST) | 170/258 conformes \| 257 violations (2026-09-20) |
| **Tests de non-régression** | Suite Pytest existante | test_lexicon_project_resolver.py, test_lexicon_resolver_tiebreak.py, test_lexicon_resolve_story_prefix.py, test_token_ledger.py |

---

### ⚖️ 1.1 Matrice de Résolution des Conflits de Sources

| Conflit | Source A (Niveau & Valeur) | Source B (Niveau & Valeur) | Décision Retenue & Justification |
| :--- | :--- | :--- | :--- |
| **C1 — Périmètre utils vs Gherkin n°4** | Story In-Scope L30-34 (5 fichiers) | Story Gherkin n°4 L84-88 (« compte total des violations AST pour cette couche strictement égal à zéro ») | **CONTRADICTION INTERNE NON RÉSOLUE** → Arbitrage #2. 3 fichiers utils hors scope portent 4 violations (context_monitor L96, lexical_guard L136/142, antigravity_meter L45). |
| **C2 — opencode_meter au-delà des except** | Story In-Scope L34 (audit `except: pass` uniquement) | code-check RULE-AST-02 L143 (`sqlite3.connect` nu) | **GAP NON COUVERT** → l'In-Scope doit viser « zéro violation code-check », pas seulement les `except: pass`. |
| **C3 — project.py hors scope** | Story In-Scope (src/utils/ strict) | `src/commands/handlers/project.py` : 462L / 24 326 o / 2×RULE-AST-01 | **HORS PÉRIMÈTRE DÉCLARÉ** → Arbitrage #1 (cette session). |
| **C4 — Nommage module hooks** | Proposition initiale : `handlers/hooks.py` | `handlers/hook.py` EXISTE (92L, hooks cycle de vie pre_compact, ADR-0364) | Si extraction : nommer `handlers/git_hooks.py` (éviter collision sémantique lexicale). |
| **C5 — Portée ADR-0202 sur src/utils/** | ADR-0202 §1 L8 (contexte : `src/pipelines/` et `src/agents/`) | code-check applique RULE-AST-01 à tout `src/` y compris utils | La portée utils est une **extension de facto** du linter (MLOOP-080-BE) ; l'écrire noir sur blanc dans la story leverait l'ambiguïté. |

### 🎙️ 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> [!NOTE]
> **Extrait 1 — Plafonds incompressibles ADR-0202**
> **Source** : [`0202-modularite-interne-agents.md#L14-L23`](file:///C:/Memory%20Loop/standards/adr-system/0202-modularite-interne-agents.md#L14-L23)
> *« Tout fichier d'agent ou de pipeline doit respecter les plafonds incompressibles suivants : | Nombre de lignes | > 300 lignes | Refactoring obligatoire par extraction de sous-modules | … | Taille fichier | > 15 Ko | Signal fort de monolithisme à décomposer. … Les fonctions auxiliaires sont extraites dans des sous-modules Python purs adjacents »*
> ➔ **Fait établi** : Plafond strict 300L **ET** 15 Ko par module ; pattern = sous-modules adjacents au module d'origine (valide le plan `src/utils/lexicon/entity_matcher.py` + `project_resolver.py`).

> [!NOTE]
> **Extrait 2 — Périmètre originel d'ADR-0202**
> **Source** : [`0202-modularite-interne-agents.md#L6-L8`](file:///C:/Memory%20Loop/standards/adr-system/0202-modularite-interne-agents.md#L6-L8)
> *« Afin d'éviter que les fichiers Python sous `src/pipelines/` et `src/agents/` ne deviennent monolithiques et inmaintenables, un cadrage strict sur la taille et le découpage modulaire est requis. »*
> ➔ **Fait établi** : ADR-0202 ne cite pas `src/utils/` ; l'application aux utils relève de l'extension linter code-check (conflit C5).

> [!NOTE]
> **Extrait 3 — In-Scope déclaré de la story**
> **Source** : [`MLOOP-101-BE.md#L30-L34`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-101-BE.md#L30-L34)
> *« Découpage de `src/utils/lexicon_resolver.py` (411L) en : `src/utils/lexicon/entity_matcher.py` … `project_resolver.py` ; Refactoring de `src/utils/token_ledger.py` (350L) en conservant la façade publique intacte ; Audit et remplacement exhaustif de tous les `except: pass` dans `src/utils/file_lock.py`, `src/utils/context_guard.py` et `src/utils/opencode_meter.py`. »*
> ➔ **Fait établi** : 5 fichiers en scope ; la décomposition cible de token_ledger n'est PAS spécifiée (contrairement à lexicon) — gap de spécification.

> [!NOTE]
> **Extrait 4 — Exigence Gherkin n°4 (zéro violation sur la couche)**
> **Source** : [`MLOOP-101-BE.md#L84-L88`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-101-BE.md#L84-L88)
> *« Quand l'analyseur déterministe code-check inspecte l'ensemble du dossier utils / Alors chaque module audité obtient la mention PASS / Et le compte total des violations AST pour cette couche est strictement égal à zéro »*
> ➔ **Fait établi** : Non satisfaisable avec l'In-Scope actuel (C1) : il faudrait couvrir AUSSI context_monitor.py, lexical_guard.py, antigravity_meter.py.

> [!NOTE]
> **Extrait 5 — Exigence de performance sans harness**
> **Source** : [`MLOOP-101-BE.md#L77-L81`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-101-BE.md#L77-L81)
> *« Alors le temps de réponse unitaire moyen demeure sous le seuil des 5 millisecondes / Et la mémoire vive consommée reste stable »*
> ➔ **Fait établi** : AUCUN fichier `tests/*perf*|*bench*|*latency*` n'existe dans le dépôt → le scénario n°3 n'est pas vérifiable en l'état (ADR-0352 : `verification_harness` vide = BLOQUANT).

> [!NOTE]
> **Extrait 6 — Structure réelle de project.py (proposition utilisateur)**
> **Source** : [`project.py#L156-L236`](file:///C:/Memory%20Loop/src/commands/handlers/project.py#L156-L236) (24 326 o, 462L)
> *Bloc Git-hooks : `_HOOK_MANAGED_MARKER` (L156), `_resolve_git_root` (L162-169), `handle_install_hooks` (L172-219), `_uninstall_hook` (L221-236) ≈ 80 lignes. Reste : `handle_init` (L16-124, ~108L), `handle_guide` (L238-343, ~105L), `handle_lifecycle_status` (~L395-433), `handle_lifecycle_clean` (L436-459).*
> ➔ **Fait établi** : Extraire UNIQUEMENT les handlers hooks ramènerait project.py à ≈ 382L → **toujours > 300L** : l'extraction proposée est nécessaire mais insuffisante pour la conformité ADR-0202.

### 🗄️ 3. Socle Factuel Mesuré (Baseline Déterministe code-check — 2026-09-20)

#### 3.1 Couche `src/utils/` (16 fichiers)

| Fichier | Lignes | Ko | Violations | Détail AST |
| :--- | :---: | :---: | :---: | :--- |
| `lexicon_resolver.py` | 411 | 18.9 | **4** | AST-01 (>300L, >15Ko) + AST-04 (L297, L331) |
| `token_ledger.py` | 350 | 14.8 | **2** | AST-01 (>300L) + AST-04 (L105) |
| `opencode_meter.py` | 225 | 9.7 | **3** | AST-04 (L49, L117) + **AST-02 (L143 : sqlite3.connect nu)** |
| `file_lock.py` | 177 | 5.8 | **4** | AST-04 (L72, L78, L154, L166) |
| `context_guard.py` | 148 | 6.2 | **1** | AST-04 (L138) |
| `lexical_guard.py` | 146 | 5.2 | **2** ⚠️ hors scope | AST-04 (L136, L142) |
| `antigravity_meter.py` | 255 | 10.4 | **1** ⚠️ hors scope | AST-04 (L45) |
| `context_monitor.py` | 125 | 5.2 | **1** ⚠️ hors scope | AST-04 (L96) |
| 8 autres modules | ≤275 | ≤13.5 | **0** | PASS (semantic_chunker 275L, blueprints 81L, event_logger 156L, logger 104L, parent_doc_resolver 140L, retry 70L, secret_guard 49L, token_budget 76L) |

#### 3.2 Blast Radius (16 sites d'import dans 14 fichiers)

- **`lexicon_resolver`** : `src/swarm.py`, `src/pipelines/focus.py`, `src/commands/handlers/{analysis,deep_search,fact_check,fact_search,hook}.py` → toute réorganisation doit conserver l'import `SemanticLexiconResolver` opérationnel (façade publique).
- **`token_ledger`** : `src/core/llm_client.py`, `src/pipelines/{rubber_duck,vibe_check}.py`, `src/converters/markpdfdown_converter.py`, `src/utils/{antigravity_meter,opencode_meter}.py` → façade `TokenLedger` intangible.

#### 3.3 Dette Handlers (contexte Arbitrage #1 — hors scope déclaré)

| Fichier | Lignes | Violations AST-01 | Autres |
| :--- | :---: | :---: | :--- |
| `commands/_registry.py` | 1 993 | >300L, >15Ko (73.6 Ko) | — |
| `commands/handlers/analysis.py` | 669 | >300L, >15Ko | — |
| `commands/handlers/project.py` | 462 | >300L, >15Ko | sujet de l'Arbitrage #1 |
| `commands/handlers/export.py` | 399 | >300L, >15Ko | — |
| `commands/handlers/architecture.py` | 371 | >300L | — |
| `commands/handlers/code_intelligence.py` | 289 | — | AST-04 (L69) |
| `commands/handlers/{gates,memo_search}.py` | 99/100 | — | AST-04 (L90 / L73) |
| `commands/handlers/plannotator.py` | 229 | — | AST-03 ×2 (subprocess.run sans timeout L69, L156) |

### 🎯 4. Contrats Déclaratifs Cibles (Façades Modules Backend)

* **Façade `src/utils/lexicon_resolver.py` (conservée)** : `SemanticLexiconResolver.resolve_project_alias(str) -> str | None`, `SemanticLexiconResolver.resolve_story_query(str, Path) -> Path | None` — intangible (16 sites d'import).
* **Façade `src/utils/token_ledger.py` (conservée)** : `TokenLedger` — intangible (7 sites d'import).
* **Nouveaux modules adjacents (ADR-0202)** : `src/utils/lexicon/entity_matcher.py`, `src/utils/lexicon/project_resolver.py` — imports internes uniquement, zéro API CLI nouvelle.
* **Critère de sortie** : `python src/swarm.py code-check --file <cible>` → PASS sur 100% des fichiers en périmètre final ; suite pytest 4 fichiers au vert ; `sync`/`guide --sync` sans dérive CLI (ADR-0370).

---

### 🏁 5. Évaluation de la Frontière Active

#### ✅ Arbitrage #1 — RÉSOLU (2026-09-20, approbateur : Marco)

**Sort du découpage de `src/commands/handlers/project.py` (462L / 24.3 Ko, 2×RULE-AST-01)**
* **DÉCISION (Option A)** : MLOOP-101-BE reste 100% `src/utils/` ; création d'une story dédiée `MLOOP-106-BE` « Découpage Modulaire des Handlers CLI » (project.py 462L + analysis.py 669L + export.py 399L + architecture.py 371L ; _registry.py 1993L en backlog EPIC-10). L'extraction git-hooks y sera nommée `handlers/git_hooks.py` (règle C4 — éviter la collision avec `handlers/hook.py` ADR-0364).
* **Implications** : le gap handlers n'est PAS couvert par MLOOP-101-BE ; interdiction d'injecter des modifications handlers dans cette story. MLOOP-106-BE est à créer en gabarit Palier 1 (`story_draft_template.md`, `status: DRAFT`, `grill_me: PENDING`).

#### ✅ Arbitrage #2 — RÉSOLU (2026-09-20, approbateur : Marco)

**Portée du « zéro violation » (conflit C1/C2)**
* **DÉCISION (Option A)** : In-Scope ÉTENDU — ajout des 3 modules utils oubliés à l'audit d'exception : `context_monitor.py` (L96), `lexical_guard.py` (L136, L142), `antigravity_meter.py` (L45) + intégration du fix RULE-AST-02 `opencode_meter.py` L143 (`sqlite3.connect` encapsulé en context manager). Le scénario Gherkin n°4 (« zéro violation AST sur toute la couche utils ») devient cohérent avec l'In-Scope.
* **Implications** : 8 modules utils en périmètre (2 découpages + 6 audits de conformité ADR-0369) ; l'In-Scope de la story sera amendé en conséquence à la clôture du grill.

#### ✅ Arbitrage #3 — RÉSOLU (2026-09-20, approbateur : Marco)

**Décomposition cible de `token_ledger.py` (350L, classe unique `TokenLedger` L20-350)**
* **DÉCISION (Option A)** : Extraction en package `src/utils/token_ledger/` :
  - `token_ledger/reporting.py` : reçoit `generate_report()` (~100L, L250-349) ;
  - `token_ledger/key_info.py` : reçoit `resolve_active_key_info()` (~70L, L62-130, logique de sélection de clé LiteLLM) ;
  - façade `token_ledger.py` allégée : `TokenLedger` conservée avec `calculate_cost()` + `record_interaction()` + `load_entries()`, déléguant aux sous-modules — **< 300L garanti**, façade `TokenLedger` intangible (7 sites d'import).
* **Implications** : mêmes imports fonctionnels (`from src.utils.token_ledger import TokenLedger`) grâce au module `token_ledger/__init__.py` ré-exportant la façade ; structure symétrique du package `src/utils/lexicon/`.

#### ✅ Arbitrage #4 — RÉSOLU (2026-09-20, approbateur : Marco)

**Harnais de vérification du scénario n°3 « < 5 ms » (prérequis ADR-0352 — `verification_harness` vide = BLOQUANT)**
* **DÉCISION (Option A)** : Test pytest dédié `tests/performance/test_utils_latency.py` — mesure `time.perf_counter()` moyenne < 5 ms sur le chemin chaud `resolve_project_alias` + `resolve_story_query`, et vérification déterministe des plafonds ADR-0202 (300L / 15 Ko) sur les modules utils du périmètre. Intégré à la suite de non-régression (4 fichiers lexicon/ledger existants).
* **Implications** : le champ `verification_harness` de l'EvidencePack sera alimenté avec ce test ; le scénario n°3 devient vérifiable et la story constructible.
#### ✅ Arbitrage #5 — RÉSOLU (2026-09-20, approbateur : Marco)

**Sort du bug `focus.py` (pipelines — hors scope utils)**
* **DÉCISION (Option A)** : Story dédiée `MLOOP-107-BE` « Correction du verrou d'attention focus » (Palier 1 DRAFT, grill séparé) ; MLOOP-101-BE inchangée. Bug confirmé par lecture directe du code : L32-33 (fallback `.md` sans réassignation de `story_rel_path`), L90 (comparaison `rel_p == story_rel_path` à échouer), L114-115 (verdict de succès inconditionnel). Contournement en vigueur : passer `--story <ID>.md`.
* **Implications** : `focus.py` reste hors périmètre ; noter que `focus.py` porte lui-même une violation RULE-AST-04 (L52-53 `except Exception: pass`) qui relèvera d'une future vague pipelines.

---

### 🧾 6. Synthèse du Grill-Me 1:1 (clôture — 5/5 arbitrages résolus)

| # | Question d'arbitrage | Décision |
| :---: | :--- | :--- |
| 1 | Sort du découpage `handlers/project.py` (462L) | **Option A** — Story dédiée MLOOP-106-BE ; MLOOP-101-BE reste 100% `src/utils/` |
| 2 | Portée du « zéro violation » (conflit C1/C2) | **Option A** — In-Scope ÉTENDU aux 3 modules oubliés (8 modules utils au total) |
| 3 | Décomposition `token_ledger.py` (350L) | **Option A** — Package `token_ledger/` (`reporting.py` + `key_info.py`, façade allégée < 300L) |
| 4 | Harnais du scénario « < 5 ms » (ADR-0352) | **Option A** — `tests/performance/test_utils_latency.py` (perf_counter < 5 ms + plafonds 300L/15 Ko) |
| 5 | Bug `focus.py` (pipelines) | **Option A** — Story dédiée MLOOP-107-BE ; MLOOP-101-BE inchangée |

**Périmètre final amendé (8 modules utils)** :
1. `lexicon_resolver.py` (411L) → package `lexicon/` (`entity_matcher.py`, `project_resolver.py`, façade `SemanticLexiconResolver` intangible) ;
2. `token_ledger.py` (350L) → package `token_ledger/` (`reporting.py`, `key_info.py`, façade `TokenLedger` allégée < 300L) ;
3-8. Audits de conformité ADR-0369 : `file_lock.py` (4×AST-04), `context_guard.py` (1×AST-04), `opencode_meter.py` (2×AST-04 + fix AST-02 L143), `context_monitor.py` (1×AST-04), `lexical_guard.py` (2×AST-04), `antigravity_meter.py` (1×AST-04).

**Prochaines étapes (chemin DoR)** : (1) créer MLOOP-106-BE et MLOOP-107-BE en Palier 1 DRAFT ; (2) mettre à jour l'EvidencePack (`verification_harness`, journal de grill) ; (3) amender la section In-Scope de la story ; (4) validation contradictoire `rubber-duck` ; (5) initialiser `Projects/mLoop/memory/FRAMEWORK_STATE.md` (ADR-0352) avant génération du plan ; (6) approbation humaine finale → `READY_FOR_DEV`.

### ✅ Clôture du chemin DoR — 2026-09-20 (12:45)

| Étape | Résultat |
| :--- | :--- |
| (1) Stories sorties du grill | ✅ MLOOP-106-BE + MLOOP-107-BE créées (`DRAFT`, `grill_me: PENDING`) |
| (2) EvidencePack | ✅ `ACTIVE` / HIGH 0.95 — 6 proofs, 6 harness, `socle_factuel_validated_by_human: true` |
| (3) In-Scope amendé | ✅ 8 modules utils (découpages + audits), harnais nommé |
| (4) Rubber-duck (ADR-0326) | ✅ **APPROUVÉ** (0 bloquant — clause OQ-101 `[API de soumission à définir]`, Trust Score 91.6) |
| (5) FRAMEWORK_STATE.md (ADR-0352) | ✅ Initialisé (baseline 257 violations consignée) |
| (5bis) struct-check (Gate C12) | ✅ Conforme |
| (6) Plan formel (ADR-0307) | ✅ Archivé : `memory/plan/implementation_plan_MLOOP-101-BE.md` (status DRAFT) |
| (6bis) Sync SSOT | ✅ `python src/swarm.py sync` exit 0 (hypergraphe 198 nœuds) |
| ✅ **BUILD exécuté** | Worker Herdr `build` (OpenCode 1.18.30) — COMPLETED : packages `lexicon/` + `token_ledger/`, 6 audits ADR-0369, fix sqlite L143, harnais 15 tests. Triple Gate **revalidé indépendamment** : 28/28 pytest, 8/8 code-check (0 violation), vibe-check 19/19, struct-check PASS → `DONE_TESTED` |
| 🚢 **Ship** | jira_sync + git commit sélectif (src/utils, tests/performance, artefacts projet) + push origin/main |
| 🏗️ **BUILD (worker-spawn)** | **COMPLETED (worker-mloop-101-be, 2026-09-20)** : packages `lexicon/` (entity_matcher 194L, project_resolver 196L) + `token_ledger/` (init 227L, reporting 105L, key_info 87L), façade lexicon_resolver 141L ; 7 audits ADR-0369 (except purgés, sqlite3 en context manager) ; harnais `tests/performance/test_utils_latency.py` (15 tests) |
| ✅ **Triple Gate §5A (revalidation indépendante)** | 28/28 tests (13 régression + 15 perf, 17.4s) \| code-check 8/8 modules **0 violation** \| struct-check PASS \| vibe-check 19/19 \| smoke CLI (focus, vibe-check) \| statut final `DONE_TESTED` |
| 🚪 **Gate 3 (DoD) franchie** | `gate-approve --gate 3 --approver Marco` (2026-09-20T13:32) → projet `STAGE_4_VALIDATE` ; `jira-sync` verrouillé en attente de Gate 4 (matrice `COMMAND_MIN_STAGE`, `src/core/lifecycle.py`) |
| 🧪 **Gate 4 (Recette QA) — VERDICT** | Suite complète : **928/931 PASS (127.7s)** \| 28/28 tests ciblés utils au vert \| **3 échecs e2e PRÉ-EXISTANTS hors périmètre** (tests/test_e2e_agent_workflow.py ×2 + test_e2e_user_prompt_simulation.py ×1) : dette `Metro_COMMERCE` 18/19 (Alignement Clé LiteLLM : active `Perso (Générale)` ≠ attendue `Metro`, EXIT 0 en shell direct) + artefact exit-code du harnais subprocess face au canary ADR-0379 (stderr CONFINEMENT 403) — aucun fichier du périmètre MLOOP-101-BE impliqué (vibe_check.py, confinement_shield.py, tests e2e non modifiés par le worker) → dette routée vers **MLOOP-108-BE** (Palier 1) |

