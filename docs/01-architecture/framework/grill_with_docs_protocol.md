# 🥩 Le Protocole "Grill with Docs" (Grill Me v2)

Le **Grill with Docs** (ou *Grill Me*) est le processus central de la **Phase 2 : PLAN / ARCHI** du cycle Spec-Driven en 5 Phases (Spec -> Plan -> Build -> Validate -> Ship). C'est une entrevue interactive ciblée entre l'Humain et l'agent `plan` (Stratégie & Architecture).
Gouvernance : [ADR-0320](../../../standards/adr-system/0320-grill-me-frontier-design-tree-alignment.md), [ADR-0389](../../../standards/adr-system/0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md) et [ADR-013](../../01-architecture/ADR-013_epic-29_grill_v2_frontier_rounds_ungrillable_context.md).

---

## 1. Objectif & Matrice Orthogonale Format × Scope (ADR-0393)

L'objectif est d'éliminer toute ambiguïté fonctionnelle ou technique **avant** de découper et chiffrer les récits utilisateurs du backlog. Plutôt que de coder à la volée, le Grilling aligne systématiquement la compréhension des Faits et des Décisions.

### 1.1 Matrice 2×2 Déterministe (ADR-013 / ADR-0393)

Le système sépare irrévocablement la **forme de l'interaction** (Format) de son **périmètre d'application** (Scope) :

| | `STORY` (récit unitaire) | `EPIC / PROJECT` (transverse) |
|---|---|---|
| **`ATOMIC`** (`--format atomic`) | Micro-Grill 1:1 (`grill-me --story`) | Cadrage séquentiel (`grill-project --format atomic`) |
| **`ROUND`** (`--format round`) | Frontier Rounds unitaires | Macro-Grill transverse (`grill-project`) |

> **🚨 RÈGLE D'OR** : Choisir `ROUND` ne modifie en rien le périmètre d'analyse et ne constitue EN AUCUN CAS un ordre de rédaction de code ou de story.

1. **Format Round (`--format round`, par défaut pour `grill-project`)** :
   - Traitement par lots de **2 à 4 questions orthogonales indépendantes**.
   - Chaque question contient son *Contexte*, une hypothèse (*Guess*) et la *Recommandation mLoop*.
   - L'utilisateur peut valider en bloc ou amender sélectivement.
2. **Format Atomic (`--format atomic`, par défaut pour `grill-me --story`)** :
   - Règle stricte du **1:1** pour les dépendances fines sur un récit spécifique.

### 1.2 Arrêt Formel Post-Round & Mandat Unitaire (ADR-0393)

Dès que la frontière de décision est vide :
1. **Cessation immédiate** : L'agent cesse tout appel d'outil d'écriture.
2. **Menu d'orientation fermé obligatoire** : 3 choix (DRAFT Palier 1, Micro-Grill 1:1, Clôture).
3. **Mandat unitaire strict** : Aucun mandat d'écriture par défaut. Seul le choix explicite d'un récit par l'humain autorise la rédaction de ce seul récit.
4. **Plafond de promotion** : L'agent ne peut promouvoir qu'au statut `READY_FOR_GROOMING`. `READY_FOR_DEV` = Gate 2 humaine exclusive.

```mermaid
flowchart TD
    Start["Lancement Cadrage Phase 2"] --> ChoiceScope{"Scope"}
    ChoiceScope -->|EPIC/PROJECT| ChoiceFmt1{"Format"}
    ChoiceScope -->|STORY| ChoiceFmt2{"Format"}

    ChoiceFmt1 -->|ROUND| Round["Frontier Round (2-4 Qs)"]
    ChoiceFmt1 -->|ATOMIC| AtomicMacro["1:1 Séquentiel Transverse"]
    ChoiceFmt2 -->|ROUND| RoundStory["Frontier Rounds Unitaires"]
    ChoiceFmt2 -->|ATOMIC| Atomic["1:1 Atomic Grill-Me"]

    Round --> EvalQ{"Ungrillable ?"}
    AtomicMacro --> EvalQ
    RoundStory --> EvalQ
    Atomic --> EvalQ

    EvalQ -->|Non| TextDec["Arbitrage Textuel & ADR"]
    EvalQ -->|Oui| Handoff["Handoff Pattern (<30s)"]

    Handoff --> Proto["Visualisation locale"]
    Proto --> TextDec

    TextDec --> FrontierCheck{"Frontiere vide ?"}
    FrontierCheck -->|Non| Budget{"Budget Contexte"}
    FrontierCheck -->|Oui| Stop["ARRET FORMEL + Menu Orientation"]

    Budget -->|< 120k| Round
    Budget -->|> 120k Dumb Zone| Stop
```

