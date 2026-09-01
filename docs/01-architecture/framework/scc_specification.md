# 📜 Spécification du Story Constraint Contract (SCC) & EvidencePacks

Le **Story Constraint Contract (SCC)** est la frontière absolue et le contrat de confiance entre l'Analyse (mLoop) et l'Exécution (Développeur Humain / Client). mLoop étant un Backend d'État et d'Architecture, il s'arrête à la définition et à la validation du SCC.

---

## 1. L'Analyste vs Le Développeur
Le rôle de mLoop est de garantir que le développeur ne prend pas de décisions d'architecture hors-périmètre (Scope Creep). Le développeur s'appuie sur le SCC fourni sous `backlog/stories/`.

Un SCC est un fichier Markdown généré par l'agent `plan` au terme du protocole *Grill with Docs*.

## 2. Le Format Obligatoire du SCC

### La Structure du Document
1. **Contexte (Why)** : Un court paragraphe expliquant l'objectif métier de la story.
2. **Critères d'Acceptation (4 Piliers Gherkin)** : Les scénarios au format `Given / When / Then` couvrant obligatoirement :
   - *Scénario Nominal*
   - *Scénario de Rejet / Exception*
   - *Scénario en Mode Dégradé / Résilience*
   - *UX & Observabilité / Logs*
3. **Contraintes Techniques (Constraints)** : Les structures de données, exclusions et types à respecter.
4. **Fichiers & Composants Autorisés (Checklist)** : Les chemins physiques autorisés.
5. **Notes de Traçabilité & Références (IA Only)** : Section obligatoire au bas du récit liée à l'artefact d'évidence.

**Règle de Nommage (Zéro-ID Local)** : Ne jamais inclure d'identifiant local (ex: US-001, REC-042) dans le titre `# Titre`, la description ou les scénarios Gherkin. L'identifiant est strictement réservé au nom de fichier et au frontmatter YAML.

**Gouvernance Typage Jira (Story Only)** : Tout récit local se traduit **toujours et exclusivement** par un ticket de type **Story** dans Jira Cloud via `python src/swarm.py jira_sync`.

## 3. EvidencePackEngine & Story Guard
* **Story Guard (`story_guard.py`)** : Intercepte toute tentative d'écriture hors du périmètre déclaré dans le SCC et bloque la modification.
* **EvidencePackEngine** : Génération autonome et synchrone d'un artefact JSON structuré sous `memory/evidence/<STORY_ID>_evidence.json` consignant les preuves, alertes (`[!NOTE]`, `[!WARNING]`, etc.) et questions ouvertes (`Q-`, `QD-`).

## 4. Audit & Validation (Score INVEST & Sentinel)
L'agent `sentinel` s'active en Phase 4 (VALIDATE) pour auditer la story et le code :
* Validation des 4 Piliers Gherkin.
* Calcul du score INVEST.
* Execution de `python src/swarm.py wikifix` et de la suite `aoep`.
