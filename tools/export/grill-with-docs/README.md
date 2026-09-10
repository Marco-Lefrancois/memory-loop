# 🛠️ Grill-with-Docs : Production-Ready Agent Skill & Fact-Search Engine

> **Version** : 1.0.0  
> **Type** : Universal AI Coding Agent Skill & Verification Tooling  
> **Compatibilité** : Google Antigravity, OpenCode, Cursor, Claude Code, Windsurf, VS Code Copilot Workspace

---

## 📌 Présentation & Objectifs

`grill-with-docs` est un sous-système d'ingénierie logicielle pour agents IA qui garantit un alignement strict entre la documentation d'architecture (*SSOT*) et les récits fonctionnels (*User Stories*) avant toute phase de développement physique.

### Les 3 Principes Fondamentaux :
1. **Loi de Séparation Épistémique (*Faits vs Décisions*)** : L'agent IA a l'obligation formelle de chercher les faits dans la base documentaire (`Look it up`). L'humain (Product Owner / Architecte) est sollicité uniquement pour les arbitrages de valeur et de priorités (`Ask the PO`).
2. **Standard de Preuves Documentaires (*Passage-Level Grounding*)** : Toute question d'arbitrage est obligatoirement précédée d'un dossier de preuves vérifiables (liens de maquettes, citations verbatim avec numéros de ligne précis, structure de données DBML).
3. **Universal Dev Handoff (*Zero-Bruit*)** : La User Story finale reste 100% pure et orientée comportement métier (Gherkin 4 piliers). L'intégralité des preuves de traçabilité et des citations est isolée dans un artefact sidecar `memory/evidence/<STORY_ID>_evidence.json`.

---

## 📂 Structure du Package

```text
grill-with-docs/
├── SKILL.md                          # Définition formelle du Skill pour l'Agent IA
├── README.md                         # Documentation technique d'intégration
├── standards/
│   └── ARCHITECTURE.md               # Spécification formelle du modèle de preuves en 4 couches
├── schemas/
│   └── evidence_pack.schema.json     # Schéma JSON Schema validant les EvidencePacks
├── scripts/
│   ├── fact_search.py                # Moteur d'indexation et de recherche plein-texte SQLite FTS5
│   └── evidence_logger.py            # Validateur et gestionnaire de cycle de vie des EvidencePacks
└── templates/
    ├── dossier_preuves.template.md   # Gabarit du dossier de preuves affiché lors de l'interview
    ├── story.template.md             # Gabarit canonique de User Story (Frontmatter + 4 Piliers Gherkin)
    └── evidence.template.json        # Modèle d'EvidencePack JSON sidecar
```

---

## ⚙️ Installation & Intégration

### 1. Structure Recommandée dans votre Dépôt
Pour intégrer ce package dans un projet existant :

```text
mon-projet/
├── .agents/
│   └── skills/
│       └── grill/                    # Copier le contenu du package ici
│           ├── SKILL.md
│           ├── scripts/
│           ├── schemas/
│           └── templates/
├── docs/                             # Base documentaire ingérée (Markdown, DBML, Specs)
├── backlog/
│   └── stories/                      # User Stories générées
└── memory/
    ├── evidence/                     # EvidencePacks JSON générés
    └── fact_search_log.jsonl         # Journal d'audit append-only
```

### 2. Intégration par Environnement d'Agent
* **Google Antigravity & OpenCode** : Déposez le dossier sous `.agents/skills/grill/`. Le skill est automatiquement découvert et invocable via `/grill` ou par l'orchestrateur.
* **Cursor IDE** : Référencez `SKILL.md` dans `.cursorrules` ou `.cursor/rules/grill.mdc`.
* **Claude Code / Projects** : Chargez `SKILL.md` et `ARCHITECTURE.md` dans les instructions de projet (*Project Knowledge*).

---

## 💻 Utilisation des Outils CLI (Scripts)

Les scripts sont conçus pour être exécutés soit par l'humain en ligne de commande, soit de façon autonome par un agent IA via ses outils d'exécution (`run_command` / `bash`).

### A. Indexation de la Documentation
Indexe récursivement tous les fichiers Markdown, DBML, JSON et textes sous `docs/` dans une base SQLite FTS5 locale ultra-rapide (`.fact_search_index.db`) :

```bash
python scripts/fact_search.py index --docs-dir docs/
```

### B. Recherche de Preuves Factuelles
Recherche les passages pertinents avec extraction automatique des numéros de lignes et des sections :

```bash
# Mode texte lisible pour terminal :
python scripts/fact_search.py search "règle de calcul des heures d'incubation"

# Mode JSON pour consommation programmatique par un agent IA :
python scripts/fact_search.py search "règle de calcul" --json
```

### C. Validation & Enregistrement d'un EvidencePack
Génère ou met à jour le sidecar JSON d'une story avec calcul d'empreinte SHA-256 et validation contre le schéma :

```bash
python scripts/evidence_logger.py log \
  --story-id "STORY-001" \
  --output "memory/evidence/STORY-001_evidence.json" \
  --source-file "docs/ateliers/atelier_incubation.md" \
  --start-line 313 \
  --end-line 337 \
  --verbatim "Les œufs les plus vieux sont prioritaires overall." \
  --fact "Calcul centralisé du drapeau is_oldest_priority pour la date la plus ancienne globale."
```

Pour valider l'intégrité structurelle de tous les EvidencePacks d'un projet :
```bash
python scripts/evidence_logger.py validate-all --evidence-dir "memory/evidence"
```

---

## 📋 Standard du Gabarit de Preuves (Visual Grounding)

À chaque tour d'interview, l'agent IA structure son intervention selon ce format strict :

```markdown
# 🐣 Session Grill with Docs — <STORY_ID> (<Titre Métier Pur>)

### 📂 Dossier de Preuves Documentaires
1. 🖼️ Maquettes & Notes UI : [Lien Maquette SSOT] (Ajustement validé)
2. 🎙️ Extraits Verbatim : Source <fichier.md> (Lignes X–Y) : « Citation mot-à-mot » ➔ Fait établi : ...
3. 🗄️ Structure de Données DBML : Entités, clés et types réels.

### ❓ Question d'Arbitrage #N
* Option A (Recommandée — Motivation technique) : ...
* Option B : ...
👉 Quel arbitrage retenez-vous ?
```

---

## 🛡️ Spécification des 4 Piliers Gherkin (Definition of Ready)
Toute story rédigée à l'issue d'une session de Grilling doit obligatoirement comporter les 4 piliers de test suivants :
1. **Pilier 1 : Nominal** (Chemins heureux standard).
2. **Pilier 2 : Exceptions** (Erreurs fonctionnelles, validations, codes HTTP 400/404/422).
3. **Pilier 3 : Résilience & Mode Dégradé** (Coupures réseau, timeouts 503, concurrence, anti-rebond).
4. **Pilier 4 : UX & Ergonomie** (États de chargement, réactivité < 200ms, retours utilisateurs).
