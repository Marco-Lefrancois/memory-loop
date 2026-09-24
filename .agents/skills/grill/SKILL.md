---
name: grill
description: Interrogatoire interactif sans concession (Dualité Macro Projet vs Micro Récit 1:1), alignement PO avec hypothèses et questions atomiques, arbitrage Faits vs Décisions, et constitution du Dossier de Preuves Documentaires. Use when clarifying requirements, interviewing a stakeholder before writing stories, or exploring architecture design trade-offs.
---

# 🛠️ Skill : Session Interactive Grill & Dualité du Cadrage (`/grill`)

## Aperçu & Rôle Souverain
Ce skill régit la discipline d'interrogatoire sans concession (*Relentless Interview*), d'exploration de l'arbre de conception (**Frontier Design Tree**), et de cadrage contradictoire entre l'agent mLoop et l'utilisateur pour aligner la vision fonctionnelle et technique **AVANT** toute phase de build ([ADR-0320](../../standards/adr-system/README.md), [ADR-0375](../../standards/adr-system/README.md)). Il s'appuie sur la **Matrice des 4 États**, les **5 Vecteurs de Résilience**, et permet l'export en questionnaire (`to-questionnaire`).

---

## 🧭 La Dualité du Grill-Me (Macro vs Micro)

Le Grilling opère obligatoirement à deux échelles distinctes pour éviter le syndrome du perroquet :

### 1. Grill-Me Macro : Cadrage Global du Projet (`python src/swarm.py grill-project`)
- **Moment** : En début de Phase 2 (PLAN & ANALYSE), immédiatement après l'ingestion de la matière brute.
- **Périmètre** : Le système dans son ensemble.
- **Questions clés** : Choix d'architecture structurants (Cloud, SSO, hébergement), conformité Loi 25, frontières d'exclusions globales (Out-of-Scope), hypothèses du T-Shirt Size.
- **Livrables produits** : ADR transverses de cadrage, sections d'hypothèses de `TSHIRT_SIZE.md` / `SOW.md`, glossaire unifié `CONTEXT.md`.
- **Règle d'or** : Élimine 80% des questions répétitives en fixant le socle commun pour l'ensemble des récits du backlog.

### 2. Grill-Me Micro : Analyse Fine Récit par Récit (`python src/swarm.py grill-me --story <ID>`)
- **Moment** : Au cours du sprint, lors de la prise en charge d'un récit (`IN_ANALYZE`).
- **Périmètre** : Strictement l'écran, le contrat d'API et les règles d'affaires spécifiques de CE récit.
- **Ordre du jour** : Résolution des questions ouvertes listées en **Section 5 de `story_draft_template.md`**.
- **Livrable produit** : Récit converti au gabarit haute fidélité [`story_template.md`](../../standards/blueprints/story_template.md) avec DoR 6/6 (`READY_FOR_DEV`).

---

## Déroulé Opérationnel en 4 Étapes

### Étape 0 : « Search-Before-Ask », Localisation SSOT, CONTEXT.md & Fact-Search FTS5
0. **Localiser la Source de Vérité Canonique AVANT toute recherche (ADR-0384)** : lire d'abord `Projects/<projet>/directives/tech.md` et `directives/business.md` s'ils existent, identifier la source de vérité canonique déclarée (hiérarchie à 3 niveaux : Canonique `docs/03-models/` > Amont `docs/00-ingested/` > Staging `reference/`), puis la charte projet `AGENTS.md`, puis `docs/01-architecture/`. **Ordre de recherche imposé : directives en tête.**
   - **Interdiction de brief non sourcé** : ne jamais transmettre à un sous-agent (`task`, `worker-spawn`) un brief référençant un chemin de modèle de données non confirmé comme canonique.
   - Citer la hiérarchie SSOT retenue dans le Dossier de Preuves.
1. Interroger l'index SQLite FTS5 (`.fact_search_index.db`) et `CONTEXT.md` pour identifier les maquettes SVG validées (`docs/05-assets/`), règles métier (`RM-XXX`), schémas DBML et vocabulaire ubique.
2. Arbitrer **Faits vs Décisions** : si un fait est consigné dans la documentation ou le code existant, **interdiction absolue de poser la question à l'humain**.
3. Rédiger le Dossier de Preuves selon le gabarit normatif [`standards/blueprints/dossier_de_preuves_template.md`](../../standards/blueprints/dossier_de_preuves_template.md).

### Étape 1 : Roast à Froid & Hypothèse Explicite avec Confiance
Avant la première question, l'agent livre un avis sans complaisance (*Anti-Sycophancy*) :
```text
HYPOTHESIS: [Interprétation brute du besoin par l'agent]
CONFIDENCE: [ex: ~40% - Faits manquants : volumétrie, politique de retry, format d'export]
ROAST: [Démontage des faux prérequis, des endpoints supposés et des sur-ingénieries]
```

### Étape 2 : Format des Questions (Frontier Rounds vs 1:1 Atomique - ADR-0389)
L'humain réagit 3x plus vite pour corriger une fausse supposition que pour formuler une réponse abstraite :
- **En Macro (`grill-project`)** : Mode **Frontier Round** par défaut. L'agent regroupe **2 à 4 questions orthogonales (mutuellement indépendantes)** dont les prérequis sont vérifiés. Chaque question comporte son contexte, son `💡 GUESS` et sa `➡️ Recommandation motivée`. L'humain peut valider en bloc (« Validé ») ou amender (« Q1: opt B, Q2: ok »).
- **En Micro (`grill-me --story <ID>`)** : Mode **1:1 Atomique Strict**. Poser exactement 1 question par tour, car chaque règle d'affaires conditionne la suivante.
- **Débrayage Utilisateur** : L'humain peut imposer son mode à tout moment via `mode: round` ou `mode: 1:1`.

