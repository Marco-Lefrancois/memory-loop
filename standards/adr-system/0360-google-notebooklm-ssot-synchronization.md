# ADR-0360 : Synchronisation & Export SSOT vers Google NotebookLM

> **Statut :** DÉPRÉCIÉ / RETIRÉ  
> **Date Initiale :** 2026-09-08  
> **Date de Retrait :** 2026-09-24  
> **Contexte :** Ancienne liaison avec Google NotebookLM (Retirée du framework à la demande de l'équipe car non utilisée)  
> **Décision de Retrait :** Les commandes `notebooklm`, handlers, pipelines d'exportation et scripts d'authentification associés ont été intégralement retirés du projet mLoop.

---

## 1. Contexte & Problématique

Memory Loop possède une architecture pure-state rigoureuse (Graphify, SQLite FTS5, 64+ ADRs, 58 commandes CLI). Cependant, la restitution synthétique et l'interrogation par grand modèle de langage sans hallucination bénéficient grandement d'un ancrage direct dans Google NotebookLM (Gemini 2.5 RAG).
Le carnet officiel dédié est configurable via la variable d'environnement `NOTEBOOKLM_NOTEBOOK_URL` (défaut : `https://notebooklm.google.com`).

Jusqu'alors, aucun protocole déterministe ne permettait de compiler la documentation vivante de mLoop en artefacts prêts pour l'import dans ce carnet.

---

## 2. Décisions d'Architecture

1. **Enregistrement Paramétrable du Carnet mLoop** :
   Le carnet est identifié sous la variable `NOTEBOOKLM_NOTEBOOK_ID` (défaut : `mloop-ssot`) dans la configuration d'environnement.

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
 
- Statut : **RETIRÉ / OBSOLÈTE (2026-09-24)**.
- Supprimé de `src/commands/_registry/_reg_project.py` et du guide CLI.
- Code et pipelines supprimés (`src/commands/handlers/notebooklm.py`, `src/pipelines/notebooklm_export.py`, `tools/notebooklm/`).
