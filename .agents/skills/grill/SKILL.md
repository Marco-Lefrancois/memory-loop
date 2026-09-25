---
name: grill
description: Interrogatoire interactif sans concession (Dualité Macro Projet vs Micro Récit 1:1), alignement PO avec hypothèses et questions atomiques, arbitrage Faits vs Décisions, et constitution du Dossier de Preuves Documentaires. Use when clarifying requirements, interviewing a stakeholder before writing stories, or exploring architecture design trade-offs.
---

# 🛠️ Skill : Session Interactive Grill & Dualité du Cadrage (`/grill`)

## Aperçu & Rôle Souverain
Ce skill régit la discipline d'interrogatoire sans concession (*Relentless Interview*), d'exploration de l'arbre de conception (**Frontier Design Tree**), et de cadrage contradictoire entre l'agent mLoop et l'utilisateur pour aligner la vision fonctionnelle et technique **AVANT** toute phase de build ([ADR-0320](../../standards/adr-system/README.md), [ADR-0375](../../standards/adr-system/README.md)). Il s'appuie sur la **Matrice des 4 États**, les **5 Vecteurs de Résilience**, et permet l'export en questionnaire (`to-questionnaire`).

---

## 🚀 Protocole d'Ouverture de Session (Session Kickoff — Obligatoire)

Avant la première question, l'agent DOIT émettre un **état des lieux en 3 blocs** pour ancrer la session et éviter la boîte noire :

```markdown
## 📋 État des Lieux — Session Grill
### 1. Ce que je sais déjà (Faits établis & Preuves pivots)
- 📌 **<Fait majeur 1>** : <Énoncé factuel établi>
  > 🔍 *Preuve pivot :* `[chemin/fichier.md:Lignes X-Y]` — *« Verbatim court pertinent »*
- 📌 **<Fait majeur 2>** : <Énoncé factuel établi>
  > 🔍 *Preuve pivot :* `[chemin/fichier.md:Lignes X-Y]`
- 📁 *Dossier de preuves exhaustif consigné dans :* `memory/evidence/<STORY_ID>_fact_dossier.md`

### 2. L'unique zone d'ombre à trancher
> ❓ **Q1 — <Titre de la frontière active>**
> <Contexte factuel en 1-2 phrases>
> - **Option A** (Recommandée) : <Description + justification ADR/standard>
> - **Option B** : <Description + compromis>
> ➡️ **Recommandation mLoop** : Option A — <motif en 1 ligne appuyé par la preuve pivot>

### 3. Le plan d'action qui sera appliqué dès votre réponse
- [ ] <Étape 1 concrète>
- [ ] <Étape 2 concrète>
- [ ] <Étape 3 concrète>
```

**Règles d'or du Kickoff :**
- **Principe Preuve Pivot & Sidecar** : Extraire 1 à 3 faits majeurs avec citations cliquables (`[fichier.md:LX-Y]`) et verbatim court. Ne jamais déverser de *Wall of Evidence* dans le chat ; déporter le dossier exhaustif vers `memory/evidence/<STORY_ID>_fact_dossier.md`.
- Le bloc 2 ne contient QU'UNE seule zone d'ombre : la plus bloquante pour le plan d'action.
- Si aucune ambiguïté ne subsiste après le bloc 1, passer directement au bloc 3 (zéro question posée).
- Ce format remplace tout prologue conversationnel vague (« Commençons par... », « Voici ce que je propose... »).

---

## 🧭 Matrice Orthogonale 2×2 : Format × Scope (ADR-0393)

Le Grilling opère sur **deux axes indépendants** — la forme de l'interaction et son périmètre d'application :

### Axe 1 — Format de Dialogue (`--format`)
| Format | Description | Usage |
|--------|-------------|-------|
| `ATOMIC` | 1 question chirurgicale par tour (séquentielle) | Micro-Grill 1:1 sur un récit |
| `ROUND` | Lot structuré de 2-4 questions orthogonales (mutuellement indépendantes) | Cadrage Macro ou Frontier Rounds |

### Axe 2 — Périmètre d'Arbitrage (`--scope`)
| Scope | Description | Commande CLI |
|-------|-------------|--------------|
| `STORY` | Centré sur l'écran, le contrat d'API et les RM d'un récit unitaire | `grill-me --story <ID>` |
| `EPIC / PROJECT` | Architecture transverse, infra, conformité, exclusions globales | `grill-project` |

> **🚨 RÈGLE D'OR INVIOLABLE** : Choisir un format `ROUND` ne modifie en rien le périmètre d'analyse et ne constitue **EN AUCUN CAS** un ordre de rédaction de code ou de story.

