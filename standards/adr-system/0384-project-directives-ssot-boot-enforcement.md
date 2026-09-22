# 🏛️ ADR-0384 : Application du Chargement des Directives Projet & Ancrage SSOT Canonique

- **Statut** : ACCEPTED
- **Date** : 22 septembre 2026
- **Décideurs** : Marco (Utilisateur) & mLoop Agent
- **En lien avec** : ADR-0322 (Boot Sequence), ADR-0320 (Grill with Docs), ADR-0376 (Audit 360° en 7 Couches), ADR-0319 (Contrats API)

---

## Contexte & Problème

Lors d'une revue contradictoire de récits sur le projet BoireFrere_Segment2, un audit de conformité SSOT a été délégué à des sous-agents briefés sur des sources d'ingestion amont (`docs/00-ingested/`) au lieu de la source de vérité canonique réelle (`docs/03-models/`). Cette erreur a produit un faux diagnostic de « conflit de modèle de données non résolu » nécessitant un arbitrage, alors que la hiérarchie SSOT était déjà tranchée dans `Projects/BoireFrere_Segment2/directives/tech.md` et `directives/business.md`.

Un balayage à froid des 7 couches de gouvernance mLoop a confirmé qu'**aucune règle n'oblige l'orchestrateur à charger les directives d'un projet** avant d'agir :
1. La charte racine `AGENTS.md` ne mentionne `directives/` que pour le framework lui-même, jamais pour un projet client.
2. La charte du projet témoin ne liste même pas son propre répertoire `directives/` et pointe une source amont comme « officielle ».
3. La Boot Sequence (ADR-0322) et les contrôles du guardrail de pré-vol ne vérifient pas la prise en compte des directives.

Le principe « les directives sont les Lois Fondamentales » était abondamment documenté mais **jamais encodé comme contrôle opposable**. C'est un gap de gouvernance, non une violation de règle existante.

---

## Décision Retenue

Établir l'application déterministe du chargement des directives projet et de l'ancrage sur la source de vérité canonique, à travers trois leviers additifs et un contrôle mécanique complémentaire.

### 1. Protocole Normatif Autonome
Création de `standards/protocols/PROJECT_DIRECTIVES_SSOT_PROTOCOL.md` déclarant la hiérarchie documentaire à trois niveaux (Canonique > Amont > Staging), l'obligation de localisation avant délégation, et la distinction des deux mécanismes de gouvernance.

### 2. Clause dans les Chartes d'Instructions
Ajout d'une clause « Chargement des Directives Projet & SSOT Canonique » dans `AGENTS.md` (propagée aux miroirs GEMINI.md/CLAUDE.md), imposant en Phase ≥ 2 la lecture des directives et l'identification du SSOT avant tout cadrage, audit ou délégation. Correction corrélative de la charte du projet témoin.

### 3. Renforcement du Skill d'Entrevue
Enrichissement de l'Étape 0 « Search-Before-Ask » du skill `grill` : ordre de recherche imposé (directives en tête) et interdiction de brief non sourcé.

### 4. Contrôles Mécaniques de Pré-Vol
- **Contrôle des directives** : conditionnel (n'agit que si un répertoire `directives/` existe), sévérité **WARNING** non bloquante.
- **Contrôle d'ancrage visuel** : matérialise le principe universel du Contrat Visuel Premier (Mécanisme A) pour les récits d'interface, sévérité **WARNING**.
- Correctif corollaire : la sémantique du verdict du guardrail passe de binaire (`passed == total`) à **tri-état** (PASS / WARNING / FAIL), les avertissements n'invalidant plus le verdict global.

---

## Caractère Non-Régressif (Invariant Critique)

Sur huit projets réels, seul BoireFrere_Segment2 possède un répertoire `directives/`. Le contrôle des directives est donc **strictement conditionnel** : en l'absence de `directives/`, il réussit immédiatement. Aucun projet existant ne régresse. Les scores de verdict sont recalculés au fil de l'eau, projet par projet, sans exigence de parité de score entre projets.

---

## Conséquences

### Positives
- Élimination de la classe d'erreur d'audit sur sources non autoritaires.
- Gouvernance documentaire citable et opposable.
- Le Contrat Visuel Premier devient mécaniquement contrôlé.

### Négatives / Coûts
- La sémantique du verdict du guardrail change pour tous les projets (assumé : recalcul au fil de l'eau).
- Les tests du guardrail encodant l'ancienne sémantique binaire doivent être réalignés.

### Neutres
- Aucune nouvelle commande CLI (contrôles internes au guardrail) : pas de dérive du guide.

---

## Alternatives Rejetées

- **Contrôle bloquant (FAIL) immédiat** : rejeté au profit d'un palier WARNING, le standard `directives/` n'étant pas encore généralisé.
- **Checks dédiés par directive projet** : rejeté (hardcoding projet-spécifique dans le cœur), remplacé par le chargement forcé générique (Mécanisme B).
- **Protocole enfoui dans un document existant** : rejeté au profit d'un fichier autonome citable.
