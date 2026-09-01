# Compatibilité Inter-Plateforme des Skills mLoop

> **Dernière mise à jour :** 2026-07-21
> **Référence standard :** [Microsoft Agent Skills Specification](https://devblogs.microsoft.com/agent-framework/give-your-agents-domain-expertise-with-agent-skills-in-microsoft-agent-framework/)

## Contexte

Les skills mLoop (situés dans .agents/skills/) sont basés sur le format **Agent Skills open standard**, co-convergé avec l'initiative Microsoft Agent Framework publiée en mars 2026. Ce standard définit une structure de répertoire portable et lisible par tous les IDE agentiques modernes.

Les skills mLoop sont **nativement portables** vers plusieurs plateformes sans modification, grâce à cette convergence architecturale.

---

## Tableau de Compatibilité des Plateformes

| Plateforme | Support 
ame | Support description | Extensions mLoop | Compatibilité |
|---|---|---|---|---|
| **Antigravity IDE** (Google DeepMind) | ✅ Natif | ✅ Natif | ✅ Toutes supportées | 🟢 **Natif** |
| **Claude Code** (Anthropic) | ✅ Natif | ✅ Natif | ⚠️ Ignorées silencieusement | 🟢 **Compatible** |
| **Microsoft Agent Framework (Python)** | ✅ Natif | ✅ Natif | ⚠️ Ignorées silencieusement | 🟢 **Compatible** |
| **Microsoft Agent Framework (.NET)** | ✅ Natif | ✅ Natif | ⚠️ Ignorées silencieusement | 🟢 **Compatible** |
| **GitHub Copilot** | ✅ Natif | ✅ Natif | ⚠️ Ignorées silencieusement | 🟡 **Partiel*** |
| **agentskills.io** (registry communautaire) | ✅ Natif | ✅ Natif | ⚠️ Ignorées | 🟡 **Publiable*** |

> *GitHub Copilot et le registry agentskills.io peuvent nécessiter l'ajout d'un champ ersion dans le frontmatter YAML.

---

## Structure Standard vs Extensions mLoop

### Champs YAML Obligatoires (Standard universel)

`yaml
---
name: <nom-du-skill>        # Obligatoire - identifiant unique
description: <description>  # Obligatoire - utilisé pour la découverte (progressive disclosure)
---
`

> [!IMPORTANT]
> Ces deux champs sont les **seuls requis** par le standard inter-plateforme.
> Tous les skills mLoop les possèdent. ✅

### Champs YAML Extensions mLoop (Non-destructifs)

Ces champs sont propres à l'écosystème mLoop. Ils sont ignorés sans erreur par les plateformes tierces.

| Champ | Rôle |
|---|---|
| disable-model-invocation: true | Empêche l'invocation LLM directe du skill (mode lecture seule) |
| rgument-hint: <texte> | Affiche un hint dans la palette de commandes |

### Structure de Répertoire Standard

`
.agents/skills/<nom-du-skill>/
├── SKILL.md          # Requis — frontmatter YAML + instructions Markdown
├── scripts/          # Optionnel — scripts exécutables
├── references/       # Optionnel — documentation, knowledge files
└── resources/        # Optionnel — assets statiques, templates
`

> [!NOTE]
> Le standard MS utilise ssets/ là où mLoop utilise esources/. Ces deux noms sont sémantiquement équivalents et non-conflictuels. Lors d'une publication externe, renommer esources/ en ssets/ si la plateforme cible l'exige.

---

## Principe de Progressive Disclosure

Le mécanisme de **chargement progressif** est identique entre mLoop et le standard MS :

`
1. DÉCOUVERTE  →  L'agent ne voit que 
ame + description
                  (léger, ne charge pas le SKILL.md complet)

2. ACTIVATION  →  Si la tâche correspond, le SKILL.md complet est chargé
                  (instructions, contexte)

3. EXÉCUTION   →  Les sous-répertoires (scripts/, references/) sont lus
                  uniquement si nécessaires pour accomplir la tâche
`

Ce principe est aligné avec la **Confidence Gate** (python src/swarm.py confidence) : ne charger que le contexte strictement nécessaire.

---

## Audit de Conformité des Skills mLoop (2026-07-21)

| Skill | 
ame | description | Conforme standard | Extensions |
|-------|--------|---------------|-------------------|------------|
| nalyze | ✅ | ✅ enrichi | 🟢 **Conforme** | — |
| handoff | ✅ | ✅ | 🟢 **Conforme** | disable-model-invocation |
| plan | ✅ | ✅ enrichi | 🟢 **Conforme** | — |
| esearch | ✅ | ✅ | 🟢 **Conforme** | disable-model-invocation, rgument-hint |
| outer | ✅ | ✅ | 🟢 **Conforme** | disable-model-invocation |
| sop | ✅ | ✅ | 🟢 **Conforme** | disable-model-invocation |
| 	each | ✅ | ✅ | 🟢 **Conforme** | disable-model-invocation, rgument-hint |
| alidate | ✅ | ✅ enrichi | 🟢 **Conforme** | — |

**Score de conformité : 8/8 — 100%** 🏆

---

## Règles pour la Publication Externe

Si un skill mLoop doit être publié sur agentskills.io ou partagé avec une équipe utilisant MS Agent Framework :

1. **Vérifier** que 
ame et description sont présents et auto-descriptifs.
2. **Optionnel** : Ajouter un champ ersion: "1.0.0" dans le frontmatter.
3. **Renommer** esources/ en ssets/ si la plateforme cible l'exige.
4. **Retirer** les champs disable-model-invocation et rgument-hint (ignorés, mais plus clean).
5. **Documenter** les dépendances mLoop-spécifiques (ex: python src/swarm.py ...) dans une section ## Prerequisites du SKILL.md.

---

## Références

- [Microsoft Agent Skills Specification (mars 2026)](https://devblogs.microsoft.com/agent-framework/give-your-agents-domain-expertise-with-agent-skills-in-microsoft-agent-framework/)
- [Agent Skills for .NET — Release (juillet 2026)](https://devblogs.microsoft.com/agent-framework/agent-skills-for-net-is-now-released/)
- [agentskills.io — Registry communautaire](https://agentskills.io)
- Architecture mLoop : [architecture_mcp.md](./architecture_mcp.md)
