# 🏛️ Aide-Mémoire : Standard ADR-0327 pour les Liens Wiki Azure DevOps

## Règle d'or de l'ADR-0327
Tout lien vers un Wiki Azure DevOps dans une User Story ou un document d'architecture mLoop doit être **100% fonctionnel et sans erreur 404**.

---

## Les Deux Formats Autorisés

### 1. Permalink avec `pageId` (Recommandé)
```text
https://dev.azure.com/{organisation}/{projet}/_wiki/wikis/{wikiName}/{pageId}/{slugTitle}
```
* **Exemple** :
  `https://dev.azure.com/Projet-SIGPA/SIGPA/_wiki/wikis/SIGPA.wiki/247/Cas-4-Changer-la-classe-des-%C5%93ufs`
* **Avantage** : Insensible aux renommages, déplacements et changements d'arborescence.

### 2. URL Déterministe avec `pagePath` (Exclusif)
```text
https://dev.azure.com/{organisation}/{projet}/_wiki/wikis/{wikiName}?pagePath={encodedPath}
```
* **Règles Strictes** :
  1. Le chemin commence par `/` (absolu depuis la racine du Wiki).
  2. L'extension `.md` doit être **retirée**.
  3. **JAMAIS** de paramètre `friendlyName=`.
  4. **JAMAIS** de paramètre `anchor=` dans les liens statiques sauf nécessité absolue.

---

## Matrice de Traduction & Encodage RFC 3986

| Élément dans le filesystem local (`reference/`) | Valeur requise dans `pagePath` | Encodage URL HTTP | Pourquoi ? |
| :--- | :--- | :--- | :--- |
| Espace simple ` ` | Espace ` ` | `%20` | Standard RFC 3986 |
| Tiret littéral de séparation ` - ` (stocké `-%2D-` dans Git) | ` - ` | `%20-%20` | **Évite le bug `---`** qui produit un 404 dans Azure DevOps |
| Tiret cadratin `—` (stocké `—-` dans Git) | `—` | `%E2%80%94` | Encodage UTF-8 conforme |
| Parenthèses `(` et `)` | `(` et `)` | `%28` et `%29` | Normalisation RFC 3986 |

---

## Checklist de Validation Avant Commit d'une Story

- [ ] L'URL utilise-t-elle le format `pageId` OU un `pagePath` exclusif ?
- [ ] Le paramètre proscrit `friendlyName=` est-il absent ?
- [ ] L'extension `.md` est-elle bien supprimée du `pagePath` ?
- [ ] Les tirets de titre sont-ils encodés `%20-%20` et NON `---` ?
- [ ] Si `reference/<wiki>.wiki/` existe localement, le fichier physique correspondant est-il bien présent ?
