# ADR-0389 : Grill-Me v2 — Frontier Rounds, Handoff Ungrillable & Immunité Context Budget

* **Statut** : ACCEPTÉ
* **Date** : 24 septembre 2026
* **Décideurs** : Équipe Architecture mLoop, Agent Orchestrateur, Product Owner
* **Dépendances / Références** : [ADR-0320](0320-grill-me-frontier-design-tree-alignment.md), [ADR-0375](README.md), [ADR-0384](0384-project-directives-ssot-boot-enforcement.md), [ADR-0385](0385-protocole-falsification-frontieres-architecture-immunite-cognitive.md)

---

## 🚀 1. Contexte & Problématique

L'expérience accumulée sur le moteur de Grilling mLoop ([ADR-0320](0320-grill-me-frontier-design-tree-alignment.md)) et l'analyse de l'état de l'art (Matt Pocock / AI Hero, 2026) mettent en évidence trois goulots d'étranglement majeurs dans les workflows d'alignement interactif :

1. **Lenteur et fatigue décisionnelle du 1:1 systématique en cadrage global** :
   Imposer une question unique par tour lorsque plusieurs choix d'infrastructure ou de socle commun sont mutuellement orthogonaux génère une latence superflue et multiplie les allers-retours humains.
2. **Le piège des questions "Ungrillables" (High-Fidelity / UX)** :
   Vouloir résoudre par la dialectique textuelle pure des questions relevant de la disposition spatiale, de l'ergonomie visuelle ou de micro-interactions conduit à des discussions abstraites et des compromis fragiles.
3. **Le risque de saturation du Context Window ("Dumb Zone" > 120k tokens) et la perte de mémoire post-grill** :
   Les sessions volumineuses dégradent l'attention du modèle si le scope n'est pas borné. Inversement, réinitialiser la conversation après le grill pour commencer la rédaction détruit la valeur inestimable des arbitrages consignés dans la fenêtre d'attention.

---

## 💡 2. Décisions d'Architecture

### A. Hybridation du Format des Questions : Frontier Rounds vs 1:1 Atomique

Le format d'interrogation s'adapte au niveau de couplage des décisions :

1. **Macro-Grill (`grill-project`) — Mode "Frontier Round" par défaut** :
   - Lorsque plusieurs questions de la frontière active sont **mutuellement indépendantes (orthogonales)** et ont leurs prérequis vérifiés, l'agent les regroupe dans un **Round de Frontière (2 à 4 questions maximum)**.
   - Chaque question du round conserve son contexte factuel, son **`💡 GUESS`** et sa **`➡️ Recommandation motivée`**.
   - L'utilisateur peut tout valider en bloc (« Validé ») ou amender de manière sélective (« Q1: option B, Q2: ok, Q3: ok »).
2. **Micro-Grill (`grill-me --story`) — Maintien du 1:1 Atomique Strict** :
   - Sur un récit spécifique, les règles métier sont fortement imbriquées. L'agent pose **exactement 1 question atomique par tour** pour garantir une concentration sans dispersion.
3. **Contrôle Humain (PO Override)** :
   - L'utilisateur peut basculer le mode à tout moment en spécifiant `mode: round` ou `mode: 1:1`.

---

### B. Protocole Handoff pour Questions "Ungrillables" (`grill → prototype → grill again`)

1. **Détection Formelle** :
   - Une question est classée *ungrillable* si elle porte sur l'agencement spatial (layout, drawer vs modal, wizard vs monopage), la densité d'information visuelle, ou le ressenti ergonomique.
2. **Suspension & Handoff Jetable** :
   - L'agent suspend le grilling :  
     *« ⏸️ Question haute-fidélité IHM détectée. Suspension temporaire de l'interview pour prototypage visuel. »*
   - L'agent génère immédiatement un artefact jetable (composant HTML/Tailwind interactif ou mockup SVG sous `docs/05-assets/mockups/`).
3. **Validation Réactive & Clôture** :
   - L'humain teste ou inspecte l'artefact en quelques secondes et tranche sans ambiguïté.
   - L'agent consigne le choix dans `CONTEXT.md` et le récit, puis reprend la frontière du grill (*« ▶️ Décision actée. Reprise du Grilling. »*).

---

### C. Immunité Context Budget & Prévention de la "Dumb Zone"

1. **Partitionnement Préventif du Scope (Amont)** :
   - Si une initiative comporte plus de **7 récits** ou un volume documentaire amont supérieur à **40k tokens**, l'agent impose un découpage en *Slices Fonctionnelles* avant d'entamer le Macro-Grill.
2. **Seuils d'Alerte de Session** :
   - **Smart Zone (< 80k tokens)** : Déroulement nominal.
   - **Warning Zone (80k - 120k tokens)** : Point de contrôle obligatoire (`checkpoint_in_flight`), accélération vers la clôture de frontière.
   - **Dumb Zone (> 120k tokens)** : Interdiction d'ajouter de nouvelles branches de questions ; clôture forcée ou découpage en session fille.
3. **Externalisation Continue sur Disque** :
   - Les termes stabilisés sont inscrits immédiatement dans `CONTEXT.md`.
   - Les choix structurants génèrent des ADRs physiques (`docs/01-architecture/ADR-XXX.md`) selon la règle des 3 filtres.
4. **Interdiction Absolue de Purge Post-Grill (No Zero-Context Reset)** :
   - Il est formellement interdit de réinitialiser la conversation après le grill pour rédiger le récit.
   - L'agent enchaîne **directement dans la même session** sur la rédaction de la story avec DoR 6/6 ([`story_template.md`](../blueprints/story_template.md)) et calcul du hash anti-tampering.
   - Seule la phase de dev/test ultérieure est déléguée à un sous-agent avec contexte propre.

---

## 📈 3. Conséquences & Bénéfices

* **Réduction de 50% du temps de cadrage Macro** grâce aux Frontier Rounds sur les décisions indépendantes.
* **Éradication des débats abstraits sur l'UX** grâce au protocole Handoff et aux prototypes jetables.
* **Suppression des pertes de mémoire de session** grâce au chaînage direct sans réinitialisation de contexte.
* **Maintien constant dans la "Smart Zone"** garantissant la pertinence cognitive de l'agent.
