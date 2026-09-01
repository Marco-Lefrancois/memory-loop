# 🎣 Manuel des Dynamic Hooks & Événements Kernel (v2.0.0)

Dans l'architecture mLoop v2.0.0, le pilier "Self-Healing" monolithique est géré par un système réactif et décentralisé : les **Dynamic Hooks** et le **mLoop Event Bus** au sein du Kernel (`src/swarm.py`).

---

## 1. Comment fonctionnent les Hooks ?

Un Hook est une déclaration ou un automate au niveau du Kernel (`src/swarm.py` ou `.agents/hooks/`). Il écoute l'Event Bus et s'active automatiquement lors d'événements clés (transition de phase, modification de story, génération d'évidence, échec d'auto-étalonnage).

## 2. Hooks Natifs du Framework

### A. Auto-Audit & Evidence Enforcement
* **Événement Déclencheur** : Modification ou passage en phase PLAN / VALIDATE d'un récit (`backlog/stories/US-XXX.md`).
* **Action du Hook** : Invoque synchrone l'**EvidencePackEngine** (`evidence.py`).
* **Résultat** : Génère/met à jour l'artefact JSON `memory/evidence/<STORY_ID>_evidence.json` avec la section `## 📑 Notes de Traçabilité & Références (IA Only)`.

### B. Moteur Calibrate Engine (Auto-Repair)
* **Événement Déclencheur** : Invocations CLI `python src/swarm.py calibrate --project <nom_projet>`.
* **Action du Hook** : Vérification des 8 composants système (CLI, shortcuts, MCP, skills, directives, blueprints, SQLite/Graphify, registres SHA256).
* **Résultat** : Auto-réparation à 100% des anomalies détectées (8/8 PASS).

### C. Synapse Compression & Focus Lock
* **Événement Déclencheur** : Invalidation de contexte ou appel de `python src/swarm.py focus`.
* **Action du Hook** : Nettoyage et verrouillage du contexte actif sur la story visée, avec préchargement d'engrammes en RAM Cache (`loop_mem_preload_context`).

## 3. Créer un Custom Hook

Pour créer un Hook métier (ex: linter de conformité d'API ou audit de sécurité) :
1. Créez un fichier `.agents/hooks/custom_audit.yaml`.
2. Définissez l'événement d'écoute (ex: `on: PHASE_VALIDATE_START`).
3. Définissez la commande déterministe à exécuter (ex: `run: python src/swarm.py wikifix --project <p>`).
