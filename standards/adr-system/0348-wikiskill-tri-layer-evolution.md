# ADR-0348 : Architecture Tri-Couches WikiSkill, Mémoire Négative & Gating de Non-Régression

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-02
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Framework Backend mLoop, Pipeline d'Auto-Tuning (`src/pipelines/skill_auto_tuner.py`), Registre RHO (`src/pipelines/rho_optimizer.py`), Registre d'Impact (`src/core/skill_impact_tracker.py`), Manifestes `.agents/skills/`

---

## 1. Contexte & Problématique

Dans les systèmes multi-agents auto-évolutifs (TextGrad, DSPy, EvoAgent, Reflexion), l'optimisation continue des instructions et des compétences (*Skills*) se heurte historiquement à deux écueils majeurs identifiés par la recherche (*Tang et al., Google Research & Virginia Tech, août 2026 — arXiv:2608.27454*) :
1. **L'Amnésie d'Optimisation (*Optimization Amnesia*) & l'Oscillation** : Les moteurs de proposition de prompts explorent des mutations sans conserver la mémoire explicite des hypothèses ayant déjà échoué. Au fil des cycles, le système re-propose cycliquement des formulations déjà invalidées.
2. **La Pollution Contextuelle (*Noise Leakage & Context Rot*)** : Injecter les journaux d'exécution bruts (DOM, traces HTTP, logs d'erreurs) dans la fenêtre d'inférence de l'agent dégrade la qualité des spécifications fonctionnelles et induit un comportement de "raccourci" au détriment de l'application de règles génériques pures.

Cette ADR formalise l'intégration au sein de **mLoop** des principes fondamentaux du framework **WikiSkill** adaptés à l'orchestration logicielle d'entreprise.

---

## 2. Décisions d'Architecture

```
                               ┌────────────────────────────────────────────────────────┐
                               │           ARCHITECTURE TRI-COUCHES WIKISKILL           │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                     ┌─────────────────────────────────────┼─────────────────────────────────────┐
                     │                                     │                                     │
                     ▼                                     ▼                                     ▼
     ┌───────────────────────────────┐     ┌───────────────────────────────┐     ┌───────────────────────────────┐
     │   1. COUCHE BRUTE (RAW)       │     │  2. WIKI PERSISTANT (SAVOIR)  │     │ 3. COMPÉTENCES (EXECUTABLE)   │
     │ • memory/traces/*.jsonl       │     │ • docs/00-ingested/ (SSOT)    │     │ • .agents/skills/*/SKILL.md   │
     │ • Logs Workers Herdr          │     │ • docs/06-knowledge/          │     │ • standards/rho_rules.yaml    │
     │ • Observations brutes DOM     │     │ • memory/skill_impact.jsonl   │     │ • Manifestes compacts no-code │
     │ • Immuable (Read-Only)        │     │ • ZÉRO ROLLBACK (Anti-Patterns│     │ • Gating de Non-Régression    │
     └───────────────────────────────┘     └───────────────────────────────┘     └───────────────────────────────┘
                                                           │
                                                           ▼
                                           ┌───────────────────────────────┐
                                           │  GATING MULTI-NIVEAUX         │
                                           │ • Δscore > 0 -> ACCEPTED      │
                                           │ • Δscore <= 0 -> ROLLBACK     │
                                           │ • Inscription échec au journal│
                                           └───────────────────────────────┘
```

### 2.1 Les 5 Piliers Constitutionnels WikiSkill dans mLoop

#### 1. Séparation Stricte en 3 Couches
- **Couche 1 (Raw Traces)** : Journaux d'exécution bruts, traces HTTP, AST, captures d'écrans et sorties CLI conservés sous `memory/traces/`.
- **Couche 2 (Wiki Persistant)** : Base de connaissances distillée (`docs/00-ingested/`, `docs/06-knowledge/`, Graphify, SQLite FTS5) et registre des hypothèses négatives (`memory/skill_impact.jsonl`, `memory/rho_impact.yaml`). **Cette couche ne subit jamais de rollback.**
- **Couche 3 (Compétences Exécutables)** : Fichiers `SKILL.md` ultra-concis et règles RHO actives.

#### 2. Registre des Contraintes Négatives (`SkillImpactTracker`)
- Tout essai de mutation de compétence est consigné dans `memory/skill_impact.jsonl` avec son diff, le $\Delta \text{score}$, le verdict (`ACCEPTED` ou `REJECTED`) et le motif explicite de rejet.
- Avant toute nouvelle passe d'auto-tuning (`SkillAutoTuner`), le système extrait les contraintes négatives passées et les injecte dans le prompt du proposer pour interdire formellement les voies d'exploration déjà invalidées.

#### 3. Règle d'Or d'Isolation (« No-Wiki at Inference »)
- Lors de la phase de rédaction fonctionnelle, de décomposition INVEST ou de dev handoff, l'agent en cours d'inférence ne reçoit **jamais** les traces brutes de diagnostic. Il ne consulte que son manifeste `SKILL.md` et le contexte ciblé à 1 saut (MCP / EvidencePack).

#### 4. Gating de Non-Régression & Rollback Automatique
- Toute mutation d'un `SKILL.md` est soumise à une double validation :
  1. *Linter physique* : intégrité du Frontmatter YAML et syntaxe Markdown.
  2. *Score Delta ($\Delta \text{score}$)* : si la mutation induit une régression ($\Delta \text{score} \le 0$), le fichier `SKILL.md` est **immédiatement restauré dans son état initial (Rollback)** et l'échec est gravé dans `skill_impact.jsonl`.

#### 5. Hygiène Continue & Tombstoning Anti-Rot
- Le mécanisme `dream_collector` audite périodiquement les règles actives face aux nouvelles ADRs et marque les règles obsolètes ou contredites avec le statut `TOMBSTONE` afin de prévenir la putréfaction mémorielle (*Context Rot*).

---

## 3. Conséquences & Bénéfices

- **Élimination des régressions cycliques** : Les agents d'optimisation mLoop ne tournent plus en boucle sur des formulations défaillantes.
- **Pureté No-Code préservée** : L'étanchéité d'inférence empêche les fuites de sélecteurs ou de snippets techniques dans les User Stories.
- **Transfert Asymétrique** : Possibilité de déléguer la découverte de patterns à des modèles légers (Système 1 / Herdr workers) et l'exécution aux modèles de pointe (Système 2).
