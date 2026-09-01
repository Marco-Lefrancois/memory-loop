# ADR-0309 : Adoption du standard Agent Plugins 1.0

**Statut** : Accepté
**Date** : 10 août 2026
**Auteurs** : Équipe mLoop
**Domaine** : Architecture Multi-Agents & Interopérabilité

## 1. Contexte et Problème

Historiquement, l'écosystème Memory Loop (mLoop) structure ses compétences (skills) dans `.agents/skills/` via des fichiers `SKILL.md` et configure ses serveurs Model Context Protocol (MCP) de manière interne via `opencode.json`. Bien que cette séparation soit propre, elle limite la portabilité de nos outils vers d'autres clients d'agents (Cursor, VS Code, GitHub Copilot, OpenAI Codex) qui imposent chacun leurs propres formats de manifestes et structures de dossiers.

Le 6 août 2026, un comité technique indépendant (Amazon, Cursor, Microsoft, OpenAI, Vercel) a publié la spécification **Agent Plugins 1.0**. Ce standard ouvert définit un format de paquetage unifié, neutre et prédictible (le "plugin.json" et "mcp.json") permettant aux skills et serveurs MCP d'être découverts et exécutés par n'importe quel client compatible sans modification.

Nous devons rendre nos 21 skills et 5 ponts MCP nativement portables sans introduire de changements cassants (breaking changes) pour notre framework interne.

## 2. Décision

Nous adoptons le standard Agent Plugins 1.0 pour le framework mLoop selon les principes suivants :

1. **Mono-Plugin (mloop-framework)** : Nous regroupons l'ensemble de nos skills et de nos configurations MCP dans un seul plugin racine.
2. **Racine du Plugin** : Le dossier `.agents/` devient la racine (Plugin Root) de notre plugin portable.
3. **Manifestes Standardisés** :
   - Ajout d'un fichier `.agents/plugin.json` respectant strictement le JSON Schema 2020-12 de la spécification (nom `mloop-framework`, aucune propriété non-standard à la racine).
   - Ajout d'un fichier `.agents/mcp.json` déclarant nos 5 serveurs MCP au format `stdio`.
4. **Namespace d'Extension** : Toutes les données spécifiques à l'IDE OpenCode ou mLoop non couvertes par la spécification portable (comme les définitions d'agents, les commandes CLI, et les métadonnées de `manifest.yaml`) seront ségrégées dans le namespace d'extension `.agents/com.nmedia.opencode/` ou déclarées via le champ `extensions` de `plugin.json`.
5. **Double Déclaration Pragmatiste pour le MCP** : Nos bridges Python utilisant des chemins absolus (ex. `C:\Memory Loop\src\...`), nous utiliserons la variable `${PLUGIN_ROOT}` pour assurer le confinement des chemins (Path Containment) tel qu'exigé par la norme. La configuration interne actuelle restera active dans `opencode.json` pour éviter tout risque de régression locale, la portabilité externe étant activée via la nouvelle configuration.

## 3. Conséquences

### Positives
- **Portabilité Immédiate** : Nos skills mLoop deviennent consommables tels quels par tous les clients compatibles (Cursor, GitHub Copilot, Kiro, etc.).
- **Zéro Duplication de Contenu** : Le format `SKILL.md` étant la norme sous-jacente des Agent Plugins, nos dossiers `.agents/skills/` n'ont pas besoin d'être modifiés.
- **Séparation Nette** : La spécificité de notre framework est confinée à un namespace dédié, évitant de polluer l'espace standard.

### Négatives / Risques
- **Maintenance** : La configuration MCP sera définie à la fois pour le client local (`opencode.json`) et pour le plugin universel (`mcp.json`). Pour mitiger cela, la vérification de synchronisation sera intégrée à la CLI (`python src/swarm.py calibrate`).
- **Confinement (Sandboxing)** : La règle stricte de la spécification exigeant que `cwd` et `command` (stdio) ou les ressources ne sortent pas du plugin root pourrait nécessiter l'adaptation de certains de nos scripts bridges (via wrapping ou liens relatifs stricts) si exportés brutalement.

## 4. Alternatives Considérées

- **Multi-Plugins** : Packager chaque skill comme un plugin distinct. *Rejeté* car la version 1.0 de la spécification ne gère pas encore formellement les dépendances inter-plugins, ce qui rendrait l'orchestration du framework complexe.
- **Créer un dossier parallèle (ex. `.plugins/`)** : *Rejeté* car la spécification interdit les symlinks sortant de la racine du plugin, forçant ainsi une duplication totale de notre base de connaissances (les `SKILL.md`).
- **Ignorer la norme** : *Rejeté* car la portabilité et l'interopérabilité multi-clients sont stratégiques pour l'évolution de Memory Loop.