### Table de Mapping du Langage Naturel (Expressions Informelles → Matrice)
| Expression utilisateur | Mapping déterministe | Ce que cela ne fait PAS |
|----------------------|---------------------|------------------------|
| *« mode macro »* / *« passe en macro »* | `format: ROUND` sur le scope courant | Ne change PAS le scope, ne déclenche PAS d'écriture |
| *« mode micro »* / *« question par question »* | `format: ATOMIC` sur le scope courant | Ne change PAS le scope |
| *« grill le projet »* / *« grill l'épopée »* | `scope: EPIC/PROJECT` avec format courant | Ne déclenche PAS la rédaction de stories |
| *« grill cette story »* | `scope: STORY` avec format courant | N'autorise PAS la promotion au-delà de `READY_FOR_GROOMING` |

### Dualité des Niveaux de Cadrage

#### 1. Cadrage Transverse (`scope: EPIC/PROJECT` — `grill-project`)
- **Moment** : En début de Phase 2 (PLAN & ANALYSE), immédiatement après l'ingestion.
- **Questions clés** : Architecture structurante, conformité, exclusions globales, hypothèses macro.
- **Livrables** : ADR transverses, `CONTEXT.md`, glossaire unifié.
- **Règle d'or** : Élimine 80% des questions répétitives en fixant le socle commun.

#### 2. Analyse Fine Unitaire (`scope: STORY` — `grill-me --story <ID>`)
- **Moment** : Au cours du sprint, lors de la prise en charge d'un récit (`IN_ANALYZE`).
- **Périmètre** : Strictement l'écran, le contrat d'API et les RM de CE récit (mono-récit strict).
- **Livrable** : Récit Palier 2 DoR 6/6 au maximum `READY_FOR_GROOMING`. Le passage vers `READY_FOR_DEV` requiert l'arbitrage humain exclusif de Gate 2.

---

## Déroulé Opérationnel en 4 Étapes

### Étape 0 : « Search-Before-Ask », Localisation SSOT, CONTEXT.md & Fact-Search FTS5
0. **Localiser la Source de Vérité Canonique AVANT toute recherche (ADR-0384)** : lire d'abord `Projects/<projet>/directives/tech.md` et `directives/business.md` s'ils existent, identifier la source de vérité canonique déclarée (hiérarchie à 3 niveaux : Canonique `docs/03-models/` > Amont `docs/00-ingested/` > Staging `reference/`), puis la charte projet `AGENTS.md`, puis `docs/01-architecture/`. **Ordre de recherche imposé : directives en tête.**
   - **Interdiction de brief non sourcé** : ne jamais transmettre à un sous-agent (`task`, `worker-spawn`) un brief référençant un chemin de modèle de données non confirmé comme canonique.
   - Citer la hiérarchie SSOT retenue dans le Dossier de Preuves.
1. Interroger l'index SQLite FTS5 (`.fact_search_index.db`) et `CONTEXT.md` pour identifier les maquettes SVG validées (`docs/05-assets/`), règles métier (`RM-XXX`), schémas DBML et vocabulaire ubique. En cas d'outil absent, d'erreur ou d'échec de requête SQLite, appliquer un fallback résilient par recherche textuelle locale dans `docs/00-ingested/`.
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

### Étape 4 : Clôture de Frontière, Arrêt Formel & Menu d'Orientation (ADR-0389 / ADR-0393)
La session se termine lorsque l'arbre de décision ne contient plus aucune zone d'ombre (Épuisement de Frontière / Frontier Exhaustion).

#### 4A. Arrêt Formel Post-Round (INVIOLABLE — ADR-0393)
Dès que la frontière de décision d'un round est vide :
1. **Cessation immédiate d'écriture** : L'agent a l'**interdiction formelle** d'enchaîner sur la rédaction de récits, de modifier des fichiers sous `backlog/stories/`, ou de promouvoir des statuts.
2. **Seul livrable autorisé** : Consignation des décisions dans l'ADR (`docs/01-architecture/ADR-XXX.md`) et mise à jour de `CONTEXT.md`.
3. **Menu d'Orientation Fermé Obligatoire** : L'agent clôt impérativement son message par :
   > *« Décisions actées et scellées dans l'ADR-XXX. Aucune story n'a été altérée. Quelle est votre instruction ?*
   > *(1) Découpage en ébauches DRAFT Palier 1 (`to-tickets`)*
   > *(2) Lancer le Micro-Grill 1:1 sur un récit spécifique*
   > *(3) Clôturer la session »*