---

## 2. Le Handoff Pattern pour les Questions "Ungrillables"

Certaines questions ne peuvent être tranchées efficacement par le texte pur (agencement d'écran, modal vs monopage, stepper vs accordéon, densité d'un tableau).
Tenter de débattre textuellement d'un composant visuel mène à une dialectique stérile.

### Règle d'or : *Grill -> Prototype -> Grill Again*
1. **Détection du Signal** : Si la question touche à la disposition spatiale, à la densité ou aux micro-interactions, l'agent suspend temporairement le débat textuel.
2. **Génération Zéro-Build (< 30 secondes)** : L'agent génère un prototype autonome HTML5 (avec CDN Tailwind) ou SVG sous `Projects/<projet>/scratch/prototypes/proto_<ID>_<sujet>.<html|svg>`.
3. **Prévisualisation Locale** : L'URL locale directe `file:///...` est affichée en console.
4. **Promotion Conditionnelle** : Si le PO valide le prototype, il est promu sous `docs/05-assets/mockups/` et lié au récit, sinon consigné au scratch.

---

## 3. Surveillance du Budget de Contexte & Anti-Amnésie

La fenêtre de contexte d'un grand modèle de langage n'est pas infinie. Au-delà d'un certain volume, l'attention se dégrade (zone de fatigue cognitive, dite « Dumb Zone »).

### Seuils Déterministes (ADR-0389 §C)
- **`< 80 000 tokens` (Smart Zone)** : Attention nominale. Cadrage actif et expansion d'arbre autorisés.
- **`80 000 - 120 000 tokens` (Warning Zone)** : Avertissement proactif. Le système exige la pose d'un checkpoint (`checkpoint_in_flight.json`) avant de continuer.
- **`> 120 000 tokens` (Dumb Zone)** : Alerte critique. Le moteur gèle l'ouverture de nouvelles branches exploratoires et impose de passer immédiatement à la rédaction finale des récits.

### Interdiction Absolue de Purge Post-Grill
> **RÈGLE CRITIQUE** : L'agent **ne doit JAMAIS purger la conversation** ou réinitialiser le fil de discussion après un Grill-Me. Tout le contexte chaud accumulé lors des questions-réponses sert directement à la rédaction des critères d'acceptation DoR 6/6. Effacer la session détruit la mémoire des arbitrages et recrée des hallucinations.

---

## 4. Portes de Sortie (Gates G1 à G7)

Le passage de la Phase 2 (PLAN / ARCHI) à la Phase 3 (BUILD) est conditionné par la validation intégrale des 7 portes du blueprint canonique `standards/blueprints/gates_grill_me.template.md` :

- **G1 (Questions Ouvertes)** : Tout résidu sans arbitrage est consigné `OQ-XXX`.
- **G2 (ADR)** : Les choix structurants sont consignés en ADR Markdown opposable.
- **G3 (Preuves Fact-Search)** : Les faits sont vérifiés par recherche FTS5 documentée.
- **G4 (Fact Dossiers C9)** : Dossiers de preuves formalisés sous `memory/evidence/`.
- **G5 (Sentinel / Rubber-Duck)** : Récits validés 4 Piliers Gherkin sans objection bloquante.
- **G6 (Handoff Ungrillables)** : Tout choix IHM/UX est ancré par un prototype visuel.
- **G7 (Context Health)** : Budget de contexte maîtrisé sans rupture amnésique.
