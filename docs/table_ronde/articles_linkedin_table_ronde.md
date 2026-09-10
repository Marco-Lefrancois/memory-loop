# 📝 Deux Articles Calibrés pour LinkedIn (< 3 000 caractères)

> **Auteur** : Marco Lefrançois  
> **Contexte** : Partage d'expérience issu de la Table Ronde AI mLoop / Boire & Frères  
> **Format** : Posts LinkedIn calibrés sous la limite stricte de 3 000 caractères (espaces et hashtags inclus).  

---

# 📱 Article 1 : Vibe Coding vs Vibe Check (2 190 caractères)

> 🖼️ **Visuel à joindre au post** : [**`assets/vibe_coding_vs_vibe_check_linkedin.jpg`**](file:///C:/Memory%20Loop/docs/table_ronde/assets/vibe_coding_vs_vibe_check_linkedin.jpg)

### 📄 Texte Prêt à Copier / Coller :

Le « Vibe Coding » fait fureur. 

Andrej Karpathy l'a résumé : « I just see stuff, say stuff, run stuff ». 
Vous jasez avec votre LLM, vous acceptez le code au feeling, et un prototype prend vie. C'est grisant !

Mais sur une codebase d'entreprise, le Vibe Coding pur vire vite au cauchemar :
❌ L'IA réinvente la roue : Elle recrée des fonctions utilitaires qui existent déjà dans le repo Git.
❌ L'amnésie des conventions : Elle ignore les patrons et standards documentés dans le Wiki d'équipe (Azure DevOps / Confluence).
❌ La régression silencieuse : Elle touche à 12 fichiers, brise les contrats d'API et crée de la dette technique invisible.

Nous ne rejetons pas la vitesse de l'IA. Au contraire !
Mais nous avons remplacé le Vibe Coding par une discipline stricte : le Vibe Check.

🏎️ La métaphore de la Formule 1
Les freins d’une F1 ne sont pas là pour ralentir le bolide : ils permettent au pilote de foncer à 300 km/h en toute confiance. 

Le Vibe Check, c'est ce harnais de sécurité déterministe.

Avant qu'un agent (Cursor, Claude Code, Copilot, Antigravity) ne touche à notre code, il passe un contrôle pré-vol en 5 points :

1️⃣ Directives d'Équipe Partagées : Même cerveau de règles (nommage, architecture, linters) quel que soit l'outil du dev.
2️⃣ Confinement au Périmètre Git : L'agent est cadenassé dans son sous-module. Interdiction de toucher aux fichiers transverses ou aux secrets.
3️⃣ Fact-Search dans le Wiki & le Repo Git : Le réflexe d'or. Avant d'écrire, l'agent cherche dans le code existant et les docs. On réutilise, on n'improvise pas.
4️⃣ Traçabilité Backlog (SSOT) : Zéro commit sauvage. Chaque diff est ancré dans une User Story validée.
5️⃣ Standards & Arborescence : Clean Architecture, typage strict, zéro fichier temporaire parasite.

Règle d'or : Zero-Fail Carryover. Si un seul contrôle échoue, interdiction d'écrire du code.

L'IA n'est pas un devin complaisant. Bien harnachée, elle devient le copilote le plus rigoureux et le plus rapide de l'équipe.

Et chez vous : plutôt Vibe Coding au feeling ou harnais de sécurité ? 👇

#VibeCoding #SoftwareEngineering #ArchitectureLogicielle #CleanCode #GenAI #AgenticAI #DevCommunity #TechLeadership #Git

---
---

# 📱 Article 2 : Grill-Me with Docs x Fact-Search (2 320 caractères)

> 🖼️ **Visuel à joindre au post** : [**`assets/grill_with_docs_linkedin.jpg`**](file:///C:/Memory%20Loop/docs/table_ronde/assets/grill_with_docs_linkedin.jpg)

### 📄 Texte Prêt à Copier / Coller :

Vous connaissez le concept de « Grill Me » de Matt Pocock ?

Au lieu d'écrire un prompt flou, on inverse les rôles : on demande à l'IA de nous cuisiner avec des questions dures sur nos cas limites avant de coder. Brillant !

Mais en entreprise, face à des centaines de pages de specs, des schémas DBML et des heures d'ateliers clients, le Grill-Me ordinaire a une faille majeure : c’est une boîte noire.

Il pose de bonnes questions, mais sans jamais prouver ce qu'il a compris au départ ni d'où viennent ses postulats.

Quand nous avons conçu notre chaîne agentique pour des domaines industriels complexes (comme un couvoir de 93 312 œufs par incubateur !), j’avais deux voix sur mes épaules :
• JF : « Vérifie ce que l'agent rapporte, sans devenir le goulot d'étranglement qui relit tout ! »
• Jean-Philippe : « Prouve tes points ! Ne fais pas aveuglément confiance à l'IA, reste maître de ton sujet. »

Notre solution : le Grill-Me with Docs x Fact-Search.

Nous avons inversé la charge de la preuve : avant de questionner l'analyste, l'agent doit dresser un Dossier de Preuves en 4 blocs :
1️⃣ Ancrage visuel : Références aux maquettes SVG et croquis d'atelier.
2️⃣ Verbatims mot à mot : Citations exactes de transcription avec minutage et numéros de lignes (ex: L301–324).
3️⃣ Modèle de données : Tables DBML et entités impliquées.
4️⃣ Arbitrage d'architecture : Choix unitaire clair (Option A recommandée vs Option B).

L'effet en direct est saisissant :
👉 À gauche de l'IDE : la recommandation de l'agent citant les lignes 301–324.
👉 À droite : la transcription brute ouverte au même endroit.

En 2 secondes, l'analyste valide la parole métier. Fini les 2 heures à réécouter un audio !

Mieux : en croisant les verbatims avec le schéma de données, l'agent a soulevé des optimisations qu'aucun de nous n'avait vues à l'analyse initiale.

Un moteur Fact-Check (NLI) certifie ensuite que chaque règle découle formellement des documents (ENTAILMENT), bloquant toute hallucination.

Quand on force l'IA à prouver ses sources, elle devient le sparring partner ultime des analystes et architectes.

Avez-vous déjà testé des mécanismes de preuve documentaire avec vos agents ? 👇

#ArtificialIntelligence #AgenticAI #PromptEngineering #BusinessAnalysis #SoftwareArchitecture #ProductManagement #FactChecking #Innovation
