---
name: router
description: "Router: Index des skills mLoop. Indique quel skill utiliser selon le contexte."
disable-model-invocation: true
---

# 🧭 Router (Index des Skills mLoop)

> **Status:** Active | **Standard:** mLoop Core

## 🎯 Purpose
Ce skill sert d'index et de guide pour naviguer dans l'écosystème des skills mLoop. Il permet de réduire la charge cognitive (Context Load) des agents en centralisant la cartographie des compétences. Invoquez-le manuellement avec `/router` lorsque vous ne savez pas quel skill utiliser.

## 🗺️ Cartographie des Skills

### 📌 Skills de Phase (Automatiques ou Manuels)
Ces skills gèrent le cycle de vie principal (A-P-QA) :
- **`/analyze`** (*Ingestion*) : Ingestion des sources, moissonnage documentaire (MCP Crawler) et modélisation du graphe sémantique (Graphify). À utiliser au tout début d'un projet ou d'une grosse feature.
- **`/plan`** (*Plan*) : Analyse d'affaires, exécution du "Grill with Docs", structuration des Stories (SCC) et rédaction d'ADR. Le moteur cognitif pour la prise de décision.
- **`/graph-engineering`** (*Orchestration*) : Orchestration de la topologie DAG multi-agents (Pattern Diamant, EvidencePacks, Reducer déterministe et Risk Routing).
- **`/validate`** (*Audit*) : Vérification QA, audit de conformité (WikiFix), vérification de l'isolation technique et calcul du score INVEST. La dernière étape avant le développement.

### 🛠️ Skills Utilitaires (Invoqués par l'Humain)
Ces skills sont paramétrés pour ne pas s'activer tout seuls afin de préserver le budget cognitif de l'IA :
- **`/handoff`** (*Handoff*) : Condense le contexte de la session active et génère un document de passation (Session Recall) pour éviter la pourriture du contexte. À utiliser en fin de session ou quand le contexte s'alourdit.
- **`/calibrate`** (*Calibrage*) : Auto-étalonnage continu des 8 piliers mLoop (CLI, opencode.json, skills, MCP, directives système, guardrails).
- **`/sop`** (*SOP*) : La "Bible" mLoop. Contient la Référence Standard des Opérations, l'architecture globale (Kernel-Pipeline) et les principes d'auto-amélioration.

### 🔬 Skills Externes & Spécialisés
- **`/design-taste`** : Compétence mLoop enregistrée automatiquement.
- **`/archify`** : Compétence mLoop enregistrée automatiquement.
- **`/impeccable`** : Compétence mLoop enregistrée automatiquement.
- **`/obsidian-canvas`** : Compétence mLoop enregistrée automatiquement.
- **`/visual-excalidraw`** : Compétence mLoop enregistrée automatiquement.
- **`/visual-mermaid`** : Compétence mLoop enregistrée automatiquement.
- **`/thinking-cynefin`** : Compétence mLoop enregistrée automatiquement.
- **`/thinking-kepner-tregoe`** : Compétence mLoop enregistrée automatiquement.
- **`/thinking-reversibility`** : Compétence mLoop enregistrée automatiquement.
- **`/thinking-theory-of-constraints`** : Compétence mLoop enregistrée automatiquement.
- **`/thinking-triz`** : Compétence mLoop enregistrée automatiquement.
- **`/thinking-via-negativa`** : Compétence mLoop enregistrée automatiquement.
- **`/herdr-orchestration`** : Compétence mLoop enregistrée automatiquement.
- **`/research-and-develop`** : Compétence mLoop enregistrée automatiquement.
- **`/sentinel`** : Compétence mLoop enregistrée automatiquement.
- **`/rubber-duck`** : Compétence mLoop enregistrée automatiquement.
- **`/svg-optimize`** : Compétence mLoop enregistrée automatiquement.
- **`/svg-ocr`** : Extraction du texte des maquettes SVG/PNG à texte vectorisé (paths) via rendu headless Chromium + OCR natif Windows. À utiliser quand le SVG n'a pas de balises `<text>` et que le modèle actif ne supporte pas l'entrée image.
- **`/grill`** : Compétence mLoop enregistrée automatiquement.
- **`/research`** : Recherche autonome via le Deep Research Pipeline (Scout -> Crawl -> Synthesize).
- **`/teach`** : Enseignement d'un nouveau concept ou skill à l'utilisateur dans le workspace actuel.
- **`/markitdown`** : Conversion Markdown universelle (Office, PDF, HTML, images) pour l'ingestion dans `docs/00-ingested/`.
- **`/blindspot-scan`** : Audit proactif des 4 vecteurs d'angles morts (compatibilité runtimes, dépendances diamant, race conditions, debug vs prod) et analyse comparative multi-codebases (ADR-0306).
- **`/office`** : Manipulation chirurgicale locale de fichiers Word, Excel et PowerPoint via `office_read`, `office_write`, `office_render`.
- **`/triage`** : Triage du backlog et découpage en récits verticaux actionnables (Agent-Ready) au gabarit `story_template.md`.
- **`/wait-what`** : Pause de sécurité et d'auto-audit contradicteur en cas d'incohérence ou de risque d'hallucination (Stop & Ask).
- **`/tdd`** : Implémentation physique guidée par les tests unitaires (Red-Green-Refactor).

## 🚀 Comment l'utiliser
Ne demandez pas à un agent d'exécuter le router. Utilisez vous-même la commande (ex: `/plan`) selon la phase où vous vous trouvez, ou demandez explicitement "Passe en phase validate".