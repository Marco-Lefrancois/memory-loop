# ADR-0335 : Ingestion Épistémique & Grounding Anti-Hallucination

## Statut
**Accepté (SSOT Normatif)** — 24 août 2026

## Contexte & Problématique
Dans l'écosystème Memory Loop (mLoop), les sessions de Recherche & Développement (R&D), l'ingestion de spécifications denses (livrables clients, normes techniques, documentations d'API, papiers de recherche scientifique) et la rédaction de récits verticaux exposent les modèles d'IA à trois dérives cognitives majeures :
1. **La lecture superficielle (Abstract/Title Drift)** : L'IA base ses synthèses sur des résumés ou introductions sans inspecter en profondeur les données brutes, les chiffres expérimentaux et la mécanique interne.
2. **La sur-extrapolation des preuves (Claim Inflation)** : L'IA confond ce qu'un document *affirme/promet* avec ce qu'il *démontre formellement*, masquant les hypothèses de travail, les cas non testés et les limites de validité.
3. **Le piège du linter mécanique ("Lint as the Goal")** : La validation se limite à cocher des cases structurelles (présence de titres, conformité INVEST superficielle) sans audit contradictoire de la substance analytique.

L'étude approfondie du projet open-source **DeepPaperNote** (`917Dhj/DeepPaperNote`) met en lumière des mécanismes de rigueur méthodologique particulièrement pertinents. Conformément à la volonté de **bonifier l'existant sans prolifération de composants superflus**, cette décision d'architecture intègre ces principes au cœur des outils, compétences et standards existants de mLoop.

---

## Décision d'Architecture

### 1. Contrat de Source Canonique & Manifeste d'Ingestion (`source_manifest`)
- Pour tout document dense ou papier ingéré via `python src/swarm.py ingest` ou `research`, le système mLoop privilégie une extraction déterministe en **sections brutes canoniques** (`raw_sections`) et un **manifeste de source** (`source_manifest.json`).
- Le modèle d'analyse ne doit jamais formuler d'architecture ou de règles d'affaires sur la seule base d'un sommaire ou d'un résumé : la matière première brute fait foi (*Raw-source authority*).

### 2. Découplage Épistémique des Preuves (`what_it_actually_proves` vs `what_it_does_not_prove`)
- Dans toute analyse d'impact R&D, fiche de traçabilité ou EvidencePack (`memory/evidence/<STORY_ID>_evidence.json`), les assertions clés doivent être ventilées selon 3 dimensions épistémiques strictes :
  - **`what_it_actually_proves`** : Ce que les faits, données chiffrées, captures ou code source valident sans ambiguïté.
  - **`what_it_does_not_prove`** : Ce que la source ne démontre pas (angles morts, cas limites non abordés, limites de performance, environnements non testés).
  - **`claim_boundaries`** : Le périmètre exact de validité de chaque affirmation.

### 3. Gouvernance Multi-Gates : *"Lint is a Floor, not the Goal"*
- La validation d'une spécification mLoop suit une séquence en entonnoir :
  1. **Grounding Gate** : Vérification que chaque assertion repose sur un ancrage documentaire vérifié avant d'entamer la rédaction détaillée.
  2. **Deterministic Script Lint** : Vérification mécanique de la syntaxe, du gabarit `story_template.md` et des invariants INVEST.
  3. **Substantive Qualitative Review (Sentinel / Rubber-Duck)** : Audit de fond sur la cohérence métier, les 4 Piliers Gherkin et les 5 axes d'angles morts (ADR-0334).
  4. **Readability & Dev Handoff Gate** : Clarté rédactionnelle, pureté déclarative no-code et suppression de tout jargon ou pseudo-code parasitaire.

### 4. Fiches Terminologiques Atomiques & Maillage Sémantique (Length-Aware)
- L'enrichissement du vocabulaire métier (`docs/03-models/`, `docs/04-transverse/`) adopte une approche inspirée de `paper-glossary` :
  - Détection déterministe des entités nommées et concepts clés avec **plafonds adaptatifs basés sur la volumétrie du texte** (*Length-Aware Candidate Limits*), évitant la pollution par du bruit sémantique.
  - Génération de définitions atomiques réutilisables et renvoi bidirectionnel vers le graphe de connaissances (Graphify).

### 5. Politique "Fail-Closed" & Zéro Hallucination de Source
- Si une source est corrompue, inaccessible ou incomplète : interdiction absolue de produire une spécification dégradée ou synthétique.
- L'agent doit s'arrêter immédiatement, consigner une question ouverte explicite (`OQ-XXX`) ou demander le document source requis.

---

## Impacts & Bonification des Composants Existants

1. **Skill `research-and-develop` (`.agents/skills/research-and-develop/SKILL.md`)** :
   - Mise à niveau du workflow en 5 étapes pour y intégrer le Manifeste de Source, l'Analyse Épistémique et le Grounding Gate.
2. **Skill `sentinel` (`.agents/skills/sentinel/SKILL.md`) & `rubber-duck`** :
   - Renforcement du 3e axe d'attaque ("Confrontation Fact-Search aux Sources Réelles") par l'évaluation du diptyque *Proved vs Unproved*.
3. **Standards EvidencePacks (`memory/evidence/`)** :
   - Intégration naturelle des frontières de validité (`claim_boundaries`) dans les métadonnées de traçabilité.

---

## Conséquences & Bénéfices

- **Robustesse Anti-Hallucination Maximale** : Élimination du risque de faux consensus ou d'extrapolation lors de la lecture de documentations tierces.
- **Transparence pour l'Équipe de Développement** : Les développeurs savent exactement ce qui est formellement garanti par l'architecture vs ce qui reste à valider en intégration.
- **Économie de Complexité** : Zéro création d'agents ou de skills jetables ; intégration directe des meilleures pratiques au sein du moteur mLoop existant.
