---
story_id: MLOOP-192-BE
dossier_status: VALIDATED
created_at: 2026-09-23T16:27:50Z
updated_at: 2026-09-23T16:27:50Z
sources_hashes:
  MLOOP-192-BE.md: 37279e140006cbcdd40ec8410a5ca0323c2a1e2e60998e3aca075e2e715c5ac1
  epic_click_cli_engine.md: 2ed4ac9977f6bd9df9b9d8290439d3e516377a1fd8445d0be6e02703ded48803
  0202-modularite-interne-agents.md: 670b0754488fea26fb0cf86e51fe8e81000ffa23efc1f6fa92dac4943cab1169
  0369-python-senior-robustness-and-resource-governance.md: 81f3525dc32e4550113f70d6aaab533ef34d528331bf29a695590fecf1bd2a113
---

# 🐣 Dossier de Preuves Documentaires & Cadrage — `MLOOP-192-BE` (Complétion Shell Native (PowerShell 5.1+ / pwsh / Bash) & Compléteurs Dynamiques)

> **Titre Fonctionnel Pur** : Complétion Shell Native (PowerShell 5.1+ / pwsh / Bash) & Compléteurs Dynamiques
> **Epic Jira** : `EPIC-19-CLICK-CLI-ENGINE` (Modernisation du Moteur CLI mLoop via Click)
> **Couche** : `backend`
> **Récit Précédent / Dépendances** : [`MLOOP-191-BE.md`](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-191-BE.md)

---

### 📂 1. Sources Physiques & Maquettes SSOT (Liens Directs Cliquables)

> 💡 *Note Headless* : Récit d'expérience développeur en ligne de commande. **N/A - Composant Headless** — pas d'interface graphique ; la source principale est l'épopée technique et l'environnement shell Windows/PowerShell réel documenté.

| Source SSOT | Nature du Document | Lien Web Officiel | Lien Repo Local (`file:///...`) |
| :--- | :--- | :--- | :--- |
| **Épopée de Cadrage** | Vision technique | N/A - Interne | [epic_click_cli_engine.md](file:///C:/Memory%20Loop/Projects/mLoop/backlog/epic_click_cli_engine.md) |
| **Architecture / ADR** | Modularité < 300L | N/A - Interne | [0202-modularite-interne-agents.md](file:///C:/Memory%20Loop/standards/adr-system/0202-modularite-interne-agents.md) |
| **Architecture / ADR** | Standards Python Senior (timeout I/O) | N/A - Interne | [0369-python-senior-robustness-and-resource-governance.md](file:///C:/Memory%20Loop/standards/adr-system/0369-python-senior-robustness-and-resource-governance.md) |

---

### ⚖️ 1.1 Matrice de Résolution des Conflits de Sources

| Conflit Identifié | Source A | Source B | Décision Retenue & Justification |
| :--- | :--- | :--- | :--- |
| *Aucun* | — | — | — |

---

### 🎙️ 2. Extraits Verbatim Sourcés (Passage-Level Grounding)

> [!NOTE]
> **Extrait 1 — Absence Historique de Complétion PowerShell (Problème Racine)**
> **Source** : [`epic_click_cli_engine.md` (Lignes 16)](file:///C:/Memory%20Loop/Projects/mLoop/backlog/epic_click_cli_engine.md)
> *« `argparse` ne fournit pas d'autocomplétion native pour PowerShell (l'environnement prédominant sur les postes Windows de développement et pour l'agent local), ni pour les entités dynamiques »*
> ➔ **Fait établi** : L'environnement de référence des développeurs mLoop est PowerShell/pwsh sous Windows — ce qui justifie l'ordre de priorité CA-1 (PowerShell + Bash) et l'exemple concret `$env:_LOOP_COMPLETE` du récit.

> [!NOTE]
> **Extrait 2 — Gain Chiffré Attendu de la Complétion Contextuelle**
> **Source** : [`MLOOP-192-BE.md` (Lignes 59-65)](file:///C:/Memory%20Loop/Projects/mLoop/backlog/stories/MLOOP-192-BE.md)
> *« Cette capacité divise par 3 le temps de saisie et évite les erreurs de casse sur les noms de projets. »*
> ➔ **Fait établi** : Le bénéfice métier est chiffré (division par 3 du temps de saisie), fondant la métrique de performance CA-4 (< 15ms) comme un seuil non arbitraire lié à l'expérience "sans lag perceptible" à la touche Tab.

> [!NOTE]
> **Extrait 3 — Exigence de Timeout / Silence Contrôlé sur les Accès I/O (ADR-0369)**
> **Source** : [`0369-python-senior-robustness-and-resource-governance.md` (Ligne 56)](file:///C:/Memory%20Loop/standards/adr-system/0369-python-senior-robustness-and-resource-governance.md)
> *« Tout bloc `except Exception: pass` avalant silencieusement une erreur est requalifié en `logger.debug("...", exc_info=True, extra={...})` afin de préserver l'auditabilité sans bloquer l'exécution. »*
> ➔ **Fait établi** : Le Pilier 3 du récit (« l'exception I/O est interceptée silencieusement en DEBUG ») est directement conforme à la Règle 4 d'ADR-0369 — aucune invention, alignement strict sur le standard constitutionnel existant.

---

### 🗄️ 3. Schéma de Données & Tables Clés (Modèle DBML / Dataverse)

N/A — Complétion shell in-memory basée sur un listing de répertoires (`Projects/`, `backlog/stories/`), aucune base de données relationnelle impliquée.

---

### 🎯 4. Contrats Déclaratifs Cibles (Endpoints REST / Matrice CTA)

* **Exemption formelle (ADR-0319)** : Composant interne du CLI mLoop — **aucune route API HTTP** consommée ni exposée (déclaré explicitement dans le récit).
* **Contrat Déclaratif Interne (Non-HTTP)** :
  - `complete_projects(ctx, param, incomplete)` : complétion dynamique des noms de projets.
  - `complete_stories(ctx, param, incomplete)` : complétion des identifiants de récits.
  - `complete_task_types(ctx, param, incomplete)` : complétion des types de tâches de gating.
  - Commande `completion-setup` : affichage de l'instruction d'activation shell.

---

### 🏁 5. Évaluation de la Frontière Active (Issue A ou Issue B)

#### ✅ Issue B — Constat Formel de Frontière Vide

Le socle factuel est complet : la nécessité PowerShell est ancrée par l'épopée, la métrique de performance (< 15ms) est justifiée par le gain "division par 3" documenté dans le récit lui-même, et le comportement de résilience silencieuse (Pilier 3) est explicitement conforme à ADR-0369 Règle 4.

👉 **Validation formelle du socle factuel confirmée** — le récit `READY_FOR_DEV` peut être développé sans arbitrage complémentaire.
