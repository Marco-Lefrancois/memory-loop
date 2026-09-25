---
story_id: MLOOP-194-BE
dossier_status: VALIDATED
created_at: 2026-09-23T16:27:50Z
updated_at: 2026-09-23T16:27:50Z
sources_hashes:
  MLOOP-194-BE.md: 079c0c35aa587abc5478e892e4a146748b5d288ccce6c68718b674af8763e6981
  epic_click_cli_engine.md: 2ed4ac9977f6bd9df9b9d8290439d3e516377a1fd8445d0be6e02703ded48803
  0202-modularite-interne-agents.md: 670b0754488fea26fb0cf86e51fe8e81000ffa23efc1f6fa92dac4943cab1169
  0369-python-senior-robustness-and-resource-governance.md: 81f3525dc32e4550113f70d6aaab533ef34d528331bf29a695590fecf1bd2a113
---

# 🐣 Dossier de Preuves Documentaires & Cadrage — `MLOOP-194-BE` (Harnais de Test In-Process CliRunner & Validation Non-Régression)

> **Titre Fonctionnel Pur** : Harnais de Test In-Process CliRunner & Validation Non-Régression
> **Epic Jira** : `EPIC-19-CLICK-CLI-ENGINE` (Modernisation du Moteur CLI mLoop via Click)
> **Couche** : `backend`
> **Récit Précédent / Dépendances** : [`MLOOP-190-BE.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-190-BE.md), [`MLOOP-191-BE.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-191-BE.md)

---

### 📂 1. Sources Physiques & Maquettes SSOT (Liens Directs Cliquables)

> 💡 *Note Headless* : Récit de harnais de test unitaire. **N/A - Composant Headless** — aucune interface visuelle. La source principale est le code source du routeur actuel et le contrat de non-régression défini dans l'épopée.

| Source SSOT | Nature du Document | Lien Web Officiel | Lien Repo Local (`file:///...`) |
| :--- | :--- | :--- | :--- |
| **Épopée de Cadrage** | Vision technique & DoD | N/A - Interne | [epic_click_cli_engine.md](file:///C:/Memory%20Loop/Projects/mLoop/backlog/epic_click_cli_engine.md) |
| **Architecture / ADR** | Modularité < 300L | N/A - Interne | [0202-modularite-interne-agents.md](file:///C:/Memory%20Loop/standards/adr-system/0202-modularite-interne-agents.md) |
| **Architecture / ADR** | Failure Contract (parametrize/raises) | N/A - Interne | [0369-python-senior-robustness-and-resource-governance.md](file:///C:/Memory%20Loop/standards/adr-system/0369-python-senior-robustness-and-resource-governance.md) |
| **Code Source Legacy** | Point d'entrée `execute_cli()` | N/A - Interne | [router.py](file:///C:/Memory%20Loop/src/commands/router.py) |

---

### ⚖️ 1.1 Matrice de Résolution des Conflits de Sources

| Conflit Identifié | Source A | Source B | Décision Retenue & Justification |
| :--- | :--- | :--- | :--- |
| *Aucun* | — | — | — |

---

### 🎙️ 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> [!NOTE]
> **Extrait 1 — Fragilité du Harnais Subprocess Legacy (Problème Racine)**
> **Source** : [`MLOOP-194-BE.md` (Lignes 55-58)](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-194-BE.md)
> *« Chaque invocation recrée un interpréteur Python, initialise les modules et coûte entre 300ms et 800ms. »*
> ➔ **Fait établi** : Le coût mesuré du harnais `subprocess.run` legacy (300-800ms/appel) fonde objectivement le seuil de performance CA-5 (suite complète < 2.0 secondes en in-process).

> [!NOTE]
> **Extrait 2 — Critère de Sortie d'Épopée sur la Couverture de Tests**
> **Source** : [`epic_click_cli_engine.md` (Ligne 123)](file:///C:/Memory%20Loop/Projects/mLoop/backlog/epic_click_cli_engine.md)
> *« Couverture des tests : Suite de tests `tests/test_click_cli_engine.py` 100% verte sur les commandes vitales (`vibe-check`, `gate-approve`, `sync`, `crawl`, `lifecycle-status`). »*
> ➔ **Fait établi** : La liste exacte des commandes vitales à couvrir (5 commandes de l'épopée + `worker-spawn` ajoutée dans le récit CA-2) est directement tracée à la Definition of Done de l'épopée EPIC-19, sans invention.

> [!NOTE]
> **Extrait 3 — Exigence de Failure Contract Systématique (ADR-0369 Règle 5)**
> **Source** : [`0369-python-senior-robustness-and-resource-governance.md` (Ligne 59)](file:///C:/Memory%20Loop/standards/adr-system/0369-python-senior-robustness-and-resource-governance.md)
> *« Les suites de tests (`tests/`) ne doivent plus se limiter au scénario nominal (*happy path*). Les tests d'intégration et de validation d'API doivent tester systématiquement les codes d'erreur »*
> ➔ **Fait établi** : Le Pilier 2 et Pilier 3 du récit (codes de sortie 1, 130, capture d'exception runtime) traduisent directement l'obligation de couverture du Failure Contract imposée par ADR-0369 Règle 5.

---

### 🗄️ 3. Schéma de Données & Tables Clés (Modèle DBML / Dataverse)

N/A — Suite de tests in-process, aucune persistance en base de données.

---

### 🎯 4. Contrats Déclaratifs Cibles (Endpoints REST / Matrice CTA)

* **Exemption formelle (ADR-0319)** : Composant de test interne — **aucune route API HTTP** consommée ni exposée (déclaré explicitement dans le récit).
* **Contrat Déclaratif Interne (Non-HTTP)** :
  - Suite `tests/test_click_cli_engine.py` exploitant `click.testing.CliRunner`.
  - Couverture des 6 commandes vitales avec assertions sur `result.exit_code`.
  - Benchmark comparatif in-process vs subprocess legacy.

---

### 🏁 5. Évaluation de la Frontière Active (Issue A ou Issue B)

#### ✅ Issue B — Constat Formel de Frontière Vide

Le socle factuel est complet : le coût du harnais legacy est chiffré dans le récit lui-même, la liste des commandes vitales est tracée à la DoD de l'épopée, et les exigences de couverture de rupture (Pilier 2/3) sont alignées sur ADR-0369 Règle 5.

👉 **Validation formelle du socle factuel confirmée** — le récit `READY_FOR_DEV` peut être développé sans arbitrage complémentaire.
