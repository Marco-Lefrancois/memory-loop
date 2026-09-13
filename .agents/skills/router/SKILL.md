---
name: router
description: "Router: Index des compétences mLoop et Agent-Skills. Indique quel skill utiliser selon le contexte."
disable-model-invocation: true
---

# 🧭 Router (Index Central des Compétences mLoop)

> **Status:** Active | **Standard:** mLoop Core & Agent-Skills Symbiosis (ADR-0365)

## 🎯 Rôle Souverain
Ce catalogue centralise la cartographie complète des compétences disponibles dans `.agents/skills/`. Il permet d'orienter les agents et l'humain vers la compétence idoine selon la phase du cycle de vie cognitif ou la tâche d'ingénierie à accomplir.

---

## 🗺️ Cartographie Thématique des Compétences

### 🏛️ Compétences Maîtresses de Cycle de Vie mLoop
- **`/grill`** : Interrogatoire interactif sans concession, cadrage pré-rédaction, constitution du Dossier de Preuves Documentaires et alignement PO.
- **`/plan`** : Analyse d'affaires amont, découpage en tranches verticales INVEST, filtrage des ADRs Type 1 et synchronisation du backlog.
- **`/sentinel`** : Audit QA contradictoire impitoyable (Avocat du Diable / Red Team), détection de failles logiques et vérification par le doute.
- **`/herdr-orchestration`** : Gouvernance d'orchestration PTY multi-agents via Herdr, isolation Fork & Harvest et politique Anti-Zombies.

### ⚙️ Ingénierie Logicielle & Standards d'Exécution (Agent-Skills)
- **`/test-driven-development`** : Développement piloté par les tests (Red-Green-Refactor, Règle de Beyoncé, pyramide de tests).
- **`/source-driven-development`** : Grounding technique officiel sur documentation SDK versionnée et lecture en lecture seule.
- **`/doubt-driven-development`** : Vérification contradictoire in-flight en contexte vierge et traque des hypothèses tacites.
- **`/spec-driven-development`** : Rédaction de spécifications formelles, PRDs et contrats d'interface avant tout code.
- **`/constraint-driven-development`** : Définition des bornes de qualité, budgets de performance et gardiens non-négociables.
- **`/planning-and-task-breakdown`** : Graphe de sous-tâches physiques atomiques ordonnées par dépendance (< 5 fichiers).
- **`/incremental-implementation`** : Implémentation par tranches verticales minces commitées avec validation continue.
- **`/context-engineering`** : Optimisation du budget de contexte (< 75%), compression d'historique et évitement du lost-in-the-middle.
- **`/code-simplification`** : Refactoring chirurgical sans altération de comportement (principe de la barrière de Chesterton).
- **`/security-and-hardening`** : Prévention OWASP Top 10, détection de secrets, audits de dépendances et principe de moindre privilège.
- **`/performance-optimization`** : Profiling, détection de requêtes N+1, budgétisation de latence et Core Web Vitals.
- **`/shipping-and-launch`** : Déploiement progressif (Canary), feature flags, observabilité active et seuils de rollback.
- **`/api-and-interface-design`** : Conception de contrats d'API déclaratifs, schémas REST / gRPC et gestion d'erreurs typées.
- **`/browser-testing-with-devtools`** : Vérification visuelle, inspection DOM et capture de traces console via Chrome DevTools MCP.
- **`/debugging-and-error-recovery`** : Diagnostic systématique des causes racines d'anomalies et procédures de rétablissement.

### 🧠 Modélisation, Graphify & Architecture
- **`/graph-engineering`** : Requêtage de sous-graphes NetworkX et hygiène du graphe de connaissances sémantique.
- **`/archify`** : Générateur de diagrammes d'architecture interactifs vectoriels HTML/SVG.
- **`/obsidian-canvas`** : Cartographie spatiale 2D de composants et flux sous forme de toiles Obsidian Canvas.
- **`/visual-mermaid`** : Génération de diagrammes de séquences, états et flux au format Mermaid.
- **`/visual-excalidraw`** : Modélisation visuelle interactive sur tableau blanc Excalidraw.

### 🔬 Outils Multimodaux, Ingestion & OCR
- **`/svg-ocr`** : Extraction OCR headless Chromium des maquettes vectorielles à texte courbé (`docs/05-assets/`).
- **`/svg-optimize`** : Minification, nettoyage de chemins et optimisation des fichiers SVG.
- **`/markitdown`** : Ingestion documentaire multimodale universelle (Office, PDF, HTML, images vers Markdown).

### 🛡️ Contrôle, Hygiène & Audit
- **`/calibrate`** : Auto-étalonnage continu des piliers de l'écosystème mLoop (CLI, MCP, skills, guardrails).
- **`/blindspot-scan`** : Audit proactif des 4 vecteurs d'angles morts (compatibilité, diamants, race conditions).
- **`/triage`** : Triage du backlog et découpage en récits verticaux actionnables.
- **`/handoff`** : Synthèse de passation de contexte en fin de session pour prévenir la dérive mémorielle.
- **`/wait-what`** : Pause d'auto-audit contradicteur en cas d'incohérence détectée (Stop & Ask).
- **`/rubber-duck`** : Verbalisation structurée d'un problème complexe pour lever un blocage logique.
- **`/design-taste`** : Évaluation de l'élégance visuelle, hiérarchie typographique et respect des standards UI.
- **`/impeccable`** : Finition esthétique chirurgicale et perfection des détails d'interface.