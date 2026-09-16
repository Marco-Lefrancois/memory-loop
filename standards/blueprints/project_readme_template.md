# 🚀 {{PROJECT_NAME}} — Documentation & Architecture SSOT

Bienvenue dans le dépôt officiel de documentation d'architecture, de règles d'affaires et de cadrage pour le projet **{{PROJECT_NAME}}**.

---

## 🎯 Objectifs du Projet
1. Cadrage fonctionnel et découpage vertical des récits utilisateur (Gabarit Gold Standard).
2. Source de Vérité Unique (SSOT) des règles métier et des contrats d'architecture.

---

## 📂 Architecture du Dépôt (Versionné dans Git)

```
{{PROJECT_NAME}}/
├── 📄 README.md                # Documentation produit et point d'entrée humain
├── 📄 AGENTS.md                # Source de vérité agentique (Boot sequence & guardrails)
├── 📄 opencode.json            # Configuration IDE OpenCode (MCP & commandes)
├── 📄 .gitignore               # Protection Git (exclusion de reference/, .codegraph/)
├── 📂 backlog/                 # User Stories (Gherkin 4 Piliers) & sprint_backlog.md
├── 📂 docs/                    # Architecture SSOT, ADRs, règles métier
└── 📂 memory/                  # EvidencePacks JSON & état de session
```

> [!NOTE]
> **Espace Local Staging (`reference/`)** : Le dossier local `reference/` (matière première brute) est exclu de Git par le `.gitignore`. Toute la matière utile est normalisée en Markdown dans `docs/00-ingested/`.
