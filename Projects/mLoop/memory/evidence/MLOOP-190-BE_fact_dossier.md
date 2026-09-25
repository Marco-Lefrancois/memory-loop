---
story_id: MLOOP-190-BE
dossier_status: VALIDATED
created_at: 2026-09-23T16:27:50Z
updated_at: 2026-09-23T16:27:50Z
sources_hashes:
  MLOOP-190-BE.md: 9b3838cdc824ae74d0cc3dbab61da5ee1955fa10af9351a11dfc2eaed8beedc1
  epic_click_cli_engine.md: 2ed4ac9977f6bd9df9b9d8290439d3e516377a1fd8445d0be6e02703ded48803
  0202-modularite-interne-agents.md: 670b0754488fea26fb0cf86e51fe8e81000ffa23efc1f6fa92dac4943cab1169
  0339-project-lifecycle-stages-governance-gates.md: f4f481dc57d2afd3f8176da6e1edd6521a24dd21b73d3173465a4bd0702e4e5b
  0369-python-senior-robustness-and-resource-governance.md: 81f3525dc32e4550113f70d6aaab533ef34d528331bf29a695590fecf1bd2a113
  router.py: cdec8649ff2f194dd69c2a4cbaed0f44c2bb3a918c57dd721cbd56789b2c696b
---

# 🐣 Dossier de Preuves Documentaires & Cadrage — `MLOOP-190-BE` (Infrastructure de Contexte Click & Middleware d'Enforcement des Lifecycle Gates)

> **Titre Fonctionnel Pur** : Infrastructure de Contexte Click & Middleware d'Enforcement des Lifecycle Gates
> **Epic Jira** : `EPIC-19-CLICK-CLI-ENGINE` (Modernisation du Moteur CLI mLoop via Click)
> **Couche** : `backend`
> **Récit Précédent / Dépendances** : Aucune (récit racine de l'épopée — socle du contexte d'exécution)

---

### 📂 1. Sources Physiques & Maquettes SSOT (Liens Directs Cliquables)

> 💡 *Note Headless* : Récit d'infrastructure interne au moteur CLI (`src/cli/click_engine/`). **N/A - Composant Headless** — aucune interface visuelle. La source principale est le code source physique du routeur historique et l'épopée de cadrage technique.

