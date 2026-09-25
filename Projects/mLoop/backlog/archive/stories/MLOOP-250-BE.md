---
id: MLOOP-250-BE
jira_key: ''
epic_key: EPIC-25-OPENCODE-ECOSYSTEM-HARNESS
type: Feature
title: "Parité Miroir Automatique des Personas (.agents/agents/ -> .opencode/agents/)"
tags:
- opencode
- personas
- mirror-sync
- subagent
- backend
origin: SPEC_SLICING
source_ref: EPIC-25-§3
macro_size: S
status: SHIPPED
grill_me: DONE
invest_score: 6/6
validated_by: Marco (PO)
validated_at: '2026-09-25'
layer: backend
blocked_by: []
created_at: '2026-09-24'
updated_at: '2026-09-25'
---

# 📖 MLOOP-250-BE : Parité Miroir Automatique des Personas (.agents/agents/ -> .opencode/agents/)

## Description
**En tant que** Développeur et Agent IA opérant avec OpenCode sur mLoop,  
**je veux** que les personas certifiés mLoop (`craftsman`, `critic`, `explorer`, `planner`, `sentinel`) soient automatiquement projetés dans `.opencode/agents/`,  
**afin de** pouvoir invoquer directement ces rôles spécialisés via `@mention` dans OpenCode tout en préservant le confinement des compétences et les directives SSOT.

---

## Contexte & Périmètre

### Contexte Métier
mLoop dispose d'un jeu de personas normalisés sous `.agents/agents/*.md` régis par `AGENTS.md` et les guardrails de confinement (ADR-0379). OpenCode (v1.18.30+) propose un système multi-agents déclaratif basé sur des fichiers Markdown sous `.opencode/agents/`. Ce récit assure la parité miroir bidirectionnelle automatique sans intervention manuelle.

**Décisions Grill-Me (2026-09-25) :**
- `craftsman` est déclaré en tant qu'agent de travail standard (`primary`), tandis que les rôles spécialisés (`critic`, `explorer`, `planner`, `sentinel`) sont configurés en `mode: subagent` avec profondeur bornée (`subagent_depth: 1`).
- Confinement étanche (ADR-0379) : filtrage automatique lors de la génération de toute compétence interdite (ex. `forbidden-skill-canary` pour `explorer`).
- Intégration transparente dans le cycle `mloop sync` et le hook pré-vol Vibe-Check.

### In-Scope
- Développement du moteur de synchronisation miroir `src/bridges/opencode/mirror_sync.py` (≤ 300 lignes, ADR-0202).
- Parsing des manifestes Markdown mLoop sous `.agents/agents/*.md` (extraction nom, description, instructions, compétences autorisées).
- Génération déterministe des manifestes compatibles OpenCode sous `.opencode/agents/<persona>.md`.
- Confinement des outils et compétences autorisées par persona selon les directives SSOT.
- Intégration du déclencheur dans le pipeline de synchronisation `src/swarm.py sync`.

### Out-of-Scope
- Modification du binaire ou du runtime interne d'OpenCode.
- Invocations automatiques ou cascades récursives d'agents non supervisées.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Moteur de Projection Miroir — PersonasSyncEngine
* **Entrée Métier** : Répertoire source `.agents/agents/` et cible `.opencode/agents/`.
* **Règles d'admissibilité & Validation** : Tout fichier source `.agents/agents/*.md` valide est parsé. Si le dossier cible n'existe pas, il est créé automatiquement de manière idempotente.
* **Traitement & Algorithme Métier** :
  - Extraction du frontmatter et du corps Markdown.
  - `craftsman` configuré avec `mode: primary`.
  - `critic`, `explorer`, `planner`, `sentinel` configurés avec `mode: subagent` et `subagent_depth: 1`.
  - Filtrage des compétences : exclusion stricte des skills prohibées pour chaque rôle.
* **Résultat Métier & Mutations** : Fichiers `.opencode/agents/<nom>.md` écrits sur disque avec hash d'intégrité.

#### 2. Contrôle d'Intégrité & Vibe-Check
* **Traitement** : Vérification que chaque agent source possède sa réplique miroir exacte dans `.opencode/agents/`.
* **Cas de Rejet Métier** : Si une désynchronisation ou une compétence confinée est détectée, le contrôle retourne une alerte bloquante.

---

## Règles d'affaires

- **Confinement SSOT Inviolable** : Aucune compétence interdite dans `.agents/agents/` ne peut fuiter dans le fichier miroir `.opencode/agents/` (ADR-0379).
- **Idempotence Absolue** : Deux exécutions successives de synchronisation sans modification source produisent zéro diff Git.
- **Plafond Modulaire AST** : Le module `src/bridges/opencode/mirror_sync.py` doit respecter strictement $\le 300$ lignes et $\le 15$ Ko (ADR-0202).

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Personas mLoop** : `.agents/agents/*.md`
- 📂 **Configuration OpenCode** : `.opencode/opencode.json` (MLOOP-220-BE)
- 🏛️ **ADR** : [ADR-0377](../../../standards/adr-system/0377-runtimes-agents-aval-et-herdr-operationnels.md) · [ADR-0379](../../../standards/adr-system/0379-standard-architecture-hexagonale-anti-leakage.md) · [ADR-0202](../../../standards/adr-system/0202-modularite-interne-agents.md)
- 📋 **Epic** : [`epics/epic_opencode_ecosystem_harness.md`](../epics/epic_opencode_ecosystem_harness.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Parité Miroir des Personas OpenCode

  Scénario: Pilier 1 - Nominal (Happy path) : Synchronisation complète des personas
    Étant donné les manifestes valides sous .agents/agents/ pour craftsman, explorer, critic
    Quand j'exécute la synchronisation miroir via PersonasSyncEngine.sync_all()
    Alors les fichiers correspondants sont générés sous .opencode/agents/
    Et craftsman possède "mode: primary"
    Et explorer possède "mode: subagent" et "subagent_depth: 1"

  Scénario: Pilier 2 - Exceptions (Cas d'erreur) : Manifeste source corrompu ou illisible
    Étant donné un fichier .agents/agents/corrupted.md sans frontmatter YAML valide
    Quand j'exécute la synchronisation miroir
    Alors une exception explicite PersonasSyncError est levée
    Et les agents valides continuent d'être synchronisés sans corruption des cibles

  Scénario: Pilier 3 - Résilience (Mode dégradé) : Confinement strict de compétence interdite
    Étant donné l'agent explorer configuré avec interdiction de "forbidden-skill-canary"
    Quand le manifeste miroir .opencode/agents/explorer.md est généré
    Alors la compétence interdite est totalement absente de la liste des outils
    Et une trace d'audit de confinement est émise dans les logs

  Scénario: Pilier 4 - UX (Accessibilité & État vide) : Répertoire cible inexistant créé proprement
    Étant donné un projet vierge sans répertoire .opencode/agents/
    Quand j'exécute la synchronisation miroir
    Alors le dossier .opencode/agents/ est créé automatiquement avec permissions standard
    Et un rapport de parité lisible indique 100% de concordance
```
