# ADR-0377 : Sonde & Gouvernance Déterministe des Runtimes d'Agents Aval (Inspiration AgentManager & Universal Dev Handoff)

* **Statut** : ACCEPTÉ
* **Date** : 18 septembre 2026
* **Décideurs** : Architecte en Chef, Équipe Core mLoop, Product Owner
* **Domaine** : Runtimes d'agents, diagnostic d'environnement, Universal Dev Handoff, pré-vol Vibe-Check

---

## 🚀 1. Contexte & Problématique

Dans l'architecture de Memory Loop (mLoop), la séparation des responsabilités est stricte :
- **mLoop** agit comme Cerveau d'État et Fournisseur Universel de Spécifications (*Universal Dev Handoff*).
- L'exécution physique du code client (Phase 3 `BUILD & DEV`) et les tâches de calcul lourd sont déléguées à des agents externes spécialisés : `herdr` (isolation PTY out-of-process - ADR-0346), `opencode`, `claude-code`, `aider`, ou `cursor-cli`.

Cependant, l'environnement local du développeur est sujet au *Runtime Drift* :
1. **Absence ou obsolescence d'un binaire clé** (ex: `herdr` absent lors d'une tentative de `worker-spawn`, bloquant l'isolation).
2. **Échecs silencieux ou blocages interactifs** : invoquer un agent non configuré ou suspendu peut bloquer le processus s'il n'y a pas de timeout strict.
3. **Dépendance externe inutile** : des outils tiers comme AgentManager (`agentmgr` en Go) proposent un catalogue de 109 agents, mais introduisent une dépendance binaire lourde et superflue sur l'hôte.

---

## 💡 2. Décisions d'Architecture

### A. Rapatriement Souverain du Pattern "Catalogue Déclaratif" en Python Pur
Plutôt que d'installer un binaire Go externe, mLoop implémente un module natif `src/core/agent_probe.py` s'inspirant des meilleures pratiques d'AgentManager :
- Un dictionnaire typé `AGENT_CATALOG` recensant le noyau dur des agents supportés par le Dev Handoff (`herdr`, `opencode`, `claude-code`, `aider`, `cursor-cli`).
- Chaque entrée définit : binaire exécutable, argument de version, version minimale requise, rôle architectural et caractère critique selon la phase du cycle.
- **100% Hors-Ligne & Souverain** : Aucune requête distante vers des registres de paquets (npm, PyPI, GitHub). Tout le diagnostic est local et immédiat (< 50 ms).

### B. Conformité Stricte aux Standards Python Senior (ADR-0369)
La sonde respecte impérativement :
1. **Typage structurel** via `typing.Protocol` (`AgentProbeProtocol`).
2. **Deadlines d'exécution inviolables** : `subprocess.run(..., timeout=2.0)` avec capture sécurisée `stdout`/`stderr`.
3. **Observabilité contextuelle** : journalisation structurée via `extra={...}` et capture explicite de `subprocess.TimeoutExpired` et `FileNotFoundError`.

### C. Le 16ᵉ Contrôle du Vibe-Check (Pré-Vol Inviolable)
Le pipeline de pré-vol `vibe-check` (`src/pipelines/vibe_check.py`) intègre un 16ᵉ contrôle déterministe :
- En phase `STAGE_1_INGEST` / `STAGE_SPEC` : informatif.
- En phase `RUN` (dès `STAGE_PLAN_GRILL`) : la présence de `herdr` est vérifiée (avertissement si absent).
- En phase `STAGE_BUILD` : la présence d'au moins un agent de dev aval (`opencode`, `claude-code` ou `aider`) devient obligatoire pour garantir l'opérabilité du *Dev Handoff*.

### D. Interface Dédiée `doctor --agents` et Commande Canonique `agent-probe`
- `python src/swarm.py doctor --agents` : Diagnostic formaté sous forme de tableau propre avec indicateurs (● Disponible, ⬆ Version obsolète, ○ Absent).
- `python src/swarm.py agent-probe` : Commande alias canonique dédiée.
- Parité SSOT garantie par `python src/swarm.py guide --sync` (ADR-0370).

---

## ⚖️ 3. Conséquences

### Positives
* **Zéro Dépendance Externe** : Aucun binaire Go ou runtime supplémentaire requis sur Windows/Linux/macOS.
* **Sécurisation du Dev Handoff** : Détection précoce des problèmes d'outillage avant d'entamer les phases d'implémentation.
* **Rapidité Maximale** : Diagnostic local instantané ne pénalisant pas la boucle de démarrage.

### Négatives & Mitigations
* **Catalogue maintenu en interne** : Limité aux 5 agents majeurs de l'écosystème mLoop, évitant l'effet de bloat d'un catalogue de 109 entrées.
