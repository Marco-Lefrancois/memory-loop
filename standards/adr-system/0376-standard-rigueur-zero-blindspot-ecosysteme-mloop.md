# ADR-0376 : Standard de Rigueur d'Ingénierie & Audit 360° Zéro Blindspot pour les Évolutions de l'Écosystème mLoop

* **Statut** : ACCEPTÉ
* **Date** : 18 septembre 2026
* **Décideurs** : Architecte en Chef, Équipe Core mLoop, Product Owner
* **Domaine** : Rigueur d'ingénierie, gouvernance du code source du framework, protocole d'auto-évolution

---

## 🚀 1. Contexte & Problématique

Memory Loop est un framework de gouvernance et d'orchestration agentique multi-LLMs. Lorsque des modifications sont apportées au framework lui-même (commandes CLI, templates de stories, machine à états, protocoles de validation), les interventions ponctuelles non coordonnées génèrent de l'entropie :
- Des artefacts ou gabarits obsolètes restent présents dans `standards/blueprints/` et créent de la confusion.
- Des directives dans les personas ou skills des sous-agents contredisent le nouveau code Python.
- Des tests unitaires ne sont pas mis à jour ou conservent des hypothèses caduques.
- Des incohérences entre la documentation normative (`standards/protocols/`) et le comportement réel du système s'installent.

Pour garantir que le framework mLoop reste un modèle d'excellence d'ingénierie logicielle, toute évolution interne doit répondre à un standard de rigueur intransigeant.

---

## 💡 2. Décisions d'Architecture

### A. Institutionnalisation de la Directive Inviolable d'Audit en 7 Couches
Toute proposition d'évolution touchant le cœur de mLoop interdit formellement l'écriture de code ou de directives sans avoir préalablement mené l'**Audit 360° en 7 Couches** formalisé dans [`standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md`](../protocols/ECOSYSTEM_RIGOR_PROTOCOL.md) :
1. **Blueprints & Gabarits** (`standards/blueprints/`)
2. **Protocoles & Frameworks Métier** (`standards/protocols/`)
3. **Système Décisionnel & ADRs** (`standards/adr-system/`)
4. **Directives, Personas & TOML Agents** (`.agents/agents/`, `standards/agents/`)
5. **Skills & Compétences Portables** (`.agents/skills/`)
6. **Moteur Core Python & CLI** (`src/core/`, `src/pipelines/`, `src/commands/`)
7. **Suite de Tests & Parité Documentation** (`tests/`, `standards/protocols/CLI_PIPELINE_GUIDE.md`)

### B. Obligation du Plan d'Implémentation Zéro Blindspot
Avant toute modification de fichier, l'agent ou l'ingénieur doit soumettre un **plan d'implémentation interactif exhaustif** détaillant :
- Chaque fichier impacté avec sa mention explicite : `[NEW]`, `[MODIFY]`, `[DELETE]`.
- La justification de chaque action et son articulation avec les 7 couches.
- Le plan de vérification déterministe (commandes pytest précises).
- **Feu vert humain bloquant** : Aucune écriture n'est autorisée avant approbation explicite.

### C. Triangulation Normative Active (Directive + Règle IDE + Protocole)
Cette rigueur est rendue inviolable par sa triple présence dans les points d'entrée des LLMs :
1. Inscrite dans [`AGENTS.md`](../../AGENTS.md) comme consigne suprême pour tous les modèles.
2. Déployée dans [`.agents/rules/ecosystem_rigor_zero_blindspot.md`](../../.agents/rules/ecosystem_rigor_zero_blindspot.md) pour les agents IDE (Antigravity, Cursor, OpenCode).
3. Documentée dans le protocole normatif [`standards/protocols/ECOSYSTEM_RIGOR_PROTOCOL.md`](../protocols/ECOSYSTEM_RIGOR_PROTOCOL.md).

---

## ⚖️ 3. Conséquences

### Positives
* **Zéro angle mort technique** : Fin des résidus orphelins, des gabarits fantômes et des règles contradictoires.
* **Confiance absolue dans les évolutions du framework** : Chaque modification est traçable de bout en bout, de l'ADR aux tests unitaires.
* **Auto-alignement déterministe des agents** : Tous les LLMs opérant sur mLoop sont contraints d'adopter la même discipline d'ingénierie senior.

### Négatives & Mitigations
* **Effort de cadrage accru avant implémentation** : Tempéré par le fait que le temps investi dans l'audit à froid élimine 90% des allers-retours de débogage et de correction de régressions en aval.
