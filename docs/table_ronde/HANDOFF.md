# 🤝 Document de Handoff — Kit Table Ronde AI & Publications LinkedIn

> **Date** : 4 Septembre 2026  
> **Auteur** : Marco Lefrançois & Agent Pair-Programming (mLoop)  
> **Statut** : ✅ **100 % Prêt pour Présentation & Déploiement**  
> **Répertoire Canonique** : [`docs/table_ronde/`](file:///C:/Memory%20Loop/docs/table_ronde/)  

---

## 🎯 1. Résumé Exécutif des Travaux Réalisés

L'ensemble des livrables pour la **Table Ronde AI** (pitch de 10 minutes, démonstrations en direct, artefacts interactifs, diagrammes animés Archify et articles LinkedIn) a été consolidé, testé et centralisé dans [`docs/table_ronde/`](file:///C:/Memory%20Loop/docs/table_ronde/).

### 🔑 Deux Piliers Théoriques & Pratiques :
1. **1ᵉʳ Sujet : Grill-Me with Docs x Fact-Search, Fact-Check & Évidences**
   - Évolution du concept de Matt Pocock (*Grill-Me*) en brisant l'effet « boîte noire » de l'IA.
   - Inversion de la charge de la preuve : avant de questionner l'analyste, l'agent produit un **Dossier de Preuves Documentaires** en 4 blocs étanches (maquettes SVG, verbatims transcrits mot à mot L301–324, modèle relationnel DBML, et arbitrage unitaire).
   - Verrou aval par **Fact-Check NLI déterministe** (`ENTAILMENT` vs `CONTRADICTION` en 0.18s).
   - Ancrage humain : La citation fondatrice de Marco (le dilemme de l'ange et du démon : JF exigeant la véracité sans goulot d'étranglement, Jean-Philippe exigeant des preuves vérifiables).

2. **2ᵉ Sujet : Vibe Coding vs Vibe Check — Le Regard Développeur**
   - Réponse au cauchemar du Vibe Coding pur en entreprise (réinvention de la roue, amnésie du Wiki, régressions silencieuses).
   - Métaphore F1 : les freins permettent de foncer à 300 km/h en confiance.
   - Contrôle pré-vol en **5 points** orienté Dev :
     1. Directives d'équipe partagées (Cursor, Claude Code, Antigravity).
     2. Confinement au périmètre Git (interdiction de toucher au code transverse ou aux secrets).
     3. Fact-Search dans le Wiki (Azure DevOps / Confluence) & le Repo Git (réutiliser, ne pas inventer).
     4. Traçabilité Backlog & User Stories (SSOT).
     5. Standards de code & Clean Architecture (zéro fichier temporaire parasite).
   - Règle **Zero-Fail Carryover** et reprise instantanée via `python src/swarm.py resume` (2s).

---

## 📂 2. Cartographie Complète des Fichiers du Dossier (`docs/table_ronde/`)

| Fichier | Type | Description |
| :--- | :---: | :--- |
| [**`README.md`**](file:///C:/Memory%20Loop/docs/table_ronde/README.md) | Index | Sommaire général, liens rapides et navigation du kit complet. |
| [**`presentation_synthese_10min_table_ronde.md`**](file:///C:/Memory%20Loop/docs/table_ronde/presentation_synthese_10min_table_ronde.md) | Conducteur | Script minuté de 10 min avec speaker notes, anecdotes et minutage officiel. |
| [**`guide_demonstrations_concretes.md`**](file:///C:/Memory%20Loop/docs/table_ronde/guide_demonstrations_concretes.md) | CLI Démo | Commandes PowerShell prêtes à copier-coller et talk-tracks pour les démos live. |
| [**`presentation_table_ronde.md`**](file:///C:/Memory%20Loop/docs/table_ronde/presentation_table_ronde.md) | Slides | 7 slides détaillées sur Grill with Docs, Fact-Search et Fact-Check NLI. |
| [**`presentation_vibe_coding_vs_vibe_check.md`**](file:///C:/Memory%20Loop/docs/table_ronde/presentation_vibe_coding_vs_vibe_check.md) | Slides | 7 slides détaillées sur le Vibe Check, l'ingénierie de harnais et l'anti-amnésie. |
| [**`presentation_archify.md`**](file:///C:/Memory%20Loop/docs/table_ronde/presentation_archify.md) | Slides | 7 slides détaillées sur le moteur Architecture-as-Code Archify. |
| [**`articles_linkedin_table_ronde.md`**](file:///C:/Memory%20Loop/docs/table_ronde/articles_linkedin_table_ronde.md) | Réseaux | 2 articles LinkedIn calibrés sous les 3 000 caractères avec visuels attachés. |
| [**`dossier_preuves_INC-002-BE.html`**](file:///C:/Memory%20Loop/docs/table_ronde/dossier_preuves_INC-002-BE.html) | Artefact | Dossier de preuves autonome en thème **bleu nuit foncé (`#020617`)**. |
| [**`grill-with-docs-epistemic-flow.architecture.html`**](file:///C:/Memory%20Loop/docs/table_ronde/grill-with-docs-epistemic-flow.architecture.html) | Schéma Live | Diagramme interactif Archify avec particules lumineuses animées. |
| [**`grill-with-docs-epistemic-flow.architecture.json`**](file:///C:/Memory%20Loop/docs/table_ronde/grill-with-docs-epistemic-flow.architecture.json) | Code IR | Spécification déclarative Archify validée 9/9 contrôles Showcase. |

### 🖼️ Sous-Dossier Visuels (`docs/table_ronde/assets/`) :
1. [**`screenshot_ide_split_screen.png`**](file:///C:/Memory%20Loop/docs/table_ronde/assets/screenshot_ide_split_screen.png) : Capture choc de l'écran scindé IDE (Grill-with-Docs à gauche, transcription brute L301-324 à droite).
2. [**`screenshot_dossier_preuves_verbatims.png`**](file:///C:/Memory%20Loop/docs/table_ronde/assets/screenshot_dossier_preuves_verbatims.png) : Anatomie du Dossier de Preuves Documentaires en 4 blocs.
3. [**`vibe_coding_vs_vibe_check_linkedin.jpg`**](file:///C:/Memory%20Loop/docs/table_ronde/assets/vibe_coding_vs_vibe_check_linkedin.jpg) : Visuel LinkedIn Article 1 (Split Vibe Coding chaotique vs Vibe Check télémétrie F1 & checklist 5 points).
4. [**`grill_with_docs_linkedin.jpg`**](file:///C:/Memory%20Loop/docs/table_ronde/assets/grill_with_docs_linkedin.jpg) : Visuel LinkedIn Article 2 (Split Black Box Grill-Me vs Dossier de Preuves holographique 4 blocs & sceau Fact-Check NLI).

---

## 🔗 3. Traçabilité Historique (Origine du Travail)

Pour une démonstration en direct de la session où les travaux ont été réalisés :
* **ID de Conversation** : `53dfbf7c-4395-41f3-80ef-43f49c8d1c21`
* **Lien Direct** : [`conversation://53dfbf7c-4395-41f3-80ef-43f49c8d1c21`](conversation://53dfbf7c-4395-41f3-80ef-43f49c8d1c21)
* **Étapes Clés du Transcript** : Steps 219 à 225 (conception du dossier de preuves `INC-001-BE` et `INC-002-BE` sur le couvoir Boire & Frères).

---

## 🚀 4. Prochaines Actions Immédiates pour Marco

1. **Publication LinkedIn (Article 1)** :
   - Copier le texte de l'Article 1 depuis [`articles_linkedin_table_ronde.md`](file:///C:/Memory%20Loop/docs/table_ronde/articles_linkedin_table_ronde.md) (2 190 caractères).
   - Attacher le visuel [`assets/vibe_coding_vs_vibe_check_linkedin.jpg`](file:///C:/Memory%20Loop/docs/table_ronde/assets/vibe_coding_vs_vibe_check_linkedin.jpg).
2. **Publication LinkedIn (Article 2)** :
   - Copier le texte de l'Article 2 (2 320 caractères).
   - Attacher le visuel [`assets/grill_with_docs_linkedin.jpg`](file:///C:/Memory%20Loop/docs/table_ronde/assets/grill_with_docs_linkedin.jpg).
3. **Répétition du Pitch 10 Min** :
   - Suivre le chronomètre dans [`presentation_synthese_10min_table_ronde.md`](file:///C:/Memory%20Loop/docs/table_ronde/presentation_synthese_10min_table_ronde.md).
   - Ouvrir en onglets préalables dans le navigateur :
     - Le diagramme animé [`grill-with-docs-epistemic-flow.architecture.html`](file:///C:/Memory%20Loop/docs/table_ronde/grill-with-docs-epistemic-flow.architecture.html)
     - L'artefact bleu nuit [`dossier_preuves_INC-002-BE.html`](file:///C:/Memory%20Loop/docs/table_ronde/dossier_preuves_INC-002-BE.html)
