---
id: 0327
validation_rules: []
---

# 🏛️ ADR-0327 : Standard Canonique de Construction des URLs de Wiki Azure DevOps

- **Statut** : ACCEPTED
- **Date** : 2026-08-21
- **Auteurs** : mLoop Architecture & Equipe Projet
- **Domaine** : SSOT, Documentation, Gouvernance des Liens Externes

---

## 1. Contexte & Problématique

Dans les User Stories (`backlog/stories/`), la section `## Références` contient des liens hypertextes vers la documentation d'architecture et les spécifications fonctionnelles hébergées sur le **Wiki Azure DevOps** du client.

Deux problèmes récurrents ont été constatés lors de la navigation vers ces ressources :
1. **Erreurs 404 (Page Not Found)** : Liens construits sur des chemins supposés ou incomplets (ex: omission de sous-dossiers intermédiaires comme `inventaire-disponibilites` ou `Architecture-Segment2`).
2. **Conflit de Paramètres d'URL Azure DevOps** : Utilisation simultanée du paramètre `friendlyName=...` et du paramètre `pagePath=...`, ce qui perturbe le moteur de routage interne d'Azure DevOps et redirige vers des pages d'accueil ou des erreurs.

Il est nécessaire d'établir un standard formel et déterministe pour la construction des URLs de Wiki Azure DevOps consommables par les développeurs et les agents IA.

---

## 2. Décision d'Architecture

### A. Les Deux Formats Canoniques Reconnus

#### 🥇 Format 1 : Le Permalink Natif Azure DevOps (Recommandé / Prioritaire)
Lorsqu'un identifiant numérique de page (`pageId`) est connu, utiliser le lien permanent officiel généré nativement par Azure DevOps :

$$\text{URL} = \texttt{https://dev.azure.com/\{organisation\}/\{projet\}/\_wiki/wikis/\{wikiName\}/\{pageId\}/\{slugTitle\}}$$

- **Exemple Réel** : `https://dev.azure.com/Projet-SIGPA/SIGPA/_wiki/wikis/SIGPA.wiki/247/Cas-4-Changer-la-classe-des-%C5%93ufs-apr%C3%A8s-la-r%C3%A9ception`
- **Avantage** : 100% insensible aux renommages de dossiers parents, déplacements d'arborescence et pièges d'encodage d'espaces.

#### 🥈 Format 2 : Le Chemin d'Arborescence Déterministe (`pagePath`)
En l'absence de `pageId` numérique connu, utiliser le chemin absolu RFC 3986 depuis la racine du wiki :

$$\text{URL} = \texttt{https://dev.azure.com/\{organisation\}/\{projet\}/\_wiki/wikis/\{wikiName\}?pagePath=\{encodedPath\}}$$

1. **Exclusivité du paramètre `pagePath`** : Ne JAMAIS inclure `friendlyName=`, `anchor=` ou d'autres paramètres d'état de vue dans les liens statiques des Stories, sauf si une ancre explicite est indispensable.
2. **Encodage Strict de l'Arborescence (`pagePath`)** :
   - Le chemin doit être le **chemin absolu depuis la racine du wiki Azure DevOps**, débutant par un slash `/`.
   - L'extension de fichier `.md` doit être **omise** du `pagePath`.
   - Les espaces et caractères spéciaux doivent être encodés selon la norme RFC 3986 (ex: `%20` pour les espaces, `%E2%80%94` pour les cadratins `—`, `%28` et `%29` pour les parenthèses `( )`).

### B. Correspondance Physique Filesystem ↔ Wiki Azure DevOps
Pour tout projet disposant d'un staging local du wiki sous `reference/<nom_wiki>.wiki/` :
1. Le chemin relatif du fichier `.md` sous `reference/<nom_wiki>.wiki/` définit exactement la structure du `pagePath`.
2. Exemple :
   - Fichier physique : `reference/SIGPA.wiki/Projet-S.I.G.P.A.-(Système-Intégré-Gestion-Production-Avicole)/Architecture-Segment2/docs/04-transverse/01-modele-de-donnees-transverse.md`
   - `pagePath` décodé : `/Projet S.I.G.P.A. (Système Intégré Gestion Production Avicole)/Architecture-Segment2/docs/04-transverse/01-modele-de-donnees-transverse`
   - URL finale : `https://dev.azure.com/Projet-SIGPA/SIGPA/_wiki/wikis/SIGPA.wiki?pagePath=/Projet%20S.I.G.P.A.%20(Syst%C3%A8me%20Int%C3%A9gr%C3%A9%20Gestion%20Production%20Avicole)/Architecture-Segment2/docs/04-transverse/01-modele-de-donnees-transverse`

### C. Règles de Remplacement des Symboles Échappés
| Symbole dans le nom de fichier local | Titre Réel dans le Wiki UI | Valeur dans `pagePath` Wiki | Encodage URL Strict |
| :--- | :--- | :--- | :--- |
| Tirets de séparation standard `-` | Espace ` ` | Espace ` ` ou tiret `-` | `%20` ou `-` |
| `%2D` encadré de tirets `-%2D-` | Espace - Espace ` - ` | ` - ` | `%20-%20` *(Évite l'écrasement en 3 tirets `---`)* |
| Tiret cadratin `—-` | Tiret cadratin `—` | `—` | `%E2%80%94` |
| Parenthèses `( )` | Parenthèses `( )` | `( )` | `(` `)` ou `%28` `%29` |

> [!IMPORTANT]
> **Le Piège du `%2D` dans Azure DevOps Git** : Dans le backend Git d'Azure DevOps, un tiret littéral dans un titre (ex: `Récits - Cas utilisations`) est enregistré sous le nom `Récits-%2D-Cas-utilisations.md`. Lors de l'appel HTTP, le serveur web décode `%2D` en tiret `-`. Si l'URL contient `---`, Azure DevOps cherche un titre avec 3 tirets et renvoie une erreur 404. Il faut impérativement encoder le segment sous la forme `R%C3%A9cits%20-%20Cas%20utilisations`.

---

## 3. Conséquences

### Positives
- **100% de Liens Fonctionnels** : Zéro erreur 404 lors du clic sur les références depuis les User Stories.
- **Vérifiabilité Déterministe** : Tout agent peut valider l'existence physique du fichier sous `reference/` avant de générer l'URL.
- **Interopérabilité** : Clarté immédiate pour les développeurs utilisant le portail Azure DevOps.

### Négatives / Contraintes
- Nécessite de vérifier les chemins réels dans l'arborescence du wiki local plutôt que d'assumer des chemins simplifiés.

---
*Généré dans le cadre de la gouvernance documentaire mLoop ADR-0327.*
