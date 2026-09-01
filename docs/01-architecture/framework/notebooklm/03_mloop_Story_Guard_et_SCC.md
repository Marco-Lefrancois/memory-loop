# mLoop - 03. La Frontière Ultime : SCC, EvidencePacks & Story Guard

Dans le framework mLoop, la règle d'or est stricte : **aucune ligne de code physique n'est modifiée sans contrat et sans pack d'évidence.**

## SCC (Story Constraint Contract)
Le SCC est la matérialisation du périmètre de travail fonctionnel et technique. C'est un fichier Markdown (situé sous `backlog/stories/`) généré par l'agent `plan`. Il définit le périmètre exact et non-négociable des composants autorisés à la modification. Il comprend obligatoirement :
* Le contexte fonctionnel (Why).
* Les critères d'acceptation rédigés sous forme de scénarios de test Gherkin (**4 Piliers** : Nominal, Rejet/Exception, Mode Dégradé, UX/Observabilité).
* Les contraintes techniques (types, structures de données, exclusions).
* La checklist précise des tâches et fichiers physiques à modifier.

**Règle de Nommage (Zéro-ID Local dans le corps)** : Pour éviter le couplage éphémère, les identifiants locaux (`ST-001`, `REC-042`) doivent résider exclusivement dans le nom du fichier et dans son frontmatter YAML.

**Gouvernance Typage Jira (Story Only)** : Un récit local du backlog mLoop (`REC-XXX`, `US-XXX`) se traduit **toujours et exclusivement** par un ticket de type **Story** dans Jira Cloud (`jira_sync`). Il est strictement interdit d'apparier ou créer un récit sous forme de Sub-task ou de tâche simple dans Jira.

## Génération Automatique des EvidencePacks (Zero-Ask Evidence Enforcement)
Lors de toute création, scission, découpage vertical ou révision de récit, l'agent mLoop DOIT générer de manière 100% autonome et synchrone :
1. L'artefact JSON d'audit sous `memory/evidence/<STORY_ID>_evidence.json` via l'engine `EvidencePackEngine`. Cet artefact consigne les preuves, alertes (`[!NOTE]`, `[!TIP]`, `[!IMPORTANT]`, `[!WARNING]`, `[!CAUTION]`) et questions ouvertes (`Q-`, `QD-`).
2. La section obligatoire au bas du récit : `## 📑 Notes de Traçabilité & Références (IA Only)`.

## Le Garde-Fou Actif (Story Guard)
Le script `story_guard.py` est le verrou physique empêchant la dérive technique (Scope Creep) lors des phases d'écriture.
*   **Fonctionnement** : Avant d'exécuter la moindre écriture physique de fichier, l'IDE ou l'agent a l'obligation d'invoquer `python src/bridges/story_guard.py --check_file <path>`.
*   **Validation** : Le script charge l'état réactif via `LoopState`, identifie la story active (`active_story_id`), extrait les composants et chemins déclarés dans son SCC, et vérifie si le `<path>` cible y figure.
*   **Rejet** : Si le fichier n'appartient pas au périmètre du contrat, l'outil lève une erreur critique et bloque l'écriture, immunisant le code source de l'application contre les modifications non planifiées.
