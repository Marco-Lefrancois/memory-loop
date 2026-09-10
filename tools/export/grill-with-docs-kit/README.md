# 🐣 Kit d'Ingénierie : *Grill with Docs & Fact-Search Engine*

> **Le Framework Universel d'Alignement d'Architecture & d'Audit Sans Complaisance pour Assistants IA**  
> *Conçu pour Product Owners, Architectes, Développeurs et Équipes d'Ingénierie IA.*

---

## 💡 Qu'est-ce que le *Grill with Docs* ?

Les assistants IA génératifs actuels souffrent de deux maux majeurs :
1. **La complaisance passive (*Docile Polishing / Sycophancy*)** : Ils valident docilement les brouillons, extrapolent des règles métier inexistantes et inventent des endpoints d'API fictifs.
2. **La fatigue décisionnelle** : Ils posent des listes interminables de questions triviales dont les réponses sont **déjà écrites** dans la documentation ingérée.

Le **Grill with Docs** résout ce problème en instaurant la **Loi de Séparation Épistémique (Frederick Brooks & Matt Pocock)** :
* 🔍 **Les Faits (*Look it up*)** : Responsabilité **100% IA**. L'agent interroge les sources (transcriptions d'ateliers, modèles DBML, maquettes) via un moteur de recherche plein-texte FTS5 et extrait les citations exactes avec numéros de lignes. **Interdiction formelle d'interroger l'humain sur ce qui est déjà documenté.**
* ⚖️ **Les Décisions (*Ask the PO*)** : Responsabilité **100% Humain**. L'agent présente un **Dossier de Preuves Documentaires** en 4 blocs et ne pose qu'**une seule question d'arbitrage ciblée à la fois** (avec recommandation motivée).
* 🛡️ **Les Preuves (*EvidencePacks*)** : Toutes les citations et empreintes de fichiers sont consignées dans un sidecar `evidence.json`, préservant la **pureté no-code** du récit Markdown final (*Universal Dev Handoff*).
* 🧪 **La Vérification (*Fact-Check NLI*)** : Les critères et scénarios Gherkin sont décomposés en affirmations atomiques et audités par inférence logique (Entailment / Contradiction) pour produire un **Certificat de Confiance (Trust Index)** garanti par un guardrail physique sur disque.

---

## 📂 Contenu du Kit

```text
grill-with-docs-kit/
├── README.md                           # Guide d'utilisation et d'intégration
├── SKILL.md                            # Directive d'agent universelle (Cursor, Antigravity, Claude, OpenCode)
├── scripts/
│   └── fact_search.py                  # Moteur autonome SQLite FTS5 de recherche de preuves & Evidence Logger
├── standards/
│   └── ADR-0326-fact-search-and-grounding.md  # Décision d'architecture formelle SSOT
├── templates/
│   ├── dossier_preuves_template.md     # Gabarit du dossier affiché au PO lors du Grill
│   ├── story_template.md               # Gabarit officiel de User Story (4 Piliers Gherkin)
│   └── evidence_template.json          # Modèle d'EvidencePack JSON sidecar
└── docs/
    ├── presentation_synthese_10min_table_ronde.md  # ⚡ PITCH 10 MIN : Synthèse des 3 Piliers pour la Table Ronde
    ├── guide_demonstrations_concretes.md           # 🎬 GUIDE DÉMOS LIVE : Commandes, sorties réelles & script de démo
    ├── presentation_table_ronde.md                 # Deck Détaillé : Grill with Docs, Fact-Search & Fact-Check
    ├── presentation_vibe_coding_vs_vibe_check.md   # Deck Détaillé : Du Vibe Coding au Vibe Check (Harness Engineering)
    ├── presentation_archify.md                     # Deck Détaillé : Archify (Cartographie d'Architecture Déclarative)
    └── assets/
        ├── grill-with-docs-epistemic-flow.architecture.html  # 🌐 Diagramme Interactif Vivant (Généré par Archify)
        ├── screenshot_ide_split_screen.png                  # 📸 Capture Écran Scindé IDE
        └── screenshot_dossier_preuves_verbatims.png         # 📸 Capture Dossier de Preuves Documentaires
```

---

## 🚀 Démarrage Rapide (En 3 Minutes)

### Étape 1 : Indexer vos documents
Déposez vos transcriptions de réunions, spécifications, exports DBML ou documents de référence dans un dossier `docs/` (ou sous-dossiers), puis lancez l'indexation :

```bash
python scripts/fact_search.py index --docs-dir docs/
```
> *Génère instantanément un index SQLite FTS5 ultra-rapide et autonome.*

### Étape 2 : Lancer une recherche factuelle
Pour trouver un fait ou vérifier une affirmation avant de spécifier :

```bash
python scripts/fact_search.py search "date de ponte plus ancienne prioritaire"
```
> *Retourne le fichier source, le paragraphe exact, les numéros de ligne et le score de pertinence.*

### Étape 3 : Installer le Skill dans votre Agent IA
* **Pour Google Antigravity / OpenCode** : Copiez le dossier sous `.agents/skills/grill/`.
* **Pour Cursor IDE** : Copiez le contenu de `SKILL.md` dans votre `.cursorrules` ou dans un prompt système.
* **Pour Claude Code / Claude Projects** : Ajoutez `SKILL.md` aux instructions de projet.

---

## 📊 Le Gabarit Standard du Dossier de Preuves

Chaque question posée au PO par l'IA doit **obligatoirement** suivre cette structure :

```markdown
# 🐣 Session Grill with Docs — <STORY_ID> (<Titre Métier Pur>)

### 📂 Dossier de Preuves Documentaires
1. 🖼️ Maquettes & Notes UI : [Lien Maquette SSOT] (Ajustement validé)
2. 🎙️ Extraits Verbatim : Source doc.md (Lignes X–Y) : « Citation mot-à-mot » ➔ Fait établi : ...
3. 🗄️ Structure de Données DBML : Tables, types et statuts de cycle de vie réels.

### ❓ Question d'Arbitrage #N
* Option A (Recommandée — Motivation technique) : ...
* Option B : ...
👉 Quel arbitrage retenez-vous ?
```

---

## 📜 Licence & Origine
Développé dans le cadre de l'écosystème d'architecture logicielle **Memory Loop (mLoop)**.  
Libre d'utilisation, de modification et de partage pour vos équipes.
