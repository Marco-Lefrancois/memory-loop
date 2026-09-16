# ADR-0370 : Générateur Automatique du Guide CLI SSOT & Gouvernance Anti-Drift Déterministe

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-15
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Registre CLI (`src/commands/_registry.py`), Générateur (`src/pipelines/guide_generator.py`), Guardrail Pré-vol (`src/pipelines/vibe_check.py`), Guide Normatif SSOT (`standards/protocols/CLI_PIPELINE_GUIDE.md`)
- **Autorité** : [ADR-0001](0001-python-state-graph.md), [ADR-0322](0322-three-pillars-knowledge-stack-and-boot-sequence.md), [ADR-0339](0339-project-lifecycle-stages-governance-gates.md), [ADR-0360](0360-google-notebooklm-ssot-synchronization.md), [ADR-0369](0369-python-senior-robustness-and-resource-governance.md)

---

## 1. Contexte & Problématique

Le backend d'état **Memory Loop (mLoop)** expose une interface en ligne de commande unifiée (`python src/swarm.py`) pilotée par un registre déclaratif centralisé (`src/commands/_registry.py`). Au fil des évolutions architecturales majeures (Workers Herdr ADR-0346, NotebookLM ADR-0360, Moteur Tabulaire CSV ADR-0368, Plannotator, et Robustesse Python ADR-0369), le registre s'est enrichi jusqu'à compter **103 commandes actives**.

Cependant, le document de référence normatif [`standards/protocols/CLI_PIPELINE_GUIDE.md`](file:///c:/Memory%20Loop/standards/protocols/CLI_PIPELINE_GUIDE.md) — cité dans la constitution `AGENTS.md` (ligne 14), `GEMINI.md`, `CLAUDE.md` et exporté dans Google NotebookLM — était maintenu manuellement. Un audit d'intégrité a révélé une **dérive documentaire critique** :
1. Seules 55 commandes étaient documentées, laissant **48 commandes invisibles** dans le guide officiel.
2. Des pans fonctionnels critiques (moteur CSV, travailleurs d'audit contradictoire Red Team, ponts NotebookLM, gestionnaires de hooks pré-compaction) n'étaient documentés que dans le code source Python.
3. La documentation statique présentait un risque permanent de divergence à chaque ajout ou modification de commande dans `_registry.py`.

---

## 2. Décisions d'Architecture

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│             GOUVERNANCE ANTI-DRIFT DÉTERMINISTE DU GUIDE CLI SSOT (ADR-0370)           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   src/commands/_registry.py (Code Python SSOT - 103 Commandes)                         │
│             │                                                                          │
│             ├──> guide_generator.py (Compilation Déterministe AST)                     │
│             │          │                                                               │
│             │          ▼                                                               │
│             │    standards/protocols/CLI_PIPELINE_GUIDE.md (100% à jour)               │
│             │                                                                          │
│             ├──> swarm.py guide --sync (Déclenchement Manuel / Développeur)            │
│             │                                                                          │
│             └──> vibe-check (Check 15 : Guardrail Pré-vol & Auto-Healing Déterministe) │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Source de Vérité Unique (Code-First SSOT)
Le dictionnaire `COMMANDS` dans `src/commands/_registry.py` constitue la **Source Unique de Vérité physique** pour l'intégralité des commandes, descriptions, arguments et permissions du pipeline. Aucune commande ne peut être documentée si elle n'est pas déclarée dans `_registry.py`.

### 2. Moteur de Compilation Déterministe (`src/pipelines/guide_generator.py`)
Un générateur dédié segmente automatiquement les 103 commandes à travers les 6 phases du cycle de vie mLoop (Phase 0 SOW, Phase 1 SPEC, Phase 2 PLAN, Phase 3 BUILD, Phase 4 VALIDATE, Phase 5 SHIP) plus la phase Transverse, générant des tables Markdown exhaustives incluant les paramètres et les artefacts de sortie.

### 3. Synchronisation CLI (`python src/swarm.py guide --sync`)
L'option `--sync` est greffée directement sur la commande universelle `guide`. Elle permet à tout développeur ou agent de régénérer instantanément le guide Markdown après toute modification du registre.

### 4. Guardrail Pré-Vol & Auto-Healing Déterministe (`vibe-check` Check 15)
Le 15ᵉ contrôle du guardrail pré-vol `vibe-check` audite la parité exacte entre le registre Python et `CLI_PIPELINE_GUIDE.md`. En cas de détection d'une seule commande manquante ou d'un décalage de version, le guardrail **auto-guérit immédiatement** le guide en le régénérant avant d'émettre son verdict `PASS`.

### 5. Règle Constitutionnelle dans `AGENTS.md`
Toute modification apportée à `src/commands/_registry.py` DOIT être immédiatement suivie de l'exécution de `python src/swarm.py guide --sync` ou validée par `python src/swarm.py vibe-check`.

---

## 3. Conséquences & Invariants

- **Zéro Dérive Documentaire** : Le fichier `standards/protocols/CLI_PIPELINE_GUIDE.md` est garanti en parité 100% stricte avec l'état réel du code source.
- **Auto-Réparation Silencieuse & Robuste** : Si un agent omet de régénérer le guide après avoir créé une commande, le premier `vibe-check` restaure la parité sans bloquer inutilement l'utilisateur.
- **Visibilité Totale des Capacités** : Les 103 commandes réelles sont désormais indexées, documentées et directement interrogeables par les agents et les humains.
