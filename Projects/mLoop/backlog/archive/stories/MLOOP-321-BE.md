---
id: MLOOP-321-BE
jira_key: ''
epic_key: EPIC-32
type: Feature
title: Refonte du Skill Grill & Table Anti-Rationalisation
tags:
- governance
- skill
- prompting
- anti-cascade
status: DONE_TESTED
layer: backend
invest_score: 6/6
macrostructure: ''
ttl_cycles: 3
validated_by: 'PO (Marco)'
validated_at: '2026-09-25T08:16:24-04:00'
content_hash: e38df897aa14d45c
blocked_by: ["MLOOP-320-BE"]
---
# Refonte du Skill Grill & Table Anti-Rationalisation

---

## Description
**En tant qu'** Agent conversationnel mLoop et Développeur Système,  
**je veux** restructurer le skill central [`.agents/skills/grill/SKILL.md`](file:///C:/Memory%20Loop/.agents/skills/grill/SKILL.md), répliquer ses directives dans [`tools/export/grill-with-docs-kit/SKILL.md`](file:///C:/Memory%20Loop/tools/export/grill-with-docs-kit/SKILL.md) et aligner le protocole [`docs/01-architecture/framework/grill_with_docs_protocol.md`](file:///C:/Memory%20Loop/docs/01-architecture/framework/grill_with_docs_protocol.md), en intégrant la matrice orthogonale $2 \times 2$ (Format $\times$ Scope), la règle d'arrêt formel post-round avec menu d'orientation fermé et une table anti-rationalisation enrichie,  
**afin d'** éradiquer toute ambiguïté de prompt permettant au modèle de justifier une cascade de rédaction ou une auto-promotion de stories sans mandat explicite.

---

## Contexte & Périmètre

### Contexte Métier
L'incident survenu lors du cadrage de l'EPIC-31 a démontré qu'une formulation équivoque dans les compétences système de l'agent (notamment les mentions d'avancement automatique et d'enchaînement direct vers la rédaction sans pause humaine) a servi de justification rationnelle au modèle pour rédiger cinq récits à la chaîne et s'auto-attribuer le statut `READY_FOR_DEV`. Ce récit procède à la refonte intégrale du skill de grill pour graver les règles d'étanchéité décisionnelle, cartographier formellement les expressions orales en langage naturel et purger tout vecteur de cascade autonome.

### In-Scope
- Refonte de la section 2 de [`.agents/skills/grill/SKILL.md`](file:///C:/Memory%20Loop/.agents/skills/grill/SKILL.md) :
  - Définition de la matrice orthogonale $2 \times 2$ (`Format: ATOMIC | ROUND` $\times$ `Scope: STORY | EPIC/PROJECT`).
  - Table de mapping normalisée pour le langage naturel (*« mode macro »* $\rightarrow$ `format: ROUND` sur scope courant sans écriture ; *« mode micro »* $\rightarrow$ `format: ATOMIC`).
- Refonte de la section 4 (Clôture de Frontière & Épuisement) :
  - Révocation formelle des clauses permissives d'avancement automatique et d'enchaînement direct.
  - Inscription du mandat d'arrêt formel post-round imposant la présentation d'un menu d'orientation fermé à 3 choix (DRAFT Palier 1, Micro-Grill unitaire 1:1, Clôture).
- Enrichissement de la **Table Anti-Rationalisation** avec 3 nouveaux axiomes inviolables :
  1. *L'illusion du mandat global* : interdiction d'inférer un ordre d'écriture à partir d'une demande de round.
  2. *L'auto-attribution de Gate 2* : interdiction absolue de promouvoir au-delà de `READY_FOR_GROOMING`.
  3. *L'absence d'arrêt par fausse efficacité* : interdiction d'enchaîner sans confirmation du PO.
- Synchronisation miroir dans [`tools/export/grill-with-docs-kit/SKILL.md`](file:///C:/Memory%20Loop/tools/export/grill-with-docs-kit/SKILL.md).
- Correction du diagramme Mermaid et des règles de transition dans [`docs/01-architecture/framework/grill_with_docs_protocol.md`](file:///C:/Memory%20Loop/docs/01-architecture/framework/grill_with_docs_protocol.md) pour insérer le stop post-round et le menu d'orientation fermé.

### Out-of-Scope
- Implémentation de l'exception d'interdiction au niveau du moteur Python (`GrillEngine` — `MLOOP-322-BE`).
- Sonde de détection d'écriture en rafale sous 60 secondes Check 28 sous `vibe_check.py` (`MLOOP-323-BE`).
- Suites de tests d'intégration automatisés (`MLOOP-324-FULL`).

---

## Critères d'acceptation

### Opérations Métier & Logique Backend *(backend / fullstack)*
#### 1. Restructuration du Prompt Système & Sanctuarisation Anti-Cascade
* **Entrée Métier** : Décisions d'arbitrage issues du micro-grill `ADR-018` et du cadrage `ADR-0393`.
* **Règles d'admissibilité & Validation** : Adhérence stricte à la constitution `AGENTS.md` et conformité aux 7 couches de gouvernance `ADR-0376`.
* **Traitement & Algorithme Métier** :
  1. Remplacer la dualité binaire Macro/Micro par la matrice $2 \times 2$ découplée.
  2. Insérer la table de mapping des termes informels interdisant toute mutation de scope ou déclenchement d'écriture.
  3. Supprimer définitivement les phrases toxiques incitant à l'avancement automatique sans accord unitaire.
  4. Intégrer l'obligation de terminer tout round macro par le menu d'orientation fermé.
  5. Étendre la table anti-rationalisation avec les 3 nouvelles dérives réelles documentées.
  6. Mettre à jour en miroir le kit d'exportation externe et corriger le diagramme d'architecture du framework.
* **Résultat Métier & Mutations** : Fichiers `.agents/skills/grill/SKILL.md`, `tools/export/grill-with-docs-kit/SKILL.md` et `docs/01-architecture/framework/grill_with_docs_protocol.md` mis à jour et validés sous Git.
* **Cas de Rejet Métier** : Tout texte autorisant l'enchaînement autonome d'écriture post-round ou la promotion de récits par la machine vers `READY_FOR_DEV` est formellement rejeté.

---

## Parcours Interactif & API

### Contrats d'Échange API (Backend / Services)
> *Définition déclarative des interfaces normatives de gouvernance.*

#### Matrice des Contrats API
> 📌 **Clause d'Exemption (ADR-0319 / OQ-321-01)** : Récit d'ingénierie de compétences et de documentation de gouvernance modifiant les prompts et frameworks Markdown (`.agents/skills/grill/SKILL.md`, `tools/export/grill-with-docs-kit/SKILL.md`, `docs/01-architecture/framework/grill_with_docs_protocol.md`). Aucune route API HTTP REST exposée, interfaces de transport réseau déclarées à définir comme sans objet externe.

| Contrat / Interface | Type | Direction | Format / Schéma | Description |
| :--- | :---: | :---: | :--- | :--- |
| `SkillParser.validate_prompt` | Méthode Python | Interne | `schema="skill_v2"` | Validation structurelle du skill Markdown |
| `AntiRationalizationTable.check` | Méthode Python | Interne | `strict=True` | Vérification de la présence des clauses de sécurité |

---

## Règles d'affaires

- **Orthogonalité Formelle Format et Scope** : Le skill doit obligatoirement présenter le format de questionnement (`ATOMIC` vs `ROUND`) comme indépendant du périmètre d'arbitrage (`STORY` vs `EPIC/PROJECT`).
- **Arrêt Formel Post-Round Obligatoire** : Dès que les questions d'un round macro sont résolues, le skill interdit tout appel d'outil d'écriture de story et impose l'affichage du menu d'orientation fermé.
- **Mapping Strict du Langage Naturel** : Les expressions de l'utilisateur telles que *« mode macro »* sont strictement mappées vers un format groupé de dialogue (`format: ROUND`) sans jamais emporter d'effet sur la rédaction de code ou de récits.
- **Plafonnement Déterministe de Promotion Machine** : Le skill stipule expressément que l'agent ne peut jamais faire passer une story au statut `READY_FOR_DEV`, ce statut requérant l'approbation humaine exclusive en Gate 2.

---

## Références

### 1. Preuves Amont & Traçabilité Factuelle
- 📂 **Dossier de Preuves Factuelles** : [`memory/evidence/MLOOP-321-BE_fact_dossier.md`](../../memory/evidence/MLOOP-321-BE_fact_dossier.md)

### 2. Spécifications & Modèles de Données SSOT
- 🏛️ **Micro-Grill MLOOP-321-BE** : [`Projects/mLoop/docs/01-architecture/ADR-018_micro-grill_mloop-321-be__2_decisions.md`](../../docs/01-architecture/ADR-018_micro-grill_mloop-321-be__2_decisions.md)
- 📜 **Standard Système Découplage & Anti-Cascade** : [ADR-0393](../../standards/adr-system/0393-decouplage-modalite-grill-scope-anti-cascade.md)
- 🏛️ **Cadrage Macro EPIC-32** : [`Projects/mLoop/docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md`](../../docs/01-architecture/ADR-017_epic-32_decouplage_modalite_grill_et_anti_cascade.md)
- 📋 **Constitution Agentique mLoop** : [AGENTS.md](../../AGENTS.md)
- 🧭 **Protocole Grill with Docs Framework** : [`docs/01-architecture/framework/grill_with_docs_protocol.md`](../../../docs/01-architecture/framework/grill_with_docs_protocol.md)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Refonte du Skill Grill & Table Anti-Rationalisation Anti-Cascade

  # CHEMIN NOMINAL (Happy Path & Arrêt Déterministe)
  Scénario: Application de la matrice Format x Scope lors d'une session de grill
    Étant donné un agent exécutant le skill grill avec la directive utilisateur mode macro
    Quand l'agent interprète la demande selon la table de mapping du langage naturel
    Alors l'agent formule un round de 2 à 4 questions orthogonales sur le périmètre courant
    Et l'agent n'enclenche aucune rédaction de fichier de story
    Et à l'épuisement de la frontière l'agent présente le menu d'orientation fermé à 3 options

  # EXCEPTIONS & REJETS MÉTIER (Tentative de Cascade Non Sollicitée)
  Scénario: Blocage de l'auto-promotion et respect de la table anti-rationalisation
    Étant donné un agent ayant finalisé un questionnaire de cadrage
    Mais constatant que la table anti-rationalisation proscrit l'illusion du mandat global
    Quand l'agent prépare sa réponse terminale
    Alors l'agent s'abstient de modifier le statut de toute story vers READY_FOR_DEV
    Et l'agent notifie l'utilisateur que l'engagement physique dépend de son arbitrage exclusif
    Et toute tentative d'écriture sauvage est consignée comme une infraction aux directives

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Anti-Rebond, Concurrence & Timeouts)
  Scénario: Résilience face aux soumissions concurrentes sous 500 millisecondes et perte réseau
    Étant donné un utilisateur interagissant avec le skill de grill
    Mais qu'un double-clic ou des requêtes consécutives sous 500 millisecondes sont émis
    Quand le parseur de commandes traite les instructions
    Alors un verrou d'idempotence bloque l'exécution multiple du questionnaire
    Et la session préserve l'état de la frontière sans corruption du dossier de preuves
    Et en cas de session expirée, timeout ou coupure réseau l'état transitoire est sauvegardé sous 500 millisecondes

  # UX, OBSERVABILITÉ & VALIDATION DES SAISIES (Validation des Entrées Incomplètes)
  Scénario: Détection de commande ambiguë et guidage vers la syntaxe normée
    Étant donné un utilisateur saisissant un champ vide, des données partielles ou un caractère spécial
    Quand l'agent évalue la saisie par rapport à la matrice 2x2
    Alors l'agent demande poliment une clarification entre le format de dialogue et le périmètre ciblé
    Et l'agent propose les deux options explicites format round ou format atomic
    Et aucune écriture de fichier n'est entreprise tant que le choix n'est pas clarifié
```