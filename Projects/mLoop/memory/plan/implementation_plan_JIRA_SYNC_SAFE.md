# Plan d'implémentation — Sécurisation de la commande jira_sync

*Statut*: **Approuvé**
*Date*: 20 août 2026

## 1. Problème à éliminer
La commande `jira_sync --project <projet>` synchronise implicitement tous les récits éligibles. Elle ne permet pas de cibler, de prévisualiser, ni de confirmer l'étendue des modifications avant l'appel à l'API distante. Cela génère des mises à jour non désirées (ex. la synchronisation globale intervenue au lieu de COUVBOIRE-957 seul).

---

## 2. Nouveau comportement CLI requis (`src/swarm.py jira_sync`)

### A. Ciblage par défaut
L'appel de base **ne doit plus rien synchroniser** vers Jira. Il doit générer une erreur explicite invitant à utiliser le ciblage ou le flag administratif.
- `--story <CLE_JIRA>` ou `--stories <CLE1>,<CLE2>` : Cible explicitement des tickets.

### B. Dry-run obligatoire (Prévisualisation)
Toute intention de synchronisation génère d'abord un aperçu local (`dry-run`), sauf si le flag d'application est fourni.
- Le système refuse les clés `TEMP-*` et les statuts `OPEN` ou `IN_ANALYZE`.
- Pour déroger et synchroniser un récit `IN_ANALYZE` (ex. pour provisionner la coquille), utiliser un flag `--allow-in-analyze`.

### C. Verrou de confirmation (Write)
Pour écrire effectivement sur Jira :
- `--apply` **ET** `--confirm-scope <CLE_JIRA>`
- La liste fournie à `confirm-scope` doit être *exactement identique* aux tickets qui ont passé l'éligibilité. Si une erreur d'éligibilité survient, la commande refuse l'écriture pour tout le monde (Fail-Closed).

### D. Mode Global Administratif (Déprécié pour l'usage courant)
L'ancienne synchronisation globale est verrouillée :
- Requiert `--all` **ET** `--apply` **ET** `--confirm-all-project-stories`
- Ce mode doit être utilisé avec parcimonie.

---

## 3. Mécanisme de Manifeste

Le framework (par exemple `src/pipelines/jira_adapter.py`) doit enregistrer un fichier de manifeste temporaire avant l'appel API final (`memory/sync/jira_sync_preview.json`). Ce manifeste sert à comparer les SHA256 des fichiers pour s'assurer qu'aucune modification locale n'est survenue entre le dry-run et l'apply.

---

## 4. Tests d'acceptation (QA Backend Framework)

L'équipe mLoop devra s'assurer que :
1. L'omission des paramètres de ciblage ou l'omission de `--apply`/`--confirm-scope` empêche formellement tout trafic HTTP vers Jira.
2. Un ticket en statut local `IN_ANALYZE` est rejeté avec un code d'erreur, sauf option explicite.
3. Les rapports de synchronisation (`jira_sync_report.md`) n'incluent plus les "IGNORE" de sous-tâches, mais se concentrent uniquement sur l'audit du ticket ciblé.
4. L'EvidencePack du récit synchronisé consigne l'opération avec l'identifiant du Manifeste.

---

## 5. Livrables de l'équipe de Build
1. Mise à jour de `src/swarm.py` (CLI parser).
2. Mise à jour de la classe gérant `jira_sync`.
3. Mise à jour de ce guide opérationnel (AGENTS/Skills) pour informer les assistants de cette nouvelle règle de sécurité.