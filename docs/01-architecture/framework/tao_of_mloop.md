# ☯️ Le Tao de mLoop : Manifeste de la Contrainte Utile (Harness Engineering)

> *« Le Tao ne fait rien, et pourtant rien ne reste infait. »* — Lao Tseu (Verset 37)

L'écosystème **Memory Loop (mLoop v2.0)** est conçu selon une philosophie de la contrainte sémantique qui puise ses fondements conceptuels dans la sagesse du **Tao Te Ching**. Ce manifeste établit le parallèle rigoureux entre la pensée taoïste et l'ingénierie de harnais (*Harness Engineering*) qui régit nos agents de Système 2 (Antigravity).

---

## 🌾 1. Le Wu Wei (La Non-Action) et la Suprématie du Harnais (Harness Supremacy)

*   **Le Concept Taoïste (Verset 11)** : *« On façonne l'argile pour en faire un vase, mais c'est le vide à l'intérieur qui retient l'eau. On bâtit une pièce en y perçant des portes et des fenêtres, mais c'est le vide qui la rend habitable. »*
*   **La Transposition mLoop** : Le "Wu Wei" n'est pas de l'inaction passive, mais une action pure et sans force qui s'appuie sur le vide structuré et la contrainte externe.
    *   **Harness Supremacy** : Le harnais externe déterministe (Système 1 en Python/SQLite : règles, linters, protocoles, boucliers) prime et contraint impérativement le modèle probabiliste (Système 2 - LLM). L'intelligence et la fiabilité s'accumulent dans le harnais déterministe.
    *   **La Non-Action Technique (Wu Wei Linter)** : Antigravity (Cerveau) a l'obligation de refuser la prolifération de fichiers, d'abstractions complexes et de dépendances superflues. Moins il y a de code, plus le système est robuste. Le meilleur code est celui qui n'a pas besoin d'être écrit.

---

## 🪵 2. Le Pu (Le Bloc non sculpté), Pureté Fonctionnelle & Universal Dev Handoff

*   **Le Concept Taoïste (Verset 27 & 38)** : *« Le Maître reste fidèle au fruit et non à la fleur, au solide et non au superficiel. Le sage se consacre à la simplicité originelle du bloc non sculpté. »*
*   **La Transposition mLoop** : Le bloc non sculpté représente la spécification fonctionnelle pure, débarrassée du jargon et des bruits de l'implémentation technique.
    *   **Herméticité Absolue & Universal Dev Handoff** : mLoop ne modifie jamais le code physique de l'application cliente. Il agit comme le fournisseur universel de spécifications prêtes pour les agents et développeurs avals (Cursor, Copilot, OpenCode, Claude Code), sans ambiguïté via des contrats déclaratifs REST/CTA et règles métier atomiques (`RM-XXX`).
    *   **Règle des 2 Seuls Gabarits (ADR-0375)** : Éradication de tout gabarit intermédiaire :
        - *Palier 1 (Macro-Cadrage)* : `story_draft_template.md` (Statut `DRAFT`, `grill_me: PENDING`) pour découper vite sans friction.
        - *Palier 2 (Haute Fidélité)* : `story_template.md` (Statut `READY_FOR_DEV`, DoR 6/6, 4 Piliers Gherkin : Nominal, Exceptions, Résilience, UX).
    *   **Simplicité Originelle & EvidencePacks** : L'agent génère des contrats simples accompagnés d'un artefact d'évidence déterministe (`memory/evidence/`), scellé de façon 100% autonome et synchrone (*Zero-Ask Evidence Enforcement*).

---

## 💧 3. L'Eau, le Flux de la Mémoire & le Diptyque Épistémique

