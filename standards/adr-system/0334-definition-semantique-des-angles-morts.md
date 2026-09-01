# ADR-0334 : Définition Sémantique des Angles Morts (Zero-Blindspot)

## 1. Objectif (Pourquoi)
Suite à l'évolution conjointe du framework lors de la session de refonte de la Traçabilité (ADR-0333) et de la primauté des maquettes SVG, il est devenu évident que la notion "d'Angle Mort" dans mLoop ne se limite pas à des bugs de code. Elle englobe une dimension systémique et architecturale que les agents IA doivent comprendre et intégrer viscéralement pour garantir la robustesse du projet.

## 2. Définition Opérationnelle : Qu'est-ce que "Couvrir tous les angles morts" ?

Dans l'écosystème Memory Loop, **couvrir tous les angles morts** signifie traquer et neutraliser proactivement 5 vecteurs de failles interconnectés :

### Axe 1 : L'Angle Mort Documentaire (Le "Drift" Lexical et Fonctionnel)
- **Définition** : L'IA ou l'humain dévie silencieusement de la Source Unique de Vérité (SSOT).
- **Exemple vécu** : Un agent rédige "Menu déroulant" au lieu de "Filtre rapide (Segmented Control)" parce qu'il a rédigé le texte avant de voir la maquette SVG, ou utilise le mot "Cartes" au lieu de "Sections groupées".
- **La couverture mLoop** : L'Agent Sentinel doit forcer la *Fidélité Séquentielle Visuelle*. La maquette SVG/Figma l'emporte toujours sur l'intuition de l'IA (Violation du Contrat Visuel = BLOCKING).

### Axe 2 : L'Angle Mort Technique (Les "Race Conditions" du Framework)
- **Définition** : Modifier une règle A sans voir que le script B (qui garantit la règle A) tourne en arrière-plan et annule l'action (Auto-Healing vs Linter).
- **Exemple vécu** : Effacer la section "Notes de Traçabilité" du Markdown pour appliquer l'ADR-0333, mais oublier que la routine Python wikifix.py réinjecte silencieusement cette section à chaque synchronisation parce qu'elle la croit supprimée par erreur.
- **La couverture mLoop** : Toute modification d'un *Gold Standard* ou d'un *Gabarit* doit s'accompagner d'une recherche transversale (Grep/AST) dans src/pipelines/ pour vérifier si le code source du framework "durcode" une dépendance à l'ancien standard.

### Axe 3 : L'Angle Mort Cognitif (La Paresse des LLMs)
- **Définition** : L'Agent IA se comporte comme un "linter mécanique" (coche des cases) au lieu d'adopter une posture d'Analyste Fonctionnel critique.
- **Exemple vécu** : L'agent lit "L'utilisateur clique sur Max" et valide, sans se demander : "Et si la quantité est égale à zéro ?".
- **La couverture mLoop** : La Constitution (AGENTS.md et Sentinel) exige un scepticisme agressif : traquer l'absence des 4 états UI (Empty, Loading, Error, Success), exiger des contrats API (FE ↔ BE) symétriques, et refuser le pseudo-code.

### Axe 4 : L'Angle Mort de Rétrocompatibilité (Le Legacy)
- **Définition** : Déclarer une nouvelle loi architecturale parfaite pour le futur, mais laisser l'ensemble du backlog passé dans l'illégalité sans plan de migration.
- **Exemple vécu** : Changer la règle de l'EvidencePack pour les nouvelles stories, provoquant le crash de 17 anciennes stories (REC-001 à REC-014) lors du prochain audit INVEST.
- **La couverture mLoop** : Une modification de standard (ADR) doit toujours s'accompagner d'un script de "Memory Hygiene" pour migrer la dette technique existante en silence.

### Axe 5 : L'Angle Mort Visuel pour l'IA (Le "Bruit" vs "Signal")
- **Définition** : Fournir une donnée brute que l'IA ne peut pas comprendre correctement, entraînant de fausses déductions.
- **Exemple vécu** : Demander à l'IA d'analyser un SVG contenant des millions de coordonnées vectorielles plutôt que de lui faire ingérer le DOM sémantique via markitdown_convert.
- **La couverture mLoop** : La primauté de la conversion sémantique. L'IA doit toujours travailler sur la donnée digérée (JSON/Markdown) plutôt que sur le binaire/vectoriel brut.

## 3. Synergie Humain-Machine
La véritable force de mLoop réside dans cette boucle itérative : 
L'Architecte (Humain) détecte une incohérence systémique (ex: "Pourquoi l'ordre vertical de l'interface n'est pas le bon ?"). L'Agent IA corrige l'instance, remonte à la cause racine (la règle de prompt), durcit la loi dans AGENTS.md, et met à jour le code source Python pour garantir que *plus jamais* un agent futur ne commettra cette même erreur fonctionnelle. C'est l'évolution par l'immunité acquise.
