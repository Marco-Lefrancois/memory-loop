---
id: "ADR-0379"
title: "StandardsGraph SQLite Engine, Scoping JIT des Directives & Bouclier Runtime Anti-Outrepassage"
status: "Accepté"
date: "2026-09-18"
type: "Type 1 — Architecture & Gouvernance Système"
authority: "mLoop Senior Architecture Board"
validation_rules:
  - check_id: "standards_graph_sqlite_integrity"
    severity: "BLOCKING"
    description: "La base memory/standards_graph.db doit être intègre, synchronisée avec les .md et répondre en < 0.2ms."
    params:
      db_path: "memory/standards_graph.db"
  - check_id: "confinement_shield_no_bypass"
    severity: "BLOCKING"
    description: "Les agents au runtime ne doivent jamais pouvoir outrepasser leur whitelist d'outils ni leurs permissions de système de fichiers."
    params:
      enforced_roles: ["explorer", "plan", "orchestrator", "sentinel", "worker"]
  - check_id: "agent_ssot_markdown_only"
    severity: "BLOCKING"
    description: "Les profils d'agents doivent résider exclusivement sous .agents/agents/*.md sans fichiers .toml résiduels."
    params:
      forbidden_path: "standards/agents/*.toml"
---

# ADR-0379 : StandardsGraph SQLite Engine, Scoping JIT des Directives & Bouclier Runtime Anti-Outrepassage

## Statut
**Accepté (SSOT Normatif)** — 18 Septembre 2026

---

## 1. Contexte & Problématique

Dans l'écosystème **Memory Loop (mLoop)**, l'architecture documentaire Markdown (`.md`) constitue la **Source Unique de Vérité (SSOT)**.
Cependant, l'analyse approfondie du code source Python a révélé plusieurs angles morts critiques :
1. **La Dérive du Hardcoding (Dual-SSOT Drift)** : Des constantes d'étapes de cycle de vie et des définitions de portes étaient dupliquées en dur dans Python (`src/core/layout.py`, `src/core/lifecycle.py`) ou dans des fichiers intermédiaires (`standards/adr-contracts.json`).
2. **La Déconnexion des Compétences au Runtime** : Bien que 38 compétences soient documentées dans `.agents/skills/*/SKILL.md`, `src/core/skill_registry.py` maintenait un dictionnaire en mémoire statique vide, privant la CLI et les agents de la découverte dynamique (`python src/swarm.py skill-list` renvoyait un catalogue vide).
3. **La Duplication des Profils d'Agents** : Les rôles étaient décrits dans `.agents/agents/*.md` pour les LLMs et dans `standards/agents/*.toml` pour le daemon Python, induisant une dérive silencieuse des configurations.
4. **Le Risque d'Outrepassage par les Modèles Paresseux (*Lazy LLMs*)** : Les modèles de langage rapides ou paresseux ont tendance à contourner les consignes purement textuelles (tenter d'écrire des récits de stories prématurément, halluciner des compétences non autorisées ou sauter des étapes d'ingestion). Les instructions en prompt doux (*soft guidance*) sont insuffisantes ; un confinement physique déterministe au runtime est obligatoire.

---

## 2. Décisions d'Architecture

### 2.1 Moteur Central `StandardsGraph` (Base SQLite Compilée)
- **SSOT Absolue** : Les fichiers Markdown (`standards/adr-system/*.md`, `.agents/skills/*/SKILL.md`, `.agents/agents/*.md`, `.agents/rules/*.md`) restent la **seule et unique source de vérité** modifiée par les humains et les agents.
- **Matérialisation Graphique SQLite** : Pour éviter le coût de parsing de 80+ fichiers Markdown à chaque invocation CLI tout en interdisant le stockage en gros fichier JSON plat, le framework compile et indexe les standards dans une base SQLite embarquée : `memory/standards_graph.db`.
- **Synchronisation Incrémentale à Haute Performance** : Le moteur compare l'empreinte globale (mtime + SHA-256) des répertoires sources. Si aucun fichier n'a changé, le chargement en mémoire prend **moins de 0.2 milliseconde**.