| Source SSOT | Nature du Document | Lien Web Officiel | Lien Repo Local (`file:///...`) |
| :--- | :--- | :--- | :--- |
| **Épopée de Cadrage** | Vision technique | N/A - Interne | [epic_click_cli_engine.md](file:///C:/Memory%20Loop/Projects/mLoop/backlog/epic_click_cli_engine.md) |
| **Architecture / ADR** | Modularité < 300L | N/A - Interne | [0202-modularite-interne-agents.md](file:///C:/Memory%20Loop/standards/adr-system/0202-modularite-interne-agents.md) |
| **Architecture / ADR** | Quality Gate Enforcement | N/A - Interne | [0339-project-lifecycle-stages-governance-gates.md](file:///C:/Memory%20Loop/standards/adr-system/0339-project-lifecycle-stages-governance-gates.md) |
| **Architecture / ADR** | Standards Python Senior | N/A - Interne | [0369-python-senior-robustness-and-resource-governance.md](file:///C:/Memory%20Loop/standards/adr-system/0369-python-senior-robustness-and-resource-governance.md) |
| **Code Source Legacy** | Point d'interception actuel | N/A - Interne | [router.py](file:///C:/Memory%20Loop/src/commands/router.py) |

---

### ⚖️ 1.1 Matrice de Résolution des Conflits de Sources

Aucun conflit détecté entre l'épopée de cadrage, les ADR référencés et le code source legacy inspecté : les trois sources convergent sur la nécessité d'un middleware unifié d'enforcement.

| Conflit Identifié | Source A | Source B | Décision Retenue & Justification |
| :--- | :--- | :--- | :--- |
| *Aucun* | — | — | — |

---

### 🎙️ 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> [!NOTE]
> **Extrait 1 — Gestion Impérative du Contexte et des Portes de Sécurité (Problème Racine)**
> **Source** : [`epic_click_cli_engine.md` (Lignes 18)](file:///C:/Memory%20Loop/Projects/mLoop/backlog/epic_click_cli_engine.md)
> *« La résolution du projet, le chargement de `LoopState` et le contrôle pré-vol des *Lifecycle Gates* (ADR-0339) sont codés de manière procédurale dans `_run_cli()`. »*
> ➔ **Fait établi** : Le garde-fou de cycle de vie est aujourd'hui centralisé dans une seule fonction procédurale (`_run_cli()`), justifiant l'encapsulation objet demandée par MLOOP-190-BE.

> [!NOTE]
> **Extrait 2 — Interception Réelle du Contrôle Lifecycle Gate dans le Code Legacy**
> **Source** : [`router.py` (Lignes 162-182)](file:///C:/Memory%20Loop/src/commands/router.py)
> *« allowed, reason = ProjectLifecycleManager.can_execute_command( project_path, args.command, task_type=task_type ) if not allowed: ZeroFluffConsole.error(f"[LIFECYCLE GATE VIOLATION] {reason}") »*
> ➔ **Fait établi** : Le mécanisme actuel invoque déjà `ProjectLifecycleManager.can_execute_command()` et émet le message `[LIFECYCLE GATE VIOLATION]` — CA-4 du récit prescrit la reproduction fidèle de ce contrat sous Click, confirmant la faisabilité technique sans invention de nouvelle API.

> [!NOTE]
> **Extrait 3 — Plafond de Modularité RULE-AST-01 (ADR-0202)**
> **Source** : [`0202-modularite-interne-agents.md` (Ligne 18)](file:///C:/Memory%20Loop/standards/adr-system/0202-modularite-interne-agents.md)
> *« Nombre de lignes | > 300 lignes | Refactoring obligatoire par extraction de sous-modules »*
> ➔ **Fait établi** : CA-6 (plafond de 300 lignes pour `context.py`) est directement dérivé de la règle constitutionnelle RULE-AST-01 et n'est pas un critère arbitraire.

---

### 🗄️ 3. Schéma de Données & Tables Clés (Modèle DBML / Dataverse)

N/A — Récit d'infrastructure CLI en mémoire (aucune persistance en base de données relationnelle). Le seul "modèle" pertinent est la structure interne de l'objet de contexte tel que défini au §In-Scope du récit (`project_name`, `project_path`, `state`, `timing_start`), non un schéma de stockage persistant.

---

### 🎯 4. Contrats Déclaratifs Cibles (Endpoints REST / Matrice CTA)

* **Exemption formelle (ADR-0319)** : Ce récit est un composant interne du moteur CLI mLoop (`src/cli/click_engine/`). **Aucune route API HTTP n'est consommée ni exposée.** Conformément à la Matrice des Contrats API du récit (§ "Matrice des Contrats API"), cette exemption est déjà déclarée explicitement dans le corps du récit `MLOOP-190-BE.md`.
* **Contrat Déclaratif Interne (Non-HTTP)** — pour mémoire, sans prescription de syntaxe :
  - Classe `MLoopContext` : expose `project_name`, `project_path`, `state`, `timing_start`.
  - Décorateur `@pass_mloop_context` : injection sécurisée du contexte en premier argument.
  - Fonction `lifecycle_gate_guard(ctx, cmd_name)` : invoque `ProjectLifecycleManager.can_execute_command()`.

---

### 🏁 5. Évaluation de la Frontière Active (Issue A ou Issue B)

#### ✅ Issue B — Constat Formel de Frontière Vide

Tous les faits nécessaires à la validation du récit `MLOOP-190-BE` sont vérifiés, documentés et exempts de zone d'ombre :
- Le point d'interception legacy (`router.py:_run_cli`) est cité verbatim et confirme le contrat `ProjectLifecycleManager.can_execute_command()`.
- L'exemption API (ADR-0319) est correctement déclarée dans le récit.
- Le plafond de 300 lignes (CA-6) est ancré dans ADR-0202 (RULE-AST-01).
- Les 4 Piliers Gherkin couvrent Nominal, Exceptions (violation de gate), Résilience (alias non canonique via `SemanticLexiconResolver`) et UX (message clair sans traceback).

👉 **Validation formelle du socle factuel confirmée** — le récit `READY_FOR_DEV` est solidement ancré dans les sources physiques du dépôt mLoop, sans invention ni route API fictive.
