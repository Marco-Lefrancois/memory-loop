# ADR-0332 : Standard Assets Versionnés & Contrat Visuel

## Statut
**Accepté (SSOT Normatif)** — 20 août 2026

## Contexte & Problématique
Dans l'architecture à 3 Piliers de mLoop, le répertoire `reference/` sert de zone de staging local pour la matière première brute fournie par les clients (fichiers Word, Excel, présentations, exports Figma, vidéos, gros PDFs). En raison de la taille importante et du caractère temporaire de ces fichiers, `reference/` est systématiquement ignoré dans `.gitignore`.

Cependant, les projets de spécifications destinés à être versionnés sur Git (Azure DevOps, GitHub) et partagés avec les développeurs et les équipes métier (ex. `AccesDossierSante_Doc`) nécessitent que les **maquettes graphiques vectorielles (SVG)** et les **schémas d'architecture (PNG/WebP/SVG)** fassent partie intégrante de la documentation versionnée. Les documents Markdown ingérés sous `docs/00-ingested/` décrivent les métadonnées et calques textuels mais ne remplacent pas le rendu visuel indispensable aux équipes d'implémentation et de QA.

Afin d'assurer une cohérence parfaite avec la taxonomie ordonnée de `docs/` (`00-ingested`, `01-architecture`, `02-business-rules`, `03-models`, `04-transverse`), le répertoire des actifs graphiques adopte formellement le préfixe numérique `05-assets`.

## Décision d'Architecture

1. **Découplage Strict de reference/ (Staging Local Non Versionné)** :
   - `reference/` demeure strictement **local** et **exclu** du contrôle de version dans `.gitignore`.
   - Il sert uniquement de zone de dépôt pour les fichiers clients bruts non traités.

2. **Normalisation de docs/05-assets/ (Actifs Visuels Versionnés)** :
   - Tout actif graphique, maquette vectorielle, schéma ou image destiné à être visualisé dans la documentation et les récits utilisateur doit être stocké sous `docs/05-assets/`.
   - Arborescence standard sous `docs/05-assets/` :
     - `docs/05-assets/maquettes/` : Maquettes d'écrans vectorielles (SVG, WebP).
     - `docs/05-assets/diagrams/` : Schémas d'architecture et flux exportés (SVG, PNG).
     - `docs/05-assets/images/` : Captures d'écran et illustrations documentaires.

3. **Intégration dans le Pipeline d'Ingestion & Liens Relatifs Web-First** :
   - Lors de l'ingestion d'assets vectoriels (ex: convertisseur SVG), le fichier visuel est placé/copié sous `docs/05-assets/maquettes/` et le document Markdown généré sous `docs/00-ingested/` y fait référence via un lien relatif propre (ex: `![Maquette](../05-assets/maquettes/00_Dossier_Sante.svg)`).
   - Les liens absolus machine (`C:\Memory Loop` ou `file:///`) sont strictement interdits dans l'ensemble de la documentation versionnée.

## Conséquences & Bénéfices
- **Cohérence Structurale Parfaite** : Le dossier `docs/` s'ordonne naturellement de `00` à `05` (`00-ingested`, `01-architecture`, `02-business-rules`, `03-models`, `04-transverse`, `05-assets`).
- **Universal Dev Handoff** : Le dépôt Git cloné par un développeur ou consulté sur Azure DevOps contient nativement les maquettes visuelles sans nécessiter de fichiers locaux externes.
- **Hygiène Git** : La documentation ne versionne que les actifs graphiques utiles et optimisés sous `docs/05-assets/`, sans risquer d'embarquer des gigaoctets de matière première brute issue de `reference/`.
- **Rendu Visuel Préservé** : Les développeurs et testeurs visualisent instantanément les interfaces dans le visualiseur Git ou Markdown.
