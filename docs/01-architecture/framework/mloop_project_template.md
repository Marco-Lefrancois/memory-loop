# Blueprint : Le "mLoop Project Template" (v2.0.0 & AP 1.0)

Pour démarrer de façon standardisée, chaque projet mLoop utilise ce **Template Repository** au standard **Agent Plugins 1.0 (ADR-0309)**. Il sépare l'intelligence cognitive (Système 2 - IDE Agentique) de la gouvernance et de la validation déterministe (Système 1 - Kernel Python).

---

## 1. L'Architecture Standardisée du Dépôt (Le "Skeleton")

Structure canonique d'un projet mLoop v2.0.0 :

```text
mon-projet-mloop/
│
├── .agents/                    # [Le Cerveau AP 1.0] Configuration & Skills Portables
│   ├── plugin.json             # Manifeste Plugin (ADR-0309)
│   ├── mcp.json                # Configuration des serveurs MCP locaux
│   ├── soul.json               # Identité & Ton Senior Tech Lead (Zero-Fluff)
│   ├── agents/                 # Définitions YAML des agents (orchestrator, plan, sentinel)
│   └── skills/                 # Catalogue des 21+ compétences portables (SKILL.md)
│
├── reference/                  # [Matière Première] Documents clients bruts (PDF, Office)
├── docs/                       # [Source de Vérité - SSOT] Architecture & Directives
│   ├── 00-ingested/            # Documents convertis en Markdown (ingest / markitdown)
│   ├── 01-architecture/        # Spécifications, ADRs et CONTEXT.md
│   └── 04-transverse/          # Registre des Questions Ouvertes (00-questions-ouvertes.md)
│
├── backlog/                    # [Terrain d'Exécution] stories verticaux tracer-bullet
│   ├── sprint_backlog.md       # État et découpage des stories
│   ├── STORY_MAPPING.md        # Verrouillage du découpage SSOT
│   └── stories/                # Contrats SCC au format US-XXX.md / REC-XXX.md
│
├── memory/                     # [La Mémoire] Stockage persistant & Audit
│   ├── knowledge_graph.json    # Graphe sémantique L3 (Graphify)
│   ├── active_project.json     # Pointeur du projet actif
│   └── evidence/               # Artefacts JSON d'audit EvidencePack (<STORY_ID>_evidence.json)
│
└── graphify-out/               # Indexation du code physique (Graphe AST)
```

> [!IMPORTANT]
> **La Règle d'Or (Le Contrat de Frontière)** :
> 1. **Projets Clients** : mLoop agit comme un Backend d'État, d'Architecture et de Validation. Le code physique de l'application client est modifié par le développeur humain.
> 2. **Protection Active (`story_guard.py`)** : Interdit physiquement toute écriture hors-périmètre du SCC.

---

## 2. Le Cycle Spec-Driven en 5 Phases

1. **Phase 1 : SPEC / INGEST** : Ingestion documentaire sous `reference/` vers `docs/00-ingested/` via `ingest`.
2. **Phase 2 : PLAN / ARCHI** : Entrevue interactive *Grill with Docs* (`grill`), modélisation DDD et création des stories verticaux dans `backlog/stories/`.
3. **Phase 3 : BUILD** : Implémentation incrémentale (humain / client ou mLoop self-dev pour `C:\Memory Loop\src`) sous la protection de `story_guard.py` et du DAG `graph-run`.
4. **Phase 4 : VALIDATE / QA** : Audit contradictoire Read-Only via `sentinel` / `rubber-duck`, validation des **4 Piliers Gherkin**, calcul du score INVEST et génération de l'EvidencePack (`memory/evidence/`).
5. **Phase 5 : SHIP / SYNC** : Clôture synchrone, synchronisation Graphify (`sync`), gouvernance Jira Cloud (`jira_sync` Story-Only) et auto-étalonnage continu (`calibrate` 8/8 PASS).

---

## 3. Commandes CLI d'Amorçage & Calibrage

```bash
# Amorçage obligatoire (Boot Sequence Anti-Amnésie)
python src/swarm.py resume --project <nom_projet>
python src/swarm.py vibe-check --project <nom_projet>

# Auto-étalonnage continu & auto-réparation
python src/swarm.py calibrate --project <nom_projet>

# Empaquetage & Exportation Plugin AP 1.0
python src/swarm.py plugin-validate --project mLoop
python src/swarm.py plugin-export --project mLoop --output <dir>
```
