---
story_id: MLOOP-193-BE
dossier_status: VALIDATED
created_at: 2026-09-23T16:27:50Z
updated_at: 2026-09-23T16:27:50Z
sources_hashes:
  MLOOP-193-BE.md: e2b7e60225e762a5273a25062305393ff3d3b2df4da88f866d4726758a900846
  epic_click_cli_engine.md: 2ed4ac9977f6bd9df9b9d8290439d3e516377a1fd8445d0be6e02703ded48803
  0202-modularite-interne-agents.md: 670b0754488fea26fb0cf86e51fe8e81000ffa23efc1f6fa92dac4943cab1169
  0370-cli-pipeline-ssot-generator-and-anti-drift-governance.md: bdfaf163fe5728fb89d9f4cf8d2a03c5aeaa418d0c4757865d59145787b048da
---

# 🐣 Dossier de Preuves Documentaires & Cadrage — `MLOOP-193-BE` (Structuration de l'Aide par Phases Souveraines & Typage click.Path)

> **Titre Fonctionnel Pur** : Structuration de l'Aide par Phases Souveraines & Typage click.Path
> **Epic Jira** : `EPIC-19-CLICK-CLI-ENGINE` (Modernisation du Moteur CLI mLoop via Click)
> **Couche** : `backend`
> **Récit Précédent / Dépendances** : [`MLOOP-191-BE.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-191-BE.md)

---

### 📂 1. Sources Physiques & Maquettes SSOT (Liens Directs Cliquables)

> 💡 *Note Headless* : Récit de formatage d'aide terminal. **N/A - Composant Headless** — l'écran cible est un rendu texte de terminal (`--help`), non une maquette graphique. La source de vérité est le protocole SSOT des 5/6 phases souveraines et le code source du guide CLI généré.

| Source SSOT | Nature du Document | Lien Web Officiel | Lien Repo Local (`file:///...`) |
| :--- | :--- | :--- | :--- |
| **Épopée de Cadrage** | Vision technique | N/A - Interne | [epic_click_cli_engine.md](file:///C:/Memory%20Loop/Projects/mLoop/backlog/epic_click_cli_engine.md) |
| **Protocole SSOT** | Guide CLI généré | N/A - Interne | [CLI_PIPELINE_GUIDE.md](file:///C:/Memory%20Loop/standards/protocols/CLI_PIPELINE_GUIDE.md) |
| **Architecture / ADR** | Modularité < 300L | N/A - Interne | [0202-modularite-interne-agents.md](file:///C:/Memory%20Loop/standards/adr-system/0202-modularite-interne-agents.md) |
| **Architecture / ADR** | Générateur SSOT Anti-Drift | N/A - Interne | [0370-cli-pipeline-ssot-generator-and-anti-drift-governance.md](file:///C:/Memory%20Loop/standards/adr-system/0370-cli-pipeline-ssot-generator-and-anti-drift-governance.md) |

---

### ⚖️ 1.1 Matrice de Résolution des Conflits de Sources

| Conflit Identifié | Source A | Source B | Décision Retenue & Justification |
| :--- | :--- | :--- | :--- |
| **Nombre de phases** | Récit mentionne 6 phases (Phase 0 à Phase 5) dans le regroupement `format_commands()` | AGENTS.md / ADR-0375 définissent le cycle en 5 phases universelles (INGEST➔PLAN➔BUILD➔VALIDATE➔SHIP) | **Décision** : Le regroupement d'aide terminal (`--help`) reste un enjeu strictement d'affichage UX/ergonomie et non de gouvernance de cycle de vie. Le récit ne redéfinit pas le modèle de phases constitutionnel (ADR-0375 fait foi comme SSOT du cycle) ; il s'agit d'un regroupement visuel hérité de l'historique du guide CLI antérieur à l'amendement. Aucune correction requise à ce stade car aucun contrôle de gate n'est affecté — c'est une observation à consigner en recommandation Sentinel, non un blocage. |

---

### 🎙️ 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> [!NOTE]
> **Extrait 1 — Aide Monolithique Sans Structure de Phase (Problème Racine)**
> **Source** : [`epic_click_cli_engine.md` (Lignes 17)](file:///C:/Memory%20Loop/Projects/mLoop/backlog/epic_click_cli_engine.md)
> *« L'aide par défaut (`--help`) affiche une liste alphabétique dense de 58 commandes sans faire émerger les 6 phases souveraines du cycle de développement mLoop (Phase 0 Inception à Phase 5 Ship). »*
> ➔ **Fait établi** : Le défaut actuel d'ergonomie (liste alphabétique brute) est documenté et constitue la baseline comparative pour CA-1 (regroupement par phase).

> [!NOTE]
> **Extrait 2 — Existence Physique du Guide de Référence des Phases**
> **Source** : [`MLOOP-193-BE.md` (Ligne 62)](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-193-BE.md)
> *« le terminal affiche une cartographie alignée sur `standards/protocols/CLI_PIPELINE_GUIDE.md` »*
> ➔ **Fait établi** : Le fichier `CLI_PIPELINE_GUIDE.md` existe réellement sous `standards/protocols/` (confirmé physiquement) et sert de référentiel de regroupement pour `PhaseHelpFormatter`, éliminant tout risque de dérive documentaire (ADR-0370).

> [!NOTE]
> **Extrait 3 — Plafond de Modularité RULE-AST-01 (ADR-0202)**
> **Source** : [`0202-modularite-interne-agents.md` (Ligne 18)](file:///C:/Memory%20Loop/standards/adr-system/0202-modularite-interne-agents.md)
> *« Nombre de lignes | > 300 lignes | Refactoring obligatoire par extraction de sous-modules »*
> ➔ **Fait établi** : CA-6 (plafond de 300 lignes pour `formatter.py`) découle directement de la règle constitutionnelle applicable à tout nouveau module.

---

### 🗄️ 3. Schéma de Données & Tables Clés (Modèle DBML / Dataverse)

N/A — Récit de formatage d'affichage terminal, aucune persistance de données.

---

### 🎯 4. Contrats Déclaratifs Cibles (Endpoints REST / Matrice CTA)

* **Exemption formelle (ADR-0319)** : Composant interne du formateur d'aide CLI — **aucune route API HTTP** consommée ni exposée (déclaré explicitement dans le récit).
* **Contrat Déclaratif Interne (Non-HTTP)** :
  - `PhaseHelpFormatter(click.HelpFormatter)` : surcharge de `format_commands()`.
  - `path_exists(file_okay, dir_okay)` : validateur de chemin retournant `pathlib.Path`.
  - `dir_exists()` : validateur de répertoire.
  - `choice_param(enum_or_list)` : encapsulation `click.Choice` insensible à la casse.

---

### 🏁 5. Évaluation de la Frontière Active (Issue A ou Issue B)

#### ✅ Issue B — Constat Formel de Frontière Vide (avec observation consignée en §1.1)

Le socle factuel est complet : la baseline UX actuelle est documentée, le guide de référence `CLI_PIPELINE_GUIDE.md` existe physiquement, et le plafond de lignes est ancré dans ADR-0202. Une divergence terminologique mineure (6 phases d'affichage historique vs 5 phases de gouvernance ADR-0375) est notée en §1.1 sans impact bloquant sur le développement — elle relève d'un choix d'ergonomie d'affichage, pas d'une redéfinition du cycle de vie gouverné.

👉 **Validation formelle du socle factuel confirmée** — le récit `READY_FOR_DEV` peut être développé sans arbitrage complémentaire ; recommandation Sentinel : envisager un alignement terminologique futur entre le regroupement d'aide et les 5 phases ADR-0375 (non bloquant).
