# ADR-0360 : Synchronisation & Export SSOT vers Google NotebookLM

> **Statut :** Accepté  
> **Date :** 2026-09-08  
> **Contexte :** Liaison bidirectionnelle entre l'Orchestrateur mLoop et le carnet Google NotebookLM officiel  

---

## 1. Contexte & Problématique

Memory Loop possède une architecture pure-state rigoureuse (Graphify, SQLite FTS5, 64+ ADRs, 58 commandes CLI). Cependant, la restitution synthétique et l'interrogation par grand modèle de langage sans hallucination bénéficient grandement d'un ancrage direct dans Google NotebookLM (Gemini 2.5 RAG).
Le carnet officiel dédié a été instancié :
`https://notebook.google.com/notebook/ddf80a44-cf1c-4eb8-86fd-7cebe6156f87`

Jusqu'alors, aucun protocole déterministe ne permettait de compiler la documentation vivante de mLoop en artefacts prêts pour l'import dans ce carnet.

---

## 2. Décisions d'Architecture

1. **Enregistrement Officiel du Carnet mLoop** :
   Le carnet `https://notebook.google.com/notebook/ddf80a44-cf1c-4eb8-86fd-7cebe6156f87` est identifié comme `memory-loop-ssot` dans la bibliothèque MCP globale.

2. **Pipeline d'Exportation Déterministe (`src/pipelines/notebooklm_export.py`)** :
   Création d'un pipeline générant des artefacts Markdown normalisés sous `storage/notebooklm_export/` :
   - `01_mLoop_Constitution_AGENTS.md` : Constitution et gouvernance multi-agents.
   - `02_mLoop_CLI_Pipeline_Guide.md` : Guide exhaustif des 58 commandes CLI.
   - `03_mLoop_ADR_Master_Catalog.md` : Catalogue consolidé de l'ensemble des ADRs.
   - `mloop_complete_ssot_bundle.md` : Master bundle unique consolidé permettant une synchronisation en un glisser-déposer dans NotebookLM.

3. **Commande CLI Native (`python src/swarm.py notebooklm`)** :
   Intégration dans le registre déclaratif `src/commands/_registry.py` avec options :
   - `--bundle` : Génération des bundles documentaires.
   - `--status` : Diagnostic de session et métadonnées du carnet.
   - `--auth` : Passerelle Chrome via `login_notebooklm.mjs`.

4. **Passerelle d'Authentification Dédiée (`login_notebooklm.mjs`)** :
   Script interactif à la racine utilisant `notebooklm-mcp/dist/auth/auth-manager.js` pour renouveler le profil persistant Chrome.

---

## 3. Justification & Alignement

- Élimine tout risque de désynchronisation entre le code source mLoop et le carnet NotebookLM.
- Permet à l'utilisateur de maintenir son carnet à jour en exécutant simplement `python src/swarm.py notebooklm --bundle`.

---

## 4. Statut & Suivi

- Implémenté dans `src/commands/handlers/notebooklm.py` et `src/pipelines/notebooklm_export.py`.
- Enregistré dans `src/commands/_registry.py`.
- Carnet validé et actif sous l'ID `memory-loop-ssot`.
