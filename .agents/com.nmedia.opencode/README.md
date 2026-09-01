# com.nmedia.opencode — Extension Namespace

Ce dossier est un **namespace d'extension** au sens de la spécification Agent Plugins 1.0.
Il contient les configurations et métadonnées spécifiques au client OpenCode de nMedia
qui ne font pas partie du contrat portable standardisé.

## Contenu

| Fichier | Description |
|:--------|:------------|
| `agents.json` | Définitions des 4 agents mLoop (orchestrator, plan, build, sentinel) |
| `commands.json` | Catalogue des 28+ commandes CLI `python src/swarm.py` |

## Règle de Portabilité

Conformément à la spec Agent Plugins 1.0 :
> Les clients DOIVENT ignorer les namespaces qu'ils n'implémentent pas SANS valider ces valeurs.

Cela signifie que Cursor, VS Code, GitHub Copilot et autres clients compatibles AP 1.0
ignoreront silencieusement ce dossier tout en chargeant normalement les `skills/` et `mcp.json`.
