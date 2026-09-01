# ADR-0002 : Contextualisation Active & Adaptateurs Multi-IDE
## Statut : Accepté (Série 00xx - Fondations)

---

## 1. Contexte

Les assistants IA et environnements de développement se multiplient (Google Antigravity, OpenCode, Claude Code, VS Code). Afin d'éviter tout verrouillage technologique (*vendor lock-in*), mLoop doit exposer sa grammaire de manière 100% agnostique.

---

## 2. Décision

Nous adoptons le patron d'architecture **Contextualisation Active**. Le moteur Python est conservé pur et agnostique sous `src/`, tandis que des **Adaptateurs d'Intégration** périphériques traduisent la grammaire mLoop dans le format natif de chaque outil :

```
<workspace-root>/
├── standards/adr-system/  <-- Cœur Constitutionnel Immuable (ADRs)
├── src/                   <-- Moteur d'Exécution Agnostique (Python CLI)
├── AGENTS.md              <-- Manifeste d'Équipe Universel (Agnostique)
│
│   === ADAPTATEURS MULTI-IDE (DÉCOUPLÉS) ===
├── .agents/skills/...     <-- Adaptateur Antigravity (Google)
├── opencode.json          <-- Adaptateur OpenCode / AI SDK
├── CLAUDE.md              <-- Adaptateur Claude Code (Anthropic)
└── .vscode/tasks.json     <-- Adaptateur VS Code (Humains/IDE)
```

Le pipeline `python src/swarm.py calibrate` réaligne automatiquement et synchronise les 8 piliers de l'écosystème à partir de ces adaptateurs.

---

## 3. Conséquences

- **Agnosticisme Total** : Possibilité de basculer entre IDEs et assistants sans réécrire la logique mLoop.
- **Auto-Calibrage** : Prévention active du drift d'adaptateurs via `swarm.py calibrate`.
