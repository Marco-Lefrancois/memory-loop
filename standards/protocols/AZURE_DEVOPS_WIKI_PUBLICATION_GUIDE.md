# 🏛️ Guide de Publication Azure DevOps Wiki & Architecture Doc-as-Code (SSOT)

Ce document constitue le **standard protocolaire mLoop** pour la publication de la documentation d'architecture et des spécifications fonctionnelles sous forme de **Wiki Azure DevOps** via le mécanisme *« Publish code as wiki »*.

---

## 1. 🎯 Philosophie : La Synergie Repo Git vs Wiki Web

Dans l'écosystème mLoop, la documentation n'est jamais un artefact passif décorrélé du code. Elle est gérée selon le paradigme **Doc-as-Code** (Markdown versionné sous Git), consommé simultanément par deux populations aux besoins distincts :

```mermaid
graph LR
    subgraph Machine & Agents IA (IDE / Local)
        Repo[📂 Dépôt Git Markdown] -->|Zéro latence / Grep / Graphify / AST| Agent[🤖 Agents IA & Devs]
        Agent -->|Git Push / Pull Requests| Repo
    end
    
    subgraph Azure DevOps Cloud (Consommation Humaine)
        Repo -->|Publish code as wiki| Wiki[🌐 Wiki Azure DevOps]
        Wiki -->|Consultation visuelle / Mermaid / Liens| Humains[👥 PO / PM / Architectes / Devs]
    end
```

---

## 2. 📊 Analyse Comparative : Repo Git vs Wiki Cloud pour les Agents IA

Pourquoi les agents de codage et d'orchestration IA (Cursor, Copilot, Antigravity, OpenCode, Claude Code) sont infiniment plus performants sur un **Repo physique** que sur un **Wiki Cloud (API / Web)** :

| Dimension | 📂 Repo Git Local (Fichiers Markdown) | 🌐 Wiki Cloud (Interface Web / API ADO) |
| :--- | :--- | :--- |
| **Latence & Accès I/O** | ⚡ **Instantané (Zéro latence)** : Lecture directe sur le filesystem (`view_file`, `grep_search`). | ⏳ **Lent & Fragile** : Requêtes REST API, authentification PAT/OAuth, rate-limits. |
| **Indexation Sémantique & Graphe** | 🧠 **Maximale** : Exploitable par Graphify, SQLite FTS5, embeddings locaux, CodeGraph. | 🔍 **Limitée** : Dépend du moteur de recherche textuel basique d'Azure DevOps. |
| **Navigation Multi-Fichiers** | 🔗 **Précision chirurgicale** : Résolution locale des chemins relatifs RFC 3986 (`../01-architecture/`). | ⚠️ **Fragile** : Risque de liens cassés (`pagePath`, `friendlyName`, GUIDs instables). |
| **Traçabilité & Historique** | 📜 **Atomique (`git diff`, `git log`)** : L'IA comprend instantanément l'évolution d'une décision (ADR). | 👁️ **Historique visuel** : Difficile à inspecter et manipuler programmatiquement par l'agent. |
| **Automatisation & Guardrails** | 🛡️ **Linters & CI/CD** : Contrôle automatique (`struct-check`, `vibe-check`, `wikifix`). | ❌ **Zéro contrôle strict** : Risque de dérive de gabarit ou de syntaxe non conforme. |
| **Consommation de Tokens** | 📉 **Économie chirurgicale** : Chargement ciblé des sections pertinentes via slice notation. | 📈 **Gaspillage** : Téléchargement de pages entières souvent polluées de balises HTML. |

---

## 3. 🛠️ Configuration Recommandée : "Publish code as wiki"

Pour publier un dépôt d'architecture mLoop dans Azure DevOps :

