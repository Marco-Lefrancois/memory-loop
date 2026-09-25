---
id: MLOOP-194-BE
jira_key: ''
epic_key: EPIC-19-CLICK-CLI-ENGINE
type: Feature
title: Harnais de Test In-Process CliRunner & Validation Non-Régression
origin: DIRECT_REQUIREMENT
source_ref: epic_click_cli_engine.md
macro_size: M
status: DONE
grill_me: DONE
invest_score: 6/6
layer: backend
blocked_by:
- MLOOP-190-BE
- MLOOP-191-BE
created_at: '2026-09-23'
ttl_cycles: 2
---

# 📖 MLOOP-194-BE : Harnais de Test In-Process CliRunner & Validation Non-Régression

## 1. Intention Métier (User Story)
**En tant que** Responsable QA et Ingénieur de test du framework mLoop,  
**je veux** une suite complète de tests unitaires et d'intégration in-process exploitant `click.testing.CliRunner`,  
**afin de** valider le bon fonctionnement et la non-régression absolue des 58 commandes mLoop sans avoir à lancer de sous-processus système lents et fragiles.

---

## 2. Origine & Cadrage Avant-Projet
- **Document Source** : [`epic_click_cli_engine.md`](../epics/epic_click_cli_engine.md) (Réf : Accélération de la suite de tests CLI)
- **Références d'Architecture** : ADR-0202 (Modularité < 300L), ADR-0369 (Standards Python Senior)
- **Enveloppe Macro Estimée** : M (1 à 2 jours)

---

## 3. Périmètre Sommaire

### In-Scope (Macro)
- Création de la suite de tests `tests/test_click_cli_engine.py` (≤ 300 lignes par module de test).
- Tests in-process avec `click.testing.CliRunner` :
  - Validation du chargement paresseux (`MLoopMultiCommand`).
  - Validation du passage de contexte (`MLoopContext`) et de l'injection d'état.
  - Validation de l'interception des Lifecycle Gates (bloquant sur phase invalide, passant sur phase valide).
  - Validation du comportement nominal des commandes vitales du framework (`vibe-check`, `gate-approve`, `sync`, `crawl`, `lifecycle-status`).
  - Validation des codes de sortie déterministes (0 pour succès, 1 pour violation métier/gate, 2 pour erreur de syntaxe/parsing, 130 pour SIGINT).
- Benchmark automatisé comparant le temps d'exécution in-process vs sous-processus legacy.

### Out-of-Scope (Macro)
- Tests des implémentations internes spécifiques de chaque outil métier externe (Playwright, MarkItDown, Git, Jira).
- Modification de la suite de tests existante dans `tests/test_e2e_*.py`.

---

## 4. Contexte Métier & Architecture

Historiquement, les tests d'intégration du CLI mLoop recouraient à `subprocess.run([sys.executable, "src/swarm.py", ...])`. Ces tests présentaient plusieurs inconvénients :
1. **Lenteur** : Chaque invocation recrée un interpréteur Python, initialise les modules et coûte entre 300ms et 800ms.
2. **Difficulté de mocking** : Impossible de mocker directement des objets en mémoire sans passer par des variables d'environnement ou des fichiers temporaires.
3. **Fragilité inter-plateformes** : Comportements asynchrones ou gestion des flux stdin/stdout sous Windows PowerShell vs Linux.

L'utilisation de `click.testing.CliRunner` permet d'exécuter la commande dans le même processus, en mémoire :
```python
from click.testing import CliRunner
from src.cli.click_engine.router import cli

def test_vibe_check_passes():
    runner = CliRunner()
    result = runner.invoke(cli, ["vibe-check", "--project", "mLoop"])
    assert result.exit_code == 0
    assert "Vibe-Check PASS" in result.output
```
Le test s'exécute en moins de 15 millisecondes avec isolation complète des flux et assertion directe sur les objets Python.

---

## Critères d'Acceptation

- [ ] **CA-1** : La suite de tests `tests/test_click_cli_engine.py` s'exécute intégralement sans recours à `subprocess.run()`.
- [ ] **CA-2** : Les 6 commandes vitales (`vibe-check`, `gate-approve`, `sync`, `crawl`, `lifecycle-status`, `worker-spawn`) sont couvertes avec assertions sur les codes de sortie.
- [ ] **CA-3** : Les tests d'interception de Lifecycle Gate prouvent l'arrêt immédiat avec code de sortie `1` en cas d'interdiction de commande.
- [ ] **CA-4** : L'adaptateur `ArgsShim` est testé unitairement pour vérifier la conformité des types transmis aux anciens handlers.
- [ ] **CA-5** : L'ensemble des tests du fichier s'exécute en moins de 2.0 secondes au total.
- [ ] **CA-6** : Le fichier de test respecte le plafond de 300 lignes (conforme `RULE-AST-01`).

### Matrice des Contrats API
> **Exemption déclarée (ADR-0319)** : ce récit est un composant de test interne — **aucune route API HTTP n'est consommée ni exposée**.

---

## 5. Piliers Gherkin

### Pilier 1 : Nominal
```gherkin
Scénario: Exécution in-process d'une commande vitale via CliRunner
  Étant donné une instance de CliRunner
  Quand runner.invoke(cli, ["lifecycle-status", "--project", "mLoop"]) est exécuté
  Alors result.exit_code est égal à 0
  Et result.output contient le statut de la phase active
```

### Pilier 2 : Exceptions
```gherkin
Scénario: Échec de validation d'argument capturé in-process
  Étant donné un paramètre obligatoire manquant
  Quand runner.invoke(cli, ["vibe-check"]) est exécuté sans projet
  Alors result.exit_code est égal à 1
  Et result.output mentionne explicitement que "--project" est requis
```

### Pilier 3 : Résilience & Mode Dégradé
```gherkin
Scénario: Capture d'exception inattendue dans un handler
  Étant donné un handler simulant une exception runtime imprévue
  Quand runner.invoke(cli, ["commande-simulee"]) est exécuté
  Alors result.exit_code est égal à 1
  Et un log d'erreur structuré est enregistré
  Et le processus de test ne plante pas
```

### Pilier 4 : UX (Retour Utilisateur / Observabilité)
```gherkin
Scénario: Séparation propre des flux stdout et stderr dans Result
  Étant donné une commande émettant des warnings sur stderr et du contenu sur stdout
  Quand CliRunner l'exécute
  Alors les flux sont capturés fidèlement dans result.output
  Et les codes d'échappement ANSI sont gérés de manière prédictible
```
