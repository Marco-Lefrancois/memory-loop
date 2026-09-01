# 🚑 Guide de Dépannage, Auto-Repair & HITL (Stop & Ask)

Même dans un framework autonome et déterministe (mLoop v2.0.0), les agents peuvent rencontrer des impasses logiques, des erreurs d'environnement ou des ambiguïtés d'affaires. Voici comment auditer, auto-réparer et débloquer l'écosystème.

---

## 1. Moteur d'Auto-Calibrage (`python src/swarm.py calibrate`)

Avant toute investigation manuelle, lancez le moteur d'auto-étalonnage continu :
```bash
python src/swarm.py calibrate --project <nom_projet>
```
Le moteur teste les 8 composants système (CLI, MCP, Skills, AGENTS/GEMINI, blueprints, SQLite/Graphify, registres SHA256 et guardrails) et exécute un **Auto-Repair automatique** en cas d'écart.

## 2. Restauration d'État Anti-Amnésie
Si une session a été interrompue ou si l'agent semble avoir perdu son contexte :
```bash
python src/swarm.py resume --project <nom_projet>
python src/swarm.py focus --project <nom_projet> --story backlog/stories/US-XXX.md
```

## 3. Le Protocole "Stop & Ask" (Human-In-The-Loop)

Lorsqu'une ambiguïté d'affaires majeure est détectée ou qu'une décision d'architecture irréversible nécessite la validation humaine, le harnais déclenche la porte de confirmation (HITL strict).

### Comment ça se manifeste ?
1. Le terminal affiche : `[HITL REQUIRED] Ambiguïté d'affaires sur US-XXX. Veuillez trancher.`
2. Une Question Ouverte (`Q-` ou `QD-`) est consignée dans l'artefact d'évidence `memory/evidence/<STORY_ID>_evidence.json` et dans `docs/04-transverse/00-questions-ouvertes.md`.

### Comment débloquer ?
1. Ouvrez le récit (ex: `backlog/stories/US-XXX.md`) ou le registre `00-questions-ouvertes.md`.
2. Tranchez la question directement en répondant au message ou en consignant la décision dans `CONTEXT.md` / `business.md`.
3. Relancez la commande CLI appropriée (ex: `python src/swarm.py grill` ou `python src/swarm.py graph-run`). L'agent cristallisera la décision et poursuivra le workflow.

## 4. Réinitialisation de Phase & Reset de Story
Si une story a besoin d'être réévaluée ou révisée à partir d'une phase antérieure :
1. Modifiez le frontmatter YAML de la story : `status: DRAFT` ou `phase: PLAN`.
2. Conservez les artefacts `memory/evidence/` pour la traçabilité.
3. Exécutez `python src/swarm.py sync --project <nom_projet>` pour synchroniser le graphe.
