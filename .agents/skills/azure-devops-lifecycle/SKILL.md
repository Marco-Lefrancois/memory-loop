---
name: azure-devops-lifecycle
description: Guide d'ingénierie et d'orchestration Azure DevOps pour mLoop. Régit la résolution canonique des URLs Wiki selon ADR-0327 (zéro 404), la synchronisation des récits avec Azure Boards (Work Items Gherkin), le diagnostic de build Azure Pipelines et le cycle PR sur Azure Repos.
---

# 🌀 Skill : Cycle de Vie & Intégration Azure DevOps (`/azure-devops`)

## Aperçu & Rôle Souverain
Ce skill d'ingénierie régit toutes les interactions entre les agents **Memory Loop (mLoop)** et la plateforme **Azure DevOps**. Dans l'écosystème mLoop, Azure DevOps héberge fréquemment la documentation de référence, les spécifications fonctionnelles d'architecture client (Azure Wiki), les backlogs de développement (Azure Boards) ainsi que les dépôts et pipelines de livraison (Azure Repos & Pipelines).

Ce skill applique de manière inviolable les standards d'architecture souverains de mLoop, en particulier :
* **[ADR-0327](../../../standards/adr-system/0327-azure-devops-wiki-url-canonical-standard.md)** : *Standard Canonique de Construction des URLs de Wiki Azure DevOps* (zéro 404, gestion de l'encodage `%20-%20`, élimination des conflits `friendlyName=`).
* **Pattern Dual-Link** : Association systématique d'un lien Web HTTPS distant (Azure DevOps) et d'un chemin relatif local au dépôt ou au staging `reference/`.

---

## Déclencheurs & Exclusions
- **Quand l'utiliser** :
  - Lors de la Phase 1 (Ingestion & Specs) et Phase 2 (Architecture & ADRs) lorsqu'il faut référencer ou lire des spécifications hébergées sur un Wiki Azure DevOps.
  - Lors de la rédaction de User Stories (Phase 3) pour garnir la section `## Références` avec des liens Azure DevOps valides.
  - Pour synchroniser des récits mLoop vers Azure Boards (Work Items) en alternative ou complément à Jira Cloud.
  - Pour diagnostiquer des échecs de build Azure Pipelines ou auditer des Pull Requests Azure Repos.
- **Quand NE PAS l'utiliser** :
  - Pour les tâches internes au code source de mLoop sur GitHub (utiliser le skill [`github-ops`](../github-ops/SKILL.md)).
  - Pour les recherches documentaires purement locales déjà indexées dans SQLite FTS5 (utiliser [`fact_search`](../source-driven-development/SKILL.md)).

---

## Déroulé Opérationnel par Module

### Module 1 : Navigation Wiki & Résolution Canonique des URLs (ADR-0327)

Lorsqu'une story ou une architecture référence une page de Wiki Azure DevOps, l'agent **doit impérativement** respecter l'ordre de préséance suivant :

#### 🥇 Format 1 : Le Permalink Natif Azure DevOps (Prioritaire)
Dès qu'un identifiant numérique `pageId` est connu (via l'outil MCP Azure DevOps ou la lecture de l'arborescence) :
$$\text{URL} = \texttt{https://dev.azure.com/\{org\}/\{projet\}/\_wiki/wikis/\{wikiName\}/\{pageId\}/\{slugTitle\}}$$
* **Exemple** : `https://dev.azure.com/Projet-SIGPA/SIGPA/_wiki/wikis/SIGPA.wiki/247/Cas-4-Changer-la-classe-des-oeufs`
* **Garantie** : 100% insensible aux renommages et déplacements de sous-dossiers.

#### 🥈 Format 2 : Le Chemin d'Arborescence Déterministe (`pagePath`)
En l'absence de `pageId`, construire l'URL selon la norme RFC 3986 stricte :
$$\text{URL} = \texttt{https://dev.azure.com/\{org\}/\{projet\}/\_wiki/wikis/\{wikiName\}?pagePath=\{encodedPath\}}$$

**Règles Inviolables de construction du `pagePath`** :
1. **Exclusivité absolue de `pagePath`** : Ne JAMAIS associer `friendlyName=`, `anchor=` ou d'autres paramètres d'état de vue dans les liens statiques des Stories.
2. **Pas d'extension `.md`** : Le `pagePath` doit pointer vers la ressource sans son extension Markdown physique.
3. **Le Piège du `%2D` (Écrasement en 3 tirets)** :
   * Dans le Git Azure DevOps, un titre avec tiret littéral (ex: `Récits - Cas utilisations`) est stocké avec le segment `-%2D-`.
   * En URL HTTP, ce segment doit être encodé `%20-%20`. **Interdiction absolue d'écrire `---`** qui produit une erreur 404 immédiate.
4. **Vérification contre le Staging Local** :
   * Si le projet possède un sous-dossier `reference/<nom_wiki>.wiki/`, l'agent doit vérifier l'existence physique du fichier avant d'émettre l'URL.
   * L'agent peut utiliser le script utilitaire :
     `python .agents/skills/azure-devops-lifecycle/scripts/resolve_wiki_url.py --file reference/SIGPA.wiki/chemin/vers/page.md`

---

### Module 2 : Gestion des Work Items & Synchronisation Azure Boards

Pour exporter ou synchroniser le backlog de stories mLoop (`backlog/stories/*.md`) vers Azure Boards :

1. **Mapping des Types d'Items** :
   * Epic / Feature mLoop $\rightarrow$ Work Item Type `Epic` ou `Feature`.
   * User Story mLoop $\rightarrow$ Work Item Type `User Story` (Agile) ou `Product Backlog Item` (Scrum).
   * Tâches d'ingénierie $\rightarrow$ Work Item Type `Task`.
2. **Injection des 4 Piliers Gherkin** :
   * La description du Work Item doit contenir le format Gold Standard :
     - *Contexte & Persona* : En tant que... Je veux... Afin de...
     - *Acceptance Criteria (Gherkin)* : `Given / When / Then` rigoureux.
     - *EvidencePack Contract* : Référence au livrable de test attendu.
     - *Dual-Link Références* : Lien vers la page Wiki Azure DevOps correspondante (`ADR-0327`).
3. **Mise à jour d'état** :
   * `New` $\rightarrow$ Rédaction préliminaire.
   * `Active` $\rightarrow$ En cours d'implémentation (Focus story).
   * `Resolved` $\rightarrow$ Vibe-Check passé avec succès & EvidencePack généré.
   * `Closed` $\rightarrow$ Ship & Sync validé.

---

### Module 3 : Diagnostic CI/CD Azure Pipelines

Lorsqu'un build échoue sur Azure Pipelines :

1. **Recherche ciblée du Run** :
   * Récupérer l'identifiant du run via l'outil MCP `pipelines_get_run` ou la commande Azure CLI :
     `az pipelines runs show --id <run_id> --org <org_url> --project <project_name>`
2. **Extraction chirurgicale des logs** :
   * Ne jamais injecter l'intégralité du log de build (saturation du contexte).
   * Extraire uniquement les sections de failure (`grep -i -E "error|failed|exception|fatal"`).
3. **Correction & Déclenchement** :
   * Reproduire l'échec localement avec le harnais de test mLoop (`pytest`).
   * Valider la correction avant de relancer le pipeline distant :
     `az pipelines run --id <pipeline_id>`

---

### Module 4 : Cycle de Pull Request sur Azure Repos

1. **Pré-vol obligatoire Vibe-Check** :
   * Aucune PR ne doit être ouverte sans que le Vibe-Check 9 points de mLoop soit vert :
     `python src/swarm.py vibe-check --project <nom-projet>`
2. **Création de la PR** :
   * Associer systématiquement la PR aux Work Items IDs concernés (`--work-items <id1> <id2>`).
   * Rédiger le résumé de la PR en incluant le tableau des tests validés et les liens vers les ADRs impliqués.

---

## Configuration du Serveur MCP Azure DevOps

Le serveur MCP officiel de Microsoft est déclaré dans `.agents/mcp.json` :
```json
{
  "azure_devops": {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "@azure-devops/mcp"],
    "env": {
      "AZURE_DEVOPS_ORG_URL": "${AZURE_DEVOPS_ORG_URL}",
      "AZURE_DEVOPS_PAT": "${AZURE_DEVOPS_PAT}"
    }
  }
}
```

---

## Table Anti-Rationalisation (Inviolable)

| Excuse de l'Agent (Paresse) | Réalité & Règle Inviolable |
| :--- | :--- |
| *"Le lien Wiki avec friendlyName= fonctionne dans mon navigateur, donc je peux le laisser dans la Story."* | `friendlyName=` entre en conflit avec `pagePath=` selon le routage interne d'Azure DevOps et mène à des 404 aléatoires. **Interdiction formelle selon ADR-0327**. |
| *"Je peux remplacer le titre 'A - B' par 'A---B' dans l'URL du Wiki."* | Les triples tirets provoquent une erreur 404 immédiate dans Azure DevOps Wiki. Remplacer impérativement par `%20-%20` ou utiliser le `pageId`. |
| *"Le client n'a pas configuré son PAT Azure DevOps, donc j'invente les liens de références."* | Ne jamais fabriquer d'URL non vérifiée. Vérifier la présence physique du fichier Markdown dans `reference/<wiki>.wiki/` ou utiliser le script `resolve_wiki_url.py`. |
| *"Je vais copier les 10 000 lignes du log Azure Pipelines dans la fenêtre de discussion."* | Sature le contexte de l'agent. Isoler les 20 lignes encadrant l'erreur fatale ou l'assertion échouée. |
