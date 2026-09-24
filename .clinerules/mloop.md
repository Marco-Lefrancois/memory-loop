# 🛡️ Directives Constitutionnelles mLoop pour Cline

> Ce fichier est généré automatiquement par `mloop sync`. Ne pas modifier manuellement.
> Réf : ADR-0376 (Rigueur 360° Zéro Blindspot) · ADR-0202 (Plafond 300L) · ADR-0375 (5 Phases).

## 1. Interdiction Absolue de Saut de Phase (ADR-0339 / ADR-0375)
- En **Phase 2 (PLAN & ANALYSE)**, l'agent doit impérativement opérer en mode `--plan`.
- Il est **strictement interdit** d'écrire ou de modifier du code source avant que la story ne soit validée au statut `READY_FOR_DEV` (Grill-Me 1:1 complété, DoR 6/6).

## 2. Plafond Modulaire Strict <= 300 Lignes (ADR-0202)
- Aucun fichier source Python (`src/`, `tests/`) ne doit excéder **300 lignes effectives**.
- Tout composant qui dépasse cette limite doit être immédiatement découpé en sous-modules hautement cohésifs avec délégation explicite.

## 3. Préservation Intangible du Code & Zéro Régression
- Il est **formellement interdit de supprimer du code ou des tests existants** sous prétexte de simplification sans justification explicite et approbation.
- Conserver systématiquement les docstrings, annotations de types et gestion d'erreurs.

## 4. Rigueur d'Audit en 7 Couches (ADR-0376)
Toute évolution touchant le cœur de mLoop doit inspecter et maintenir la cohérence de :
1. Blueprints (`standards/blueprints/`)
2. Protocoles (`standards/protocols/`)
3. ADR System (`standards/adr-system/`)
4. Directives Agents (`.agents/agents/`)
5. Skills Portables (`.agents/skills/`)
6. Moteur Core Python (`src/core/`, `src/bridges/`, `src/commands/`)
7. Suites de Tests & Guides CLI (`tests/`, `CLI_PIPELINE_GUIDE.md`)

## 5. Commandes de Validation Déterministes
Après toute modification, exécuter impérativement :
```powershell
pytest tests/ -v
python src/swarm.py vibe-check --project mLoop
```