*   **Le Concept Taoïste (Verset 8)** : *« Le bien suprême est comme l'eau. L'eau bénéficie à toutes choses sans rivaliser avec elles. Elle réside dans les lieux bas que les hommes évitent. En cela, elle est proche du Tao. »*
*   **La Transposition mLoop** : L'information sémantique dans mLoop s'écoule librement et s'adapte au contenant sans jamais s'égarer dans l'hallucination.
    *   **Diptyque Épistémique (Grill-with-Docs & Fact-Search)** : Interdiction d'extrapoler. L'agent confronte toute exigence aux sources physiques via le *Passage-Level Grounding* (citations verbatim numérotées au passage près), consigné sous `memory/evidence/<STORY_ID>_fact_dossier.md` (ADR-0320 / ADR-0361).
    *   **Fluidité Contextuelle (RAG L3 & SQLite FTS5)** : Grâce aux serveurs MCP et à SQLite FTS5, l'information n'est pas stockée de manière statique et lourde dans le prompt du modèle, mais s'écoule depuis le graphe sémantique vers la mémoire RAM uniquement quand elle est requise (`graphify query`, `fact-search`).
    *   **Retour au Vide (Handoff & PITR)** : Pour éliminer le *Context Rot*, l'agent se vide de sa mémoire de session à chaque cycle via le skill `handoff` et les sauvegardes instantanées In-Flight (ADR-0371), retournant à la fraîcheur originelle tout en préservant une traçabilité immuable.

---

## 🌬️ 4. Le Soufflet (Bellows) et l'Auto-Amélioration Récursive

*   **Le Concept Taoïste (Verset 5 & 48)** : *« L'espace entre le Ciel et la Terre est comme un soufflet. Il est vide et pourtant inépuisable. Plus on l'actionne, plus il produit. [...] Pour acquérir le savoir, ajoutez chaque jour quelque chose. Pour acquérir le Tao, éliminez chaque jour quelque chose. »*
*   **La Transposition mLoop** : L'espace cognitif reste léger tandis que les fondations déterministes s'auto-améliorent en tâche de fond.
    *   **StandardsGraph & Bouclier de Confinement (ADR-0379)** : Graphe SQLite des standards et interdiction stricte de compétences en mémoire vive évalués en `< 0.2 ms`.
    *   **Replay Simulator Dream RSI (ADR-0372)** : Auto-amélioration récursive du harnais par rejeu hors-ligne sur traces d'exécution historiques pour prévenir toute régression.
    *   **RHO & Calibrate Déterministe** : Réduction continue du bruit et des faux positifs en cristallisant les apprentissages sous forme de contraintes YAML et de contrôles 19/19 PASS (`vibe-check`).

---

## 👑 5. L'Orchestration Invisible : "It happened by itself"

*   **Le Concept Taoïste (Verset 17)** : *« Du meilleur dirigeant, les gens savent seulement qu'il existe. [...] Quand son travail est fait, son but atteint, les gens disent : "Cela s'est fait tout seul". »*
*   **La Transposition mLoop** : L'orchestration du Cycle en 5 Phases universelles (ADR-0375) est fluide, asynchrone et naturelle.
    *   **Le Cycle en 5 Phases & Portes de Gouvernance (ADR-0375)** :
        - `Phase 1 : INGEST & EXPLORE` (Gate 1 : Cadrage & Ingestion Prêts — Zéro story fantôme)
        - `Phase 2 : PLAN & ANALYSE` (Gate 2 : DoR 6/6, 4 Piliers Gherkin & Grill-Me 1:1)
        - `Phase 3 : BUILD & DEV` (Gate 3 : DoD 100% Tests — Code mLoop interne ou Handoff externe)
        - `Phase 4 : VALIDATE & QA` (Gate 4 : Recette Métier & Audit Contradictoire Sentinel)
        - `Phase 5 : SHIP & SYNC` (Gate 5 : Clôture & Synchronisation Jira/Git/Graphe)
    *   **Gouvernance Sémantique & Vibe-Check Pré-Vol** : Le Kernel local (`src/swarm.py`) gère les transitions de manière déterministe. La séquence d'amorçage (`resume` ➔ `vibe-check` 19/19 ➔ `focus`) sécurise chaque tour de parole sans friction cognitive.
