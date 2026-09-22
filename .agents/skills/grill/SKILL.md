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

### Étape 2 : Questions 1:1 avec "Guess" Attaché (Pattern Interview-Me)
L'humain réagit 3x plus vite pour corriger une fausse supposition que pour formuler une réponse abstraite :
- Poser **exactement 1 question par tour** (zéro rafale de questions).
- Toujours attacher un *Guess* (votre meilleure supposition déduite) et une recommandation motivée.
```markdown
❓ **Q : <Question atomique sur la frontière active> ?**
💡 **GUESS** : <Supposition de l'agent basée sur le contexte existant>
➡️ **Recommandation mLoop** : <Option A ou B motivée par les standards>
```

### Étape 3 : Traque du « Want vs Should Want »
Poser la question brise-glace de désencombrement :
> *« Si vous n'aviez de comptes à rendre à personne et aucune contrainte d'héritage, que voudriez-vous réellement construire ici ? »*

### Étape 4 : Clôture de Frontière & Épuisement (Frontier Exhaustion)
La session se termine lorsque l'arbre de décision ne contient plus aucune zone d'ombre (épuisement de frontière).
- En Macro (`grill-project`) : enregistrement de la décision via ADR et passage au découpage `to-tickets`.
- En Micro (`grill-me --story <ID>`) : dès qu'un récit atteint l'épuisement de frontière, l'agent consigne la décision et avance automatiquement vers le récit suivant ou bascule la story vers `READY_FOR_GROOMING` puis `READY_FOR_DEV` après validation humaine.

---

## Table Anti-Rationalisation (Inviolable)

| Excuse de l'Agent (Paresse) | Réalité & Règle Inviolable |
| :--- | :--- |
| *"Le besoin est évident, je peux rédiger la story directement sans poser de question."* | Même les besoins simples cachent des hypothèses tacites non vérifiées. Le Dossier de Preuves Documentaires est obligatoire pour chaque récit. |
| *"Je vais poser 5 questions d'un coup pour faire gagner du temps à l'utilisateur."* | Le batching sature l'attention humaine et produit des réponses incomplètes. La règle d'or est **1 seule question atomique par tour**. |
| *"Je vais griller chaque story sans faire de cadrage macro global."* | Conduit au syndrome du perroquet et à l'incohérence systémique. Exécuter `grill-project` avant d'entamer le micro-grilling. |
| *"L'utilisateur m'a dit 'fais au mieux', donc je décide à sa place sans documenter."* | « Au mieux » n'est pas un contrat. Formuler l'hypothèse sous forme de *Guess*, la faire valider en 1 tour, puis consigner la décision dans l'ADR. |

---

## Vérification de Sortie
- [ ] Dossier de Preuves consigné dans `memory/evidence/<STORY_ID>_fact_dossier.md` (ou terminal).
- [ ] 100% des citations au format Grounding (`[fichier.md:Lignes X-Y]`).
- [ ] Frontière de décision validée vide par l'utilisateur.
- [ ] Récit enrichi au gabarit `story_template.md` avec DoR 6/6.
