---
name: github-ops
description: Guide d'ingénierie et d'automatisation GitHub pour mLoop. Régit la validation pré-vol Vibe-Check, le cycle des Pull Requests (INVEST & EvidencePack), le diagnostic chirurgical des runs GitHub Actions (CI/CD) et la gestion des skills d'agents avec gh skill.
---

# 🐙 Skill : Ingénierie & Automatisation GitHub (`/github-ops`)

## Aperçu & Rôle Souverain
Ce skill régit les flux d'ingénierie de **Memory Loop (mLoop)** sur **GitHub** (`https://github.com/Marco-Lefrancois/memory-loop.git`). Il outille l'agent pour piloter l'écosystème GitHub à l'aide de deux leviers complémentaires :
1. **Le Serveur MCP GitHub** (`@modelcontextprotocol/server-github` configuré dans `.agents/mcp.json`).
2. **Le CLI GitHub (`gh`)** pour les commandes d'automatisation avancées (`gh pr`, `gh run`, `gh release`, `gh skill`).

Il garantit que tout merge, toute Pull Request et tout déploiement de version respectent le protocole de qualité mLoop (Vibe-Check 9 points, format de story INVEST, rapports EvidencePacks).

---

## Déclencheurs & Exclusions
- **Quand l'utiliser** :
  - Création, mise à jour ou audit d'une Pull Request mLoop sur GitHub.
  - Diagnostic d'échecs de workflows CI/CD GitHub Actions (tests unitaires `pytest`, lint `ruff`).
  - Recherche, installation, prévisualisation ou mise à jour de skills d'agents via la commande `gh skill`.
  - Gestion des releases, tags Git et synchronisation formelle de `CHANGELOG.md`.
- **Quand NE PAS l'utiliser** :
  - Pour les projets clients hébergés sur Azure DevOps (utiliser [`azure-devops-lifecycle`](../azure-devops-lifecycle/SKILL.md)).
  - Pour des modifications de code locales simples sans interaction avec GitHub.

---

## Déroulé Opérationnel par Module

### Module 1 : Pré-Vol Vibe-Check & Cycle de Pull Request

Avant de soumettre une Pull Request sur le dépôt `memory-loop` :

1. **Contrôle Pré-Vol Déterministe Obligatoire** :
   * Exécuter la suite complète de validation locale :
     ```bash
     python src/swarm.py vibe-check
     pytest tests/
     ruff check .
     ```
   * **Règle absolue** : Zéro création de PR si un test échoue ou si le Vibe-Check signale une régression.

2. **Création Standardisée de la PR (`gh pr create`)** :
   * Créer la branche thématique : `git checkout -b feature/<nom-fonctionnalite>` ou `fix/<nom-correctif>`.
   * Formater le corps de la PR selon le gabarit mLoop :
     ```markdown
     ## 🎯 Objectif & Scope
     [Description succincte du problème résolu et des modules mLoop impactés]

     ## 🏛️ Décisions d'Architecture (ADRs)
     - ADR impliqué : [Ex: ADR-0327 - URLs Canoniques Azure DevOps]

     ## 🧪 Dossier de Preuves (EvidencePack) & Tests
     - [x] Contrôles Vibe-Check réussis (9/9)
     - [x] Tests unitaires : `pytest tests/` validé sans erreur
     - [x] Linting : `ruff check` propre

     ## 📋 Checklist de Révision
     - [x] Pas de régression de schéma dans loop_mem
     - [x] Documentation et CHANGELOG.md synchronisés
     ```
   * Commande CLI :
     ```bash
     gh pr create --title "[Scope] Intitulé clair de la PR" --body-file pr_description.md
     ```

---

### Module 2 : Diagnostic Chirurgical des Workflows GitHub Actions

Lorsqu'un workflow GitHub Actions échoue sur une branche ou une PR :

1. **Identification du Run en Échec** :
   * Lister les derniers runs :
     ```bash
     gh run list --limit 5
     ```
   * Ou utiliser l'outil MCP GitHub `list_workflow_runs`.

2. **Extraction Ciblée des Logs d'Erreurs (Anti-Saturation)** :
   * **Interdiction formelle** de déverser l'intégralité du log brut dans la conversation.
   * Utiliser la commande d'extraction des seules lignes d'échec :
     ```bash
     gh run view <run_id> --log-failed
     ```
   * Ou via MCP avec `summarize_job_log_failures`.
3. **Reproduction & Correction Locale** :
   * Reproduire l'échec exactement dans l'environnement local (`pytest tests/test_cible.py -k test_failing`).
   * Valider la correction avant de pousser un commit correctif.

---

### Module 3 : Gestion des Skills d'Agent avec `gh skill`

Conformément à la documentation officielle de GitHub Copilot et la spécification [agentskills.io](https://agentskills.io/specification), le CLI GitHub (`gh` v2.90.0+) permet de gérer les skills :

1. **Recherche de Skills** :
   ```bash
   gh skill search <terme-cle>
   ```
2. **Prévisualisation Sans Installation (Inspection Sécurité)** :
   * Inspecter systématiquement le code et le `SKILL.md` pour prévenir toute injection de prompt :
     ```bash
     gh skill preview <owner>/<repo> <skill-name>
     ```
3. **Installation dans mLoop** :
   * Installer au niveau du projet dans `.agents/skills/` :
     ```bash
     gh skill install <owner>/<repo> <skill-name>
     ```
   * Pour figer une version immuable :
     ```bash
     gh skill install <owner>/<repo> <skill-name> --pin <vX.Y.Z>
     ```
4. **Mise à Jour des Skills** :
   ```bash
   gh skill update --all
   ```

---

### Module 4 : Releases & Synchronisation CHANGELOG.md

Lors de la finalisation d'un incrément versionné de mLoop :
1. **Mise à Jour de `CHANGELOG.md`** :
   * Consigner les ajouts sous la section correspondante (`[Unreleased]` ou `[X.Y.Z]`) selon la norme Keep a Changelog.
2. **Tagging Git & Création de la Release GitHub** :
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z : [Résumé des nouveautés]"
   git push origin vX.Y.Z
   gh release create vX.Y.Z --title "vX.Y.Z" --notes-file release_notes.md
   ```

---

## Table Anti-Rationalisation (Inviolable)

| Excuse de l'Agent (Paresse) | Réalité & Règle Inviolable |
| :--- | :--- |
| *"La PR est petite, pas besoin d'exécuter vibe-check ou pytest avant de soumettre."* | Toute PR non vérifiée localement risque de casser la CI publique. Le pré-vol local est obligatoire. |
| *"Je colle l'intégralité des 5 000 lignes du log GitHub Actions pour voir où ça plante."* | Sature la fenêtre de contexte de l'agent. Utiliser `gh run view --log-failed` ou l'analyse ciblée MCP. |
| *"J'installe un skill tiers trouvé sur Internet sans regarder son contenu."* | Risque majeur de prompt injection ou d'exécution de script malveillant. Toujours lancer `gh skill preview` d'abord. |
| *"J'ai mergé la PR, je mettrai le CHANGELOG.md à jour plus tard."* | La dette documentaire mène à la perte de traçabilité. CHANGELOG.md doit être mis à jour dans la PR elle-même. |
