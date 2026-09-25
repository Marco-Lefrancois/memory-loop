---
id: MLOOP-191-BE
jira_key: ''
epic_key: EPIC-19-CLICK-CLI-ENGINE
type: Feature
title: Routeur de Commandes Dynamique Lazy-Loading (click.MultiCommand)
origin: DIRECT_REQUIREMENT
source_ref: epic_click_cli_engine.md
macro_size: L
status: DONE
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-190-BE
created_at: '2026-09-23'
ttl_cycles: 2
---

# 📖 MLOOP-191-BE : Routeur de Commandes Dynamique Lazy-Loading (click.MultiCommand)

## 1. Intention Métier (User Story)
**En tant qu'** Ingénieur du framework mLoop,  
**je veux** un routeur Click sous-classant `click.MultiCommand` capable de charger les handlers à la volée avec une passerelle de rétrocompatibilité `ArgsShim`,  
**afin de** supprimer la latence de démarrage liée à l'instanciation des 58 sous-parseurs et exécuter les commandes sans aucune modification de code dans les 58 handlers existants.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : [`epic_click_cli_engine.md`](../epics/epic_click_cli_engine.md) (Réf : Performance au boot et découplage modulaire)
- **Références d'Architecture** : ADR-0202 (Modularité < 300L), ADR-0369 (Standards Python Senior), ADR-0370 (Résilience Registre CLI)
- **Enveloppe Macro Estimée** : L (2 à 3 jours)

---

## 3. Périmètre Sommaire

### In-Scope (Macro)
- Création de `src/cli/click_engine/router.py` (≤ 300 lignes, conforme `RULE-AST-01`).
- Classe `MLoopMultiCommand(click.MultiCommand)` :
  - `list_commands(ctx)` : liste les identifiants et alias de commandes déclarés sans importer les modules lourds.
  - `get_command(ctx, cmd_name)` : résout paresseusement le module et la définition de la commande ciblée.
- Classe adaptatrice `ArgsShim(argparse.Namespace)` :
  - Reçoit les options et arguments Click et les présente sous forme d'attributs `args.nom_argument`.
  - Assure que les signatures historiques `handler(args, state, project_path)` fonctionnent immédiatement sans altération.
- Point d'entrée unifié dans `src/swarm.py` :
  - Délégation vers l'instance racine `cli()` de Click.
  - Préservation du code d'interception d'erreur globale (trace `mloop.log` et capture unhandled exceptions).

### Out-of-Scope (Macro)
- Définition de l'aide hiérarchique par phase (couvert par MLOOP-193-BE).
- Complétion dynamique de projet (couvert par MLOOP-192-BE).
- Réécriture native des 58 handlers avec des décorateurs `@click.command` (Lot 2 incrémental).

---

## 4. Contexte Métier & Architecture

L'architecture actuelle `src/commands/router.py` exécute :
```python
for cmd_name, cmd_def in sorted(cmds.items()):
    sub = subparsers.add_parser(cmd_name, ...)
    for arg_def in cmd_def.get("args", []):
        sub.add_argument(...)
```
Cette boucle itère sur 58 blocs et 180+ définitions d'arguments avant même de savoir quelle commande l'utilisateur souhaite exécuter.

Avec `click.MultiCommand` :
1. Click analyse le premier token de la ligne de commande (`sys.argv[1]`).
2. Seul le descripteur de cette commande est chargé en mémoire via `get_command()`.
3. Le temps de démarrage passe de ~250ms à ~40ms, un gain déterminant pour les orchestrateurs agentiques.

---

## Critères d'Acceptation

- [ ] **CA-1** : `MLoopMultiCommand.list_commands()` liste exhaustivement les 58 commandes répertoriées ainsi que leurs alias officiels.
- [ ] **CA-2** : `MLoopMultiCommand.get_command()` n'importe que le module correspondant au handler de la commande demandée (lazy import prouvé par test).
- [ ] **CA-3** : L'adaptateur `ArgsShim` convertit fidèlement tous les paramètres Click (flags booléens, entiers, chaînes, listes) en attributs compatibles `argparse.Namespace`.
- [ ] **CA-4** : Tous les handlers existants invoqués via `ArgsShim` reçoivent le triplet attendu `(args, state, project_path)` et s'exécutent avec succès.
- [ ] **CA-5** : Le temps d'exécution mesuré sur une commande minimale (`loop lifecycle-status --project mLoop` ou `loop --help`) est divisé par au moins 2 par rapport à la baseline `argparse`.
- [ ] **CA-6** : `src/cli/click_engine/router.py` ne dépasse pas 300 lignes (conforme `RULE-AST-01`).

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : ce récit est un composant interne du routeur CLI mLoop — **aucune route API HTTP n'est consommée ni exposée**.

---

## 5. Piliers Gherkin

### Pilier 1 : Nominal
```gherkin
Scénario: Invocation paresseuse d'une commande unitaire
  Étant donné une commande comme "vibe-check"
  Quand l'utilisateur lance "python src/swarm.py vibe-check --project mLoop"
  Alors MLoopMultiCommand charge uniquement le sous-système vibe_check
  Et aucun module lié aux 57 autres commandes n'est importé
  Et le handler s'exécute nominalement
```

### Pilier 2 : Exceptions
```gherkin
Scénario: Commande inconnue ou invalide
  Étant donné une frappe erronée "python src/swarm.py commande-inexistante"
  Quand le routeur Click parse la commande
  Alors un message d'erreur indique que la commande est inconnue
  Et Click suggère la commande la plus proche si pertinent (did-you-mean)
  Et le programme sort avec l'exit code 2
```

### Pilier 3 : Résilience & Mode Dégradé
```gherkin
Scénario: Résolution d'alias de commande
  Étant donné une commande disposant d'un alias officiel
  Quand l'utilisateur invoque la commande via son alias
  Alors get_command() résout l'alias vers le handler canonique
  Et l'exécution se déroule à l'identique de la commande principale
```

### Pilier 4 : UX (Retour Utilisateur / Observabilité)
```gherkin
Scénario: Interruption clavier propre (Ctrl+C)
  Étant donné une commande en cours d'exécution
  Quand l'utilisateur interrompt le processus avec Ctrl+C (SIGINT)
  Alors le routeur intercepte KeyboardInterrupt proprement
  Et un message d'information sobre est affiché sans stacktrace
  Et le code de sortie est 130
```
