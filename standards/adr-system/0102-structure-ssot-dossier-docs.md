# ADR-0102 : Structure Canonique & Source Unique de Vérité (SSOT) du Dossier `docs/`
## Statut : Accepté (Série 01xx - SSOT Documentation)

---

## 1. Contexte

Le répertoire `docs/` de chaque projet mLoop est le cœur du travail d'analyse d'affaires et d'architecture (*Business Analysis & Domain Architecture*). Il doit suivre une arborescence normée pour éviter l'éparpillement documentaire et garantir une indexation optimale par Graphify. Bien que `backlog/` soit hors de `docs/`, le document central `backlog/STORY_MAPPING.md` fait partie intégrante de la documentation de gouvernance macro et doit être traité comme un artefact SSOT.

---

## 2. Décision

Nous imposons l'**Arborescence Canonique SSOT et la Taxonomie Sub-Directory Globale** suivante pour tout répertoire `Projects/<nom_projet>/` dans l'écosystème Memory Loop :

```text
Projects/<nom_projet>/
├── docs/
│   ├── index.md                      <-- Index sémantique global & Carte d'orientation Graphify
│   │
│   ├── 00-ingested/                  <-- Matière première ingérée depuis reference/
│   │   ├── index.md                  <-- Index des sources ingérées
│   │   ├── 01-sow-et-contrats/       <-- Énoncés de travaux, Kickoffs & SOW
│   │   ├── 02-guides-et-specs/       <-- Guides d'implémentation & spécifications éditeur
│   │   ├── 03-scans-et-inventaires/  <-- Scans officiels consolidés & cartographies d'inventaire
│   │   ├── 04-api-reference/         <-- Documentation API & références SDK
│   │   └── archives-temp/            <-- (Optionnel) Variantes temporaires d'ingestion LLM
│   │
│   ├── 01-architecture/              <-- Architecture technique, ADRs & Diagrammes
│   │   ├── README.md                 <-- Registre général des ADRs du projet
│   │   ├── ADR-XXX-Titre-Court.md    <-- ADRs normalisées en Kebab-Case
│   │   └── syntheses/                <-- Comparatifs codebases, matrices & plans de contingence
│   │
│   ├── 02-business-rules/            <-- Règles d'affaires du domaine (RM-XXX) & matrices
│   │   ├── README.md                 <-- Index des règles métiers vivantes
│   │   ├── DIRECTIVES_...md          <-- Directives métiers & exigences légales
│   │   ├── MATRICE_...md             <-- Matrices fonctionnelles & plans de tests QA
│   │   └── archives-audits/          <-- Historique des rapports d'audits temporaires
│   │
│   ├── 03-models/                    <-- Modèles de données & schémas (Dataverse, SQL, ADF)
│   │   ├── README.md
│   │   └── schemas/
│   │
│   ├── 04-transverse/                <-- Questions ouvertes, glossaire & journal
│   │   ├── README.md
│   │   ├── 00-questions-ouvertes-client.md   (Q-XXX)
│   │   ├── 00-questions-ouvertes-devteam.md  (QD-XXX)
│   │   └── JOURNAL_DE_BORD.md
│   │
│   └── 05-assets/                    <-- Actifs visuels & graphiques versionnés (ADR-0332)
│       ├── maquettes/                <-- Maquettes vectorielles d'écrans (SVG, WebP)
│       ├── diagrams/                 <-- Schémas d'architecture et flux exportés
│       └── images/                   <-- Captures d'écran et illustrations documentaires
└── backlog/
    └── sprint_backlog.md             <-- Master SSOT du backlog unifié (FOOD, COMMERCE, SANTE)
```

**Règles de Gouvernance Système Globale :**
- **Interdiction des dossiers "Fourre-tout"** : Les sous-dossiers `00` à `04` doivent obligatoirement utiliser les sous-répertoires thématiques ci-dessus dès que le volume dépasse 5 fichiers.
- **Règlementation des Archives** : Les rapports d'audits temporaires ou les fichiers d'analyses LLM intermédiaires doivent être isolés dans des sous-dossiers `archives-audits/` ou `archives-temp/`.
- **`index.md` / `README.md`** : Chaque sous-dossier de documentation possède un fichier d'index maintenant la cartographie des documents.
- **Normalisation Kebab-Case** : Les ADRs de projets doivent utiliser le format `ADR-XXX-Titre-Court.md` pour garantir l'interopérabilité multi-plateforme.

---

## 3. Conséquences

- **Lisibilité Maximale** : Structure prévisible pour les développeurs et l'IA.
- **Indexation Graphify** : Navigation sémantique instantanée.
