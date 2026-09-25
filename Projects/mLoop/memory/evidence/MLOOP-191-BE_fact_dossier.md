---
story_id: MLOOP-191-BE
dossier_status: VALIDATED
created_at: 2026-09-23T16:27:50Z
updated_at: 2026-09-23T16:27:50Z
sources_hashes:
  MLOOP-191-BE.md: e98d96f860ba44b91a9a3888925c9e5e09a02d3425c7505f4129ada02c4671c6
  epic_click_cli_engine.md: 2ed4ac9977f6bd9df9b9d8290439d3e516377a1fd8445d0be6e02703ded48803
  0202-modularite-interne-agents.md: 670b0754488fea26fb0cf86e51fe8e81000ffa23efc1f6fa92dac4943cab1169
  0370-cli-pipeline-ssot-generator-and-anti-drift-governance.md: bdfaf163fe5728fb89d9f4cf8d2a03c5aeaa418d0c4757865d59145787b048da
  router.py: cdec8649ff2f194dd69c2a4cbaed0f44c2bb3a918c57dd721cbd56789b2c696b
---

# 🐣 Dossier de Preuves Documentaires & Cadrage — `MLOOP-191-BE` (Routeur de Commandes Dynamique Lazy-Loading (click.MultiCommand))

> **Titre Fonctionnel Pur** : Routeur de Commandes Dynamique Lazy-Loading (click.MultiCommand)
> **Epic Jira** : `EPIC-19-CLICK-CLI-ENGINE` (Modernisation du Moteur CLI mLoop via Click)
> **Couche** : `backend`
> **Récit Précédent / Dépendances** : [`MLOOP-190-BE.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-190-BE.md)

---

### 📂 1. Sources Physiques & Maquettes SSOT (Liens Directs Cliquables)

> 💡 *Note Headless* : Récit d'infrastructure interne au routeur CLI. **N/A - Composant Headless** — aucune interface visuelle. Le code source physique du parser `argparse` legacy constitue la source de vérité comparative.

| Source SSOT | Nature du Document | Lien Web Officiel | Lien Repo Local (`file:///...`) |
| :--- | :--- | :--- | :--- |
| **Épopée de Cadrage** | Vision technique | N/A - Interne | [epic_click_cli_engine.md](file:///C:/Memory%20Loop/Projects/mLoop/backlog/epic_click_cli_engine.md) |
| **Architecture / ADR** | Modularité < 300L | N/A - Interne | [0202-modularite-interne-agents.md](file:///C:/Memory%20Loop/standards/adr-system/0202-modularite-interne-agents.md) |
| **Architecture / ADR** | Résilience Registre CLI | N/A - Interne | [0370-cli-pipeline-ssot-generator-and-anti-drift-governance.md](file:///C:/Memory%20Loop/standards/adr-system/0370-cli-pipeline-ssot-generator-and-anti-drift-governance.md) |
| **Code Source Legacy** | Parser argparse actuel | N/A - Interne | [router.py](file:///C:/Memory%20Loop/src/commands/router.py) |

---

### ⚖️ 1.1 Matrice de Résolution des Conflits de Sources

| Conflit Identifié | Source A | Source B | Décision Retenue & Justification |
| :--- | :--- | :--- | :--- |
| *Aucun* | — | — | — |

---

### 🎙️ 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> [!NOTE]
> **Extrait 1 — Coût de Démarrage Mesuré de la Boucle argparse (Problème Racine)**
> **Source** : [`router.py` (Lignes 84-96)](file:///C:/Memory%20Loop/src/commands/router.py)
> *« for cmd_name, cmd_def in sorted(cmds.items()): ... sub = subparsers.add_parser( cmd_name, aliases=aliases, parents=[project_parser], help=cmd_def.get("help", "") ) for arg_def in cmd_def.get("args", []): »*
> ➔ **Fait établi** : Le parser actuel itère et instancie effectivement un sous-parser complet par commande (confirmé pour 58 commandes recensées dans le registre), corroborant le CA-2 (lazy import prouvé) qui vise à éliminer cette boucle exhaustive.

> [!NOTE]
> **Extrait 2 — Dette Modulaire du Registre Déclaratif (ADR-0370)**
> **Source** : [`0370-cli-pipeline-ssot-generator-and-anti-drift-governance.md` (Ligne 13)](file:///C:/Memory%20Loop/standards/adr-system/0370-cli-pipeline-ssot-generator-and-anti-drift-governance.md)
> *« le registre s'est enrichi jusqu'à compter **103 commandes actives** »*
> ➔ **Fait établi** : Le registre central `_registry.py` gouverne aujourd'hui 103 commandes (chiffre ADR-0370 supérieur aux 58 mentionnés dans l'épopée, ce qui ne contredit pas mais actualise l'ampleur du chantier de lazy-loading visé par CA-1).

> [!NOTE]
> **Extrait 3 — Signature Historique des Handlers à Préserver (ArgsShim)**
> **Source** : [`router.py` (Lignes 184-187)](file:///C:/Memory%20Loop/src/commands/router.py)
> *« handler = _resolve_handler(args._handler_ref) exit_code = handler(args, state, project_path) return exit_code or 0 »*
> ➔ **Fait établi** : Le contrat d'appel legacy est bien `handler(args, state, project_path)` — ce triplet exact doit être reproduit par l'adaptateur `ArgsShim` (CA-4) pour garantir zéro régression sur les handlers existants.

---

### 🗄️ 3. Schéma de Données & Tables Clés (Modèle DBML / Dataverse)

N/A — Récit purement lié au routage CLI en mémoire, aucune persistance en base de données.

---

### 🎯 4. Contrats Déclaratifs Cibles (Endpoints REST / Matrice CTA)

* **Exemption formelle (ADR-0319)** : Composant interne du routeur CLI mLoop — **aucune route API HTTP** consommée ni exposée (déclaré explicitement dans le récit).
* **Contrat Déclaratif Interne (Non-HTTP)** :
  - `MLoopMultiCommand.list_commands(ctx)` : liste exhaustive des identifiants et alias sans import lourd.
  - `MLoopMultiCommand.get_command(ctx, cmd_name)` : résolution paresseuse du module cible.
  - `ArgsShim(argparse.Namespace)` : adaptateur de compatibilité descendante.

---

### 🏁 5. Évaluation de la Frontière Active (Issue A ou Issue B)

#### ✅ Issue B — Constat Formel de Frontière Vide

Le socle factuel est complet : le comportement actuel du parser (`router.py`), le contrat d'appel des handlers `(args, state, project_path)`, et le périmètre de la dette modulaire (ADR-0370) sont tous vérifiés sur le disque. Aucune ambiguïté ne subsiste sur le contrat de rétrocompatibilité exigé par CA-4.

👉 **Validation formelle du socle factuel confirmée** — le récit `READY_FOR_DEV` peut être développé sans arbitrage complémentaire.