1. Rendez-vous dans **Azure DevOps** ➔ Votre projet (ex: `NmediaInc/Nms.Mobile`).
2. Allez dans **Overview** ➔ **Wiki**.
3. Dans le sélecteur de Wiki, cliquez sur **"Publish code as wiki"** *(Ne jamais choisir "Create project wiki" qui crée un repo fantôme déconnecté)*.
4. Paramétrage :
   - **Repository** : Nom du dépôt Git de documentation (ex: `OneTrust_Doc`).
   - **Branch** : `main`.
   - **Folder** : `/docs` *(Recommandé pour exposer une vue épurée aux parties prenantes)* ou `/` *(pour exposer l'ensemble `AGENTS`, `backlog`, `docs`)*.
   - **Wiki name** : Nom clair et fédérateur (ex: `Metro OneTrust SSOT`).

---

## 4. 📐 Standards d'Arborescence & Navigation Azure DevOps

### A. Règle des Pages Parentes vs Dossiers
Dans Azure DevOps Wiki, un dossier n'est **pas cliquable** s'il ne possède pas de fichier Markdown éponyme au même niveau hiérarchique :
- **Standard** : Pour qu'un répertoire `01-architecture/` possède une page de garde cliquable, créer un fichier `01-architecture.md` au même niveau que le dossier `01-architecture/`.

```text
docs/
├── 01-architecture.md         <-- Page de garde de la section Architecture
├── 01-architecture/
│   ├── ADR-008-Blindage-Natif.md
│   ├── ADR-020-Gouvernance-Firebase-Analytics-GCM-v2.md
│   └── ADR-028-Conformite-AppInsights-OneTrust.md
├── 02-specs-fonctionnelles.md <-- Page de garde des règles métiers
├── 02-specs-fonctionnelles/
│   ├── REGLES_METIERS_LOI_25.md
│   └── MATRICE_PILOTAGE_SDK.md
├── 03-developpeur-guides.md   <-- Guides d'intégration C# / MAUI / WebViews
├── 03-developpeur-guides/
│   ├── setup-environnement.md
│   └── integration-sdk-csharp.md
├── 04-transverse.md           <-- Questions ouvertes, gouvernance
├── 04-transverse/
│   └── 00-questions-ouvertes-client.md
└── 05-assets/                 <-- Stockage des SVG, diagrammes et maquettes
```

### B. Ordonnancement de l'Affichage
- **Préfixes Numériques (`01-`, `02-`, `03-`)** : Tri naturel automatique dans l'arborescence sans maintenance additionnelle.
- **Fichiers `.order`** : À ajouter dans un sous-dossier si un ordre personnalisé non-alphabétique est requis (contient les noms de fichiers sans extension `.md`, un par ligne).

---

## 5. 🎨 Formatage Markdown & Rendu Natif Azure DevOps

| Élément | Pratique Recommandée (SSOT) | À Proscrire |
| :--- | :--- | :--- |
| **Diagrammes** | Blocs natifs **Mermaid.js** (`graph TD`, `sequenceDiagram`, `stateDiagram`) compilés à la volée par Azure DevOps. | Captures d'écran matricielles (PNG/JPG) non éditables et non indexables. |
| **Alertes Visuelles** | Blocs de citations stylisés :<br>`> [!NOTE]`<br>`> [!IMPORTANT]`<br>`> [!WARNING]` | Texte brut sans mise en valeur typographique. |
| **Liens Relatifs** | Liens relatifs standard RFC 3986 :<br>`[Voir ADR-020](../01-architecture/ADR-020.md)` | URLs absolues web instables ou liens locaux Windows (`C:\...`). |
| **Tickets Jira & Work Items** | URL HTTPS complète pour Jira : `[MMA-4690](https://metroinc.atlassian.net/browse/MMA-4690)` ou `#ID` pour work items natifs ADO. | Clés Jira sans lien ou identifiants internes mLoop non synchronisés. |
| **Code & Contrats** | Extraits ciblés avec coloration syntaxique déclarative (`csharp`, `json`, `yaml`, `gherkin`). | Fichiers de code massifs copiés-collés intégralement. |
| **Images & Médias** | Stockage sous `docs/05-assets/` et liaison relative : `![Flux](../05-assets/flux.svg)`. | Hébergement externe non pérenne ou pièces jointes perdues. |

---

## 6. ⚖️ Gouvernance & Intégration CI/CD (Definition of Done)

1. **Pull Requests Obligatoires (Branch Protection)** :
   - La branche `main` du dépôt de documentation doit être protégée par une *Branch Policy*.
   - Toute modification architecturale ou fonctionnelle requiert une revue de code documentaire.
2. **Doc as Definition of Done (DoD)** :
   - Aucune User Story ne peut être clôturée (`CLOSED`) sans mise à jour synchronisée de la documentation d'architecture et des contrats dans le Wiki.
3. **Guardrails Automatisés mLoop** :
   - Exécution de `python src/swarm.py vibe-check` et `python src/swarm.py wikifix` pour interdire les liens orphelins, les références fantômes et les dérives de gabarit avant tout commit.