```markdown
❓ **Q : <Question sur la frontière active> ?**
💡 **GUESS** : <Supposition de l'agent basée sur le contexte existant>
➡️ **Recommandation mLoop** : <Option A ou B motivée par les standards>
```

### Étape 2bis : Traitement des Questions "Ungrillables" (Handoff Pattern - ADR-0389)
Certaines questions ne peuvent PAS être résolues par le dialogue textuel (disposition d'écrans, densité visuelle, wizard vs drawer, ressenti ergonomique).
- Dès qu'une question est classée **Ungrillable (Haute-Fidélité IHM / UX)**, appliquer le **Handoff Pattern** (`grill → prototype → grill again`) :
  1. **Pause** : Suspendre le grilling textuel (*« ⏸️ Question IHM haute fidélité détectée »*).
  2. **Prototype Jetable** : Générer un composant autonome HTML/Tailwind interactif ou un mockup SVG vectoriel sous `docs/05-assets/mockups/`.
  3. **Tranchage Visuel** : L'humain visualise, clique et choisit en 5 secondes.
  4. **Reprise** : Enregistrer le choix dans `CONTEXT.md` / récit et reprendre immédiatement le grill (*« ▶️ Décision enregistrée. Reprise de la frontière. »*).

### Étape 3 : Traque du « Want vs Should Want »
Poser la question brise-glace de désencombrement :
> *« Si vous n'aviez de comptes à rendre à personne et aucune contrainte d'héritage, que voudriez-vous réellement construire ici ? »*

### Étape 4 : Clôture de Frontière & Épuisement (Frontier Exhaustion) - Budget Contexte & Chaînage (ADR-0389)
La session se termine lorsque l'arbre de décision ne contient plus aucune zone d'ombre (Épuisement de Frontière / Frontier Exhaustion).
- En Macro (`grill-project`) : enregistrement de la décision via ADR et passage au découpage `to-tickets`.
- En Micro (`grill-me --story <ID>`) : dès qu'un récit atteint l'épuisement de frontière, l'agent consigne la décision et avance automatiquement vers le récit suivant ou bascule la story vers `READY_FOR_GROOMING` puis `READY_FOR_DEV` après validation humaine.
- **Surveillance Context Budget ("Dumb Zone")** : Si la session dépasse **80k tokens**, déclencher un point de contrôle (`checkpoint_in_flight`). Si elle dépasse **120k tokens**, interdiction d'ouvrir de nouvelles branches (clôture ou partitionnement en session fille).
- **Externalisation Continue** : Consigner les termes dans `CONTEXT.md` et les décisions filtrées dans `docs/01-architecture/ADR-XXX.md` au fil de l'eau (principe stateful).
- **Interdiction Absolue de Purge Post-Grill** : Ne jamais réinitialiser la conversation après le grill. Enchaîner **directement dans la même session** vers la rédaction du récit au gabarit haute fidélité [`story_template.md`](../../standards/blueprints/story_template.md) avec DoR 6/6 (`READY_FOR_DEV`).
- **Délégation Isolée en Aval** : Seules les étapes d'implémentation (`build` / tests) sont ensuite confiées à un sous-agent avec contexte nettoyé.


---

## Table Anti-Rationalisation (Inviolable)

| Excuse de l'Agent (Paresse) | Réalité & Règle Inviolable |
| :--- | :--- |
| *"Le besoin est évident, je peux rédiger la story directement sans poser de question."* | Même les besoins simples cachent des hypothèses tacites non vérifiées. Le Dossier de Preuves Documentaires est obligatoire pour chaque récit. |
| *"Je vais poser 5 questions dépendantes d'un coup en Micro-Grill."* | En Micro-Grill, le batching sature l'attention. La règle d'or sur un récit est **1 seule question atomique par tour** (sauf en Macro-Grill où les rounds de 2-4 questions orthogonales sont autorisés). |
| *"Je vais débattre pendant 15 tours sur l'ergonomie visuelle du formulaire."* | L'ergonomie ne se discute pas en texte pur. Déclencher immédiatement le **Handoff Pattern** et générer un prototype jetable HTML/SVG. |
| *"La session de grill est finie, je vais faire un reset de contexte pour rédiger au propre."* | **Interdiction formelle de reset**. Le context window contient la mémoire vive de tous les arbitrages. Enchaîner directement sur la rédaction de la story. |
| *"Je vais griller chaque story sans faire de cadrage macro global."* | Conduit au syndrome du perroquet et à l'incohérence systémique. Exécuter `grill-project` avant d'entamer le micro-grilling. |
| *"L'utilisateur m'a dit 'fais au mieux', donc je décide à sa place sans documenter."* | « Au mieux » n'est pas un contrat. Formuler l'hypothèse sous forme de *Guess*, la faire valider en 1 tour, puis consigner la décision dans l'ADR. |

---

## Vérification de Sortie
- [ ] Dossier de Preuves consigné dans `memory/evidence/<STORY_ID>_fact_dossier.md` (ou terminal).
- [ ] 100% des citations au format Grounding (`[fichier.md:Lignes X-Y]`).
- [ ] Questions Ungrillables déroutées vers des prototypes jetables si nécessaire.
- [ ] Frontière de décision validée vide par l'utilisateur.
- [ ] Récit enrichi au gabarit `story_template.md` avec DoR 6/6 dans la continuité du fil de session.