### 2.2 Scoping Ciblé & Chargement à la Demande (JIT Scoping)
- **Segmentation par Étape & Domaine** : Les ADRs et règles sont rattachées à des phases de cycle de vie (`STAGE_1_INGEST`, `STAGE_2_PLAN_ANALYSE`, etc.).
- **Isolation Contextuelle** : Lorsqu'un pipeline s'exécute (ex: `swarm ingest`), `StandardsGraph` n'extrait que les règles et ADRs applicables à la phase active. Le reste de la constitution mLoop demeure au repos, sans saturer la mémoire ni le contexte LLM.
- **Divulgation Progressive (*Progressive Disclosure*)** : Les métadonnées YAML légères sont toujours disponibles pour le routage ; le corps complet du texte Markdown n'est lu sur le disque que sur demande explicite.

### 2.3 Compétences à la Demande (*Just-in-Time Skills*)
- **Catalogue Découvrable** : Les 38 compétences documentées dans `.agents/skills/` sont automatiquement indexées et exposées via `python src/swarm.py skill-list`.
- **Activation Restreinte JIT** : Seules les compétences explicitement déclarées dans le profil d'agent actif (ex: `skills: [markitdown, graphify, fact-search, svg-ocr]`) sont instanciées et exposées au runtime.
- **Import Paresseux (*Lazy Loading*)** : Le module Python d'une compétence n'est importé en mémoire que lors de son invocation effective.

### 2.4 Bouclier Runtime Anti-Outrepassage (*Confinement Shield*)
Pour neutraliser définitivement la paresse et les raccourcis des LLMs, le runtime Python déploie 4 verrous déterministes infranchissables :
1. **Filtrage Physique des Outils (*Tool Whitelisting*)** : Si un modèle tente d'invoquer une compétence non déclarée dans son profil `explorer.md`, le runtime intercepte l'appel et lève immédiatement une exception bloquante `PermissionDeniedError`.
2. **Prison de Système de Fichiers (*Filesystem Write-Jail*)** : Les écritures de fichiers sont vérifiées par rapport aux listes `allowed_write_paths` et `forbidden_write_paths`. En Phase 1, toute tentative d'écriture dans `backlog/stories/**`, `docs/01-architecture/**` ou `src/**` déclenche une `SandboxViolationError`.
3. **Preuve de Travail Cryptographique (*Proof-of-Work*)** : La complétion de la Phase 1 exige la présence de `docs/00-ingested/source_manifest.json` avec les empreintes SHA-256 réelles de 100% des fichiers de `reference/` et la distinction épistémique (`what_it_actually_proves`).
4. **Sentinelle Déterministe de Porte 1** : La validation de Porte 1 s'effectue exclusivement par du code Python pur sans LLM (Check 13 = 0 story, manifeste complet).

### 2.5 Unification des Agents (.md comme SSOT Unique)
- Les fichiers `.toml` sous `standards/agents/` sont définitivement supprimés.
- Les profils d'agents sous `.agents/agents/*.md` portent dans leur frontmatter YAML l'intégralité des attributs d'exécution (`model`, `model_reasoning_effort`, `sandbox_mode`, `allowed_write_paths`, `forbidden_write_paths`, `skills`).
- Le corps Markdown constitue le prompt système officiel de l'agent.

---

## 3. Schéma Relationnel SQLite

```sql
CREATE TABLE standards_nodes (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    name TEXT NOT NULL,
    title TEXT,
    stage TEXT DEFAULT 'GLOBAL',
    domain TEXT DEFAULT 'general',
    file_path TEXT NOT NULL,
    file_mtime REAL NOT NULL,
    file_sha256 TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    body_markdown TEXT,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE standards_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    metadata_json TEXT,
    FOREIGN KEY(source_id) REFERENCES standards_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY(target_id) REFERENCES standards_nodes(id) ON DELETE CASCADE,
    UNIQUE(source_id, target_id, relation_type)
);

CREATE TABLE sync_meta (
    source_key TEXT PRIMARY KEY,
    directory_path TEXT NOT NULL,
    aggregate_hash TEXT NOT NULL,
    last_sync_timestamp REAL NOT NULL,
    node_count INTEGER NOT NULL
);
```

---

## 4. Conséquences & Bénéfices

- **Zéro Dérive Documentaire** : Impossible pour le code Python d'ignorer une règle ou un profil agent mis à jour dans un `.md`.
- **Démarrage Ultra-Rapide** : Temps de consultation `< 0.2ms`, aucune latence perceptible pour l'utilisateur ou la suite de tests.
- **Sécurité et Rigueur d'Exécution** : Les agents ne peuvent plus halluciner ou exécuter des tâches non autorisées en phase amont.
- **Traçabilité Totale** : Contrôle n°19 dans Vibe-Check garantissant la conformité en continu.
