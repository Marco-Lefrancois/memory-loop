# ADR-0336 : Modèles de Pensée Structurés & Évaluations d'Impact

## Statut
**Accepté (SSOT Normatif)** — 25 août 2026

## Contexte & Problématique
Dans l'écosystème Memory Loop (mLoop), la conception d'architectures, le triage du backlog, l'arbitrage des décisions techniques et la rédaction de récits verticaux exigent une rigueur analytique maximale. Face à des problèmes complexes ou des arbitrages d'ingénierie délicats, les modèles d'IA risquent d'osciller entre deux extrêmes préjudiciables :
1. **L'intuition non cadrée (Unframed Guessing)** : Répondre ou concevoir sans modèle mental formel, augmentant le risque d'angles morts fonctionnels ou de régressions architecturales.
2. **La surcharge cognitive et le gaspillage de tokens (Prompt Bloat & Overthinking)** : Invoquer systématiquement de lourds frameworks de raisonnement sur des tâches simples ou routinières, ce qui dégrade la latence, pollue la fenêtre de contexte et dilue l'attention (*Instruction Budget Exhaustion*).

L'étude approfondie du projet de référence **Claude Code Thinking Skills** (`tjboudreaux/cc-thinking-skills`) démontre qu'une bibliothèque de modèles mentaux structurés n'apporte de la valeur que si elle est adossée à :
- Une **sélection chirurgicale des mécaniques fondamentales** sans prolifération de micro-skills redondants.
- Une **gouvernance d'invocation stricte** basée sur le principe de *Short-Circuit (`NONE` par défaut)* et une quarantaine manuelle (*Manual-Only*).
- Une **évaluation par les résultats réels** (*Outcome-Based Evals*) plutôt qu'un simple linter syntaxique.

---

## Décision d'Architecture

### 1. Sélection & Intégration des 6 Modèles Cognitifs Clés dans mLoop
Afin de préserver la clarté et l'efficacité de l'écosystème, mLoop adopte **6 compétences de pensée spécialisées** dans `.agents/skills/` :

| Modèle Cognitif | Finalité Opérationnelle mLoop | Phase d'Activation |
|---|---|---|
| **`thinking-kepner-tregoe`** | Diagnostic d'anomalies et délimitation formelle par matrice **IS / IS-NOT** (ce qui est affecté vs ce qui est explicitement exclu). | **Spec** (Piliers Gherkin 2 & 3), **Debug** |
| **`thinking-reversibility`** | Classification formelle des décisions en **Type 1** (portes à sens unique / irréversibles ➔ ADR obligatoire) vs **Type 2** (portes à double sens / réversibles ➔ décision agile locale). | **Plan**, **Grill-with-Docs**, **ADR** |
| **`thinking-theory-of-constraints` (ToC)** | Identification du goulet d'étranglement critique (*binding bottleneck*) bloquant le flux de livraison dans le graphe DAG du backlog. | **Triage**, **Plan**, **DAG Orchestration** |
| **`thinking-cynefin`** | Classification du domaine de complexité (*Simple*, *Complicated*, *Complex*, *Chaotic*) pour identifier immédiatement les fonctionnalités nécessitant un Spike préalable (`US-SPIKE-XXX.md`). | **Triage**, **SOW / T-Shirt Sizing** |
| **`thinking-triz`** | Résolution systématique de contradictions d'ingénierie (ex: performance vs exhaustivité sémantique, compacité de prompt vs profondeur de contexte) sans compromis destructeur. | **Architecture**, **R&D Framework** |
| **`thinking-via-negativa`** | Résolution de problèmes par la *soustraction* (élimination de complexité superflue, de code mort ou d'abstractions parasites) avant tout ajout de code. | **Dev Handoff**, **Refactoring** |

---

### 2. Règle d'Invocation "Wu Wei" : Short-Circuit `NONE` & Quarantaine Manuelle

1. **Règle du Short-Circuit (`NONE` par défaut)** :
   - Pour toute tâche routinière, purement syntaxique ou ne comportant pas d'inconnue analytique, l'agent **a l'obligation formelle de raisonner directement sans invoquer de cadre réflexif** (`NONE`).
   - L'utilisation d'un modèle de pensée pour des tâches évidentes est proscrite.
2. **Quarantaine Manuelle & Déclenchement Ciblé (*Manual-Only*)** :
   - Les compétences de pensée ne sont **jamais auto-injectées globalement en tâche de fond**. Elles sont appelées explicitement lorsque les critères d'entrée (*When to Use*) sont réunis.
   - Respect absolu de la **Divulgation Progressive (*Progressive Disclosure*)** pour préserver la fenêtre de contexte.

---

### 3. Ancrage Cryptographique & Épistémique des EvidencePacks

- Les fiches de traçabilité et EvidencePacks (`memory/evidence/<STORY_ID>_evidence.json`) intègrent systématiquement :
  - **L'empreinte SHA-256** des documents sources primaires inspectés (`docs/00-ingested/...` et `reference/`).
  - **Le diptyque épistémique formalisé** :
    - `what_it_actually_proves` : Les faits et comportements formellement démontrés par les sources.
    - `what_it_does_not_prove` : Les angles morts, hypothèses non vérifiées ou limites d'échelle.
    - `claim_boundaries` : Le domaine de validité strict des assertions architecturales.

---

### 4. Évaluation par les Résultats (*Outcome-Based Evals*) : Dépassement du Linter

- La validation mLoop ne se restreint plus à un contrôle mécanique de forme ("Lint is a floor").
- L'évaluation des compétences et des prompts est adossée à la mesure de l'impact réel sur la qualité des spécifications (réduction des questions ouvertes superflues, étanchéité des cas limites Gherkin, isolation des dépendances).

---

## Impacts & Évolutions des Composants Existants

1. **Skill `grill` (`.agents/skills/grill/SKILL.md`)** :
   - Intégration de la distinction formelle Type 1 vs Type 2 lors de l'évaluation des 3 filtres d'ADR.
2. **Skill `sentinel` (`.agents/skills/sentinel/SKILL.md`)** :
   - Renforcement des axes d'attaque 1 et 3 via la grille Kepner-Tregoe IS/IS-NOT et l'analyse pré-mortem systématique.
3. **Skill `triage` (`.agents/skills/triage/SKILL.md`)** :
   - Utilisation de la grille Cynefin pour l'aiguillage automatique vers des Spikes techniques dès lors qu'un récit relève du domaine *Complex*.
4. **Gabarit de Story (`standards/blueprints/story_template.md`)** :
   - Recommandation explicite d'une clause de délimitation IS / IS-NOT pour les fonctionnalités transverses ou à haute criticité.

---

## Conséquences & Bénéfices

- **Élimination de l'Overthinking** : Zéro surcoût de tokens sur les tâches standards grâce à la politique Short-Circuit déterministe.
- **Rigueur d'Arbitrage Maximale** : Les décisions irréversibles (Type 1) sont verrouillées par des ADRs motivés, tandis que les choix réversibles (Type 2) évitent la bureaucratie analytique.
- **Traçabilité Inaltérable** : Les EvidencePacks scellés par SHA-256 garantissent la pérennité et la reproductibilité des preuves architecturales.
