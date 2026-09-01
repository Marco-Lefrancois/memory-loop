# 🛠️ Guide de Développement des Skills & Standard Agent Plugins 1.0 (ADR-0309)

Dans le framework **mLoop v2.0.0**, le pilier **Skills** donne des capacités d'action physiques à l'écosystème. Une "Skill" n'est pas codée en dur dans le Kernel, elle est chargée de manière dynamique au standard **Agent Plugins 1.0 (ADR-0309)**.

---

## 1. Structure d'une Skill & Package Plugin AP 1.0

Toutes les Skills résident dans `.agents/skills/`. Chaque Skill est un dossier contenant au minimum un fichier d'instruction `SKILL.md`.

```text
.agents/
├── plugin.json           # Manifeste global du Plugin (AP 1.0)
├── mcp.json              # Déclaration des serveurs MCP locaux
└── skills/
    └── ma_nouvelle_skill/
        ├── SKILL.md      # Le manifeste obligatoire (YAML Frontmatter + Markdown)
        ├── resources/    # Modèles, blueprints et références optionnelles
        └── script.py     # Scripts Python ou CLI optionnels
```

## 2. Le Manifeste `SKILL.md` & Divulgation Progressive

Ce fichier est lu par l'agent via la règle de **Divulgation Progressive (Progressive Disclosure)** :
Pour préserver le budget d'instructions du prompt système, le contenu de `SKILL.md` est chargé via `view_file` **uniquement lors de l'activation de la phase ou tâche correspondante**.

```yaml
---
name: api-stripe-connector
description: "Permet de vérifier et créer des souscriptions via l'API Stripe locale."
---

# Instructions d'Utilisation
1. Ne **jamais** utiliser la clé de production. Toujours vérifier la variable `STRIPE_TEST_KEY`.
2. Utiliser le script fourni `script.py` avec l'argument `--check`.
3. Consigner la trace dans l'EvidencePack (`memory/evidence/`).
```

## 3. Validation & Export Multi-Clients (ADR-0309)

Les compétences mLoop sont entièrement portables et distribuables sur n'importe quel IDE ou agent compatible AP 1.0 (Cursor, VS Code, Copilot, Codex, Kiro, Antigravity) :

```bash
# Valider la conformité AP 1.0 du package
python src/swarm.py plugin-validate --project mLoop

# Exporter le package autonome pour distribution
python src/swarm.py plugin-export --project mLoop --output <dossier_destination>
```

## 4. Moteur d'Auto-Calibrage (`calibrate.py`)

Les compétences sont surveillées en continu par le moteur `calibrate`. La commande `python src/swarm.py calibrate` vérifie que toutes les compétences déclarées sont référencées dans l'index de routage et auto-répare tout écart détecté.

## 5. Règles d'Or des Skills
1. **Indépendance** : Une skill ne doit jamais modifier directement le Kernel `src/swarm.py`.
2. **Zero-Fluff & Exit Code** : Les scripts d'une Skill doivent renvoyer un statut de succès (0) ou d'erreur (>0) et produire des sorties structurées.
3. **Evidence Integration** : Toute action critique exécutée par une skill alimente la traçabilité via `EvidencePackEngine`.