#### 4B. Mandat Unitaire Strict d'Écriture
- **Aucun mandat d'écriture par défaut** après un round macro. Seule la sélection explicite d'un récit par l'humain confère le mandat d'instruire et rédiger **ce seul récit** (mono-récit strict).
- Toute story modifiée sans mandat unitaire valide est immédiatement rétrogradée en `DRAFT` avec purge du `content_hash` et consignation `UNAUTHORIZED_CASCADE_MUTATION`.

#### 4C. Plafond de Promotion Machine
- L'agent ne peut promouvoir un récit qu'au statut maximum `READY_FOR_GROOMING`.
- Toute promotion vers `READY_FOR_DEV` requiert l'arbitrage humain explicite exclusif de Gate 2.
- Toute tentative machine d'injecter `READY_FOR_DEV` provoque la levée immédiate de `LifecycleAuthorityError`.

#### 4D. Surveillance Context Budget ("Dumb Zone")
- Si la session dépasse **80k tokens**, déclencher un point de contrôle (`checkpoint_in_flight`).
- Si elle dépasse **120k tokens**, interdiction d'ouvrir de nouvelles branches (clôture ou partitionnement en session fille).
- **Externalisation Continue** : Consigner les termes dans `CONTEXT.md` et les décisions filtrées dans l'ADR au fil de l'eau (principe stateful).
- **Délégation Isolée en Aval** : Seules les étapes d'implémentation (`build` / tests) sont ensuite confiées à un sous-agent avec contexte nettoyé.


---

## Table Anti-Rationalisation (Inviolable — ADR-0393 enrichie)

| # | Excuse de l'Agent (Paresse / Dérive) | Réalité & Règle Inviolable |
| :---: | :--- | :--- |
| 1 | *"Le besoin est évident, je peux rédiger la story directement sans poser de question."* | Même les besoins simples cachent des hypothèses tacites non vérifiées. Le Dossier de Preuves Documentaires est obligatoire pour chaque récit. |
| 2 | *"Je vais poser 5 questions dépendantes d'un coup en Micro-Grill."* | En Micro-Grill, le batching sature l'attention. La règle d'or sur un récit est **1 seule question atomique par tour** (sauf en format `ROUND` où les lots de 2-4 questions orthogonales sont autorisés). |
| 3 | *"Je vais débattre pendant 15 tours sur l'ergonomie visuelle du formulaire."* | L'ergonomie ne se discute pas en texte pur. Déclencher immédiatement le **Handoff Pattern** et générer un prototype jetable HTML/SVG. |
| 4 | *"La session de grill est finie, je vais faire un reset de contexte pour rédiger au propre."* | **Interdiction formelle de reset**. Le context window contient la mémoire vive de tous les arbitrages. Enchaîner directement sur la rédaction si le mandat unitaire est accordé. |
| 5 | *"Je vais griller chaque story sans faire de cadrage macro global."* | Conduit au syndrome du perroquet et à l'incohérence systémique. Exécuter `grill-project` avant d'entamer le micro-grilling. |
| 7 | *"L'utilisateur a demandé le mode macro, donc j'ai mandat de rédiger toutes les stories."* | **Illusion du mandat global (ADR-0393)** : `format: ROUND` ne confère aucun mandat d'écriture. Seul le choix explicite dans le menu d'orientation autorise la rédaction mono-récit. |
| 8 | *"Le Macro-Grill est terminé, je passe tout en READY_FOR_DEV."* | **Auto-attribution de Gate 2 (ADR-0393)** : Statut machine maximal = `READY_FOR_GROOMING`. `READY_FOR_DEV` est réservé à l'arbitrage humain. |
| 9 | *"Le PO a validé le cadrage macro, j'enchaîne directement sur les 5 récits."* | **Absence d'arrêt formel (ADR-0393)** : Arrêt post-round et menu d'orientation obligatoires. Enchaînement sans confirmation explicite interdit. |

---

## Vérification de Sortie
- [ ] Dossier de Preuves consigné dans `memory/evidence/<STORY_ID>_fact_dossier.md` (ou terminal).
- [ ] 100% des citations au format Grounding (`[fichier.md:Lignes X-Y]`).
- [ ] Questions Ungrillables déroutées vers des prototypes jetables si nécessaire.
- [ ] Frontière de décision validée vide par l'utilisateur.
- [ ] Récit enrichi au gabarit `story_template.md` avec DoR 6/6 dans la continuité du fil de session.

