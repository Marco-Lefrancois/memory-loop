---
name: grill
description: Interrogatoire interactif sans concession, alignement PO avec hypothèses et questions 1:1, arbitrage Faits vs Décisions, et constitution du Dossier de Preuves Documentaires. Use when clarifying requirements, interviewing a stakeholder before writing stories, or exploring architecture design trade-offs.
---

# 🛠️ Skill : Session Interactive Grill & Frontier Design Tree (`/grill`)

## Aperçu & Rôle Souverain
Ce skill régit la discipline d'interrogatoire sans concession (*Relentless Interview*) et de cadrage pré-rédaction entre l'agent mLoop et l'utilisateur pour aligner la vision fonctionnelle **AVANT** toute phase de build ([ADR-0320](../../standards/adr-system/README.md)).

## Déclencheurs & Exclusions
- **Quand l'utiliser** : Tout nouveau besoin, epic ou user story ambiguë, décision d'architecture controversée, ou désaccord sur une règle métier.
- **Quand NE PAS l'utiliser** : Pour chercher des faits documentés dans le code ou les specs existantes (utiliser `fact_search` FTS5 et [`source-driven-development`](../source-driven-development/SKILL.md)).

---

## Déroulé Opérationnel en 4 Étapes

### Étape 0 : « Search-Before-Ask » & Fact-Search FTS5
1. Interroger l'index SQLite FTS5 (`.fact_search_index.db`) pour identifier les maquettes SVG validées (`docs/05-assets/`), règles métier (`RM-XXX`) et schémas DBML.
2. Si un fait est consigné dans la documentation, **interdiction absolue de poser la question à l'humain**.
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

### Étape 4 : Clôture de Frontière (Frontier Empty)
La session se termine lorsque l'arbre de décision ne contient plus aucune zone d'ombre. Si la décision est de Type 1 (irréversible), générer l'ADR correspondant via [`.agents/references/adr-decision-checklist.md`](../references/adr-decision-checklist.md).

---

## Table Anti-Rationalisation (Inviolable)

| Excuse de l'Agent (Paresse) | Réalité & Règle Inviolable |
| :--- | :--- |
| *"Le besoin est évident, je peux rédiger la story directement sans poser de question."* | Même les besoins simples cachent des hypothèses tacites non vérifiées. Le Dossier de Preuves Documentaires est obligatoire pour chaque récit. |
| *"Je vais poser 5 questions d'un coup pour faire gagner du temps à l'utilisateur."* | Le batching sature l'attention humaine et produit des réponses incomplètes. La règle d'or est **1 seule question atomique par tour**. |
| *"L'utilisateur m'a dit 'fais au mieux', donc je décide à sa place sans documenter."* | « Au mieux » n'est pas un contrat. Formuler l'hypothèse sous forme de *Guess*, la faire valider en 1 tour, puis consigner la décision dans l'ADR. |
| *"Le PO a validé oralement, inutile de vérifier les types dans le schéma DBML."* | Le PO ignore souvent les contraintes de clés étrangères physiques. L'agent doit confronter le déclaratif au schéma relationnel réel. |

---

## Signaux d'Alerte (Red Flags)
- Poser une question dont la réponse figure dans un document `docs/00-ingested/` ou un SVG d'asset.
- Rédiger une story avec un statut `UNSUPPORTED` résiduel dans le dossier de preuves.
- Proposer une solution sans énoncer le compromis négatif (*trade-off*).

## Vérification de Sortie
- [ ] Dossier de Preuves consigné dans `memory/evidence/<STORY_ID>_fact_dossier.md` (ou affiché en terminal standard).
- [ ] 100% des citations sont au format Passage-Level Grounding (`[fichier.md:Lignes X-Y]`).
- [ ] Frontière de décision validée vide par l'utilisateur.
