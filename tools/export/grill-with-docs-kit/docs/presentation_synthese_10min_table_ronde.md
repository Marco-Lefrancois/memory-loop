# ⚡ Synthèse Executive Table Ronde AI (10 Minutes Chrono)
## L'Ingénierie Agentique en Entreprise : De la Boîte Noire au Système Fondé sur des Preuves

> **Auteur** : Marco Lefrançois & Équipe Architecture mLoop  
> **Format** : Pitch Survol 10 min (avec repères de temps pour l'orateur)  
> **Audience** : Table Ronde AI, CTOs, Praticiens IA, Architectes & Product Owners  
> **Thèse Centrale** : *« L'intelligence brute des LLMs est une commodité volatile. La véritable valeur d'ingénierie réside dans l'ancrage documentaire vérifiable (Grill with Docs & Fact-Check) et dans le harnais déterministe qui encadre leur code (Vibe Check). »*

---

## ⏱️ Découpage & Minutage du Pitch

```mermaid
gantt
    title Déroulé du Pitch 10 Minutes (Ordre Officiel)
    dateFormat mm:ss
    axisFormat %M:%S
    section Ordre du Pitch
    1. Introduction : Le Défi de l'IA en Entreprise          :00:00, 01:00
    2. 1er Sujet : Grill-Me with Docs, Preuves & Archify     :01:00, 05:30
    3. 2e Sujet : Vibe Coding vs Vibe Check (Harnais)        :05:30, 08:30
    4. Conclusion & Phrase Choc                               :08:30, 10:00
```

---

# 🎙️ 1. Introduction : Le Grand Défi de l'IA en Entreprise `[00:00 - 01:00]`

### Le Paradoxe de la Vitesse sans Confiance
* **L'attrait initial** : Des LLMs impressionnants qui répondent instantanément et génèrent des pavés de texte ou de code.
* **Le mur en production** : L'effet « boîte noire », les hallucinations indécelables, l'amnésie entre deux sessions et la rupture de confiance avec les experts métiers.
* **La mission mLoop** : Remplacer l'illusion par la certitude mathématique et documentaire. Comment ? En imposant deux règles d'acier :
  1. **Sur les exigences métier** : L'IA doit prouver ce qu'elle a compris avant de questionner (*Grill-Me with Docs*).
  2. **Sur le code produit** : L'IA doit être encadrée par un harnais déterministe impitoyable (*Vibe Check*).

---

# 🥩 2. 1ᵉʳ SUJET : Grill-Me with Docs x Fact-Search, Fact-Check & Évidences `[01:00 - 05:30]`

### A. Préambule : Du « Grill-Me » de Matt Pocock au « Grill with Docs » mLoop
* **Le concept originel de Matt Pocock (*Grill-Me*)** :  
  Plutôt que de laisser un développeur ou un analyste rédiger un prompt flou et subir des suppositions, on demande au LLM d'inverser les rôles : *« Grill me »* (cuisine-moi). L'agent prend l'initiative et pose une série de questions fermées et pertinentes pour cerner les contraintes, les cas limites et les zones grises avant d'écrire la moindre ligne de code ou de spécification.
* **La lacune** :  
  Le Grill-Me classique excelle pour poser des questions pertinentes, face à des dizaines de spécifications, modèles DBML et transcriptions d'ateliers, **il agit comme une boîte noire**. Il pose d'excellentes questions, mais sans jamais prouver ce qu'il a compris au départ ni d'où proviennent ses constats.
* *L'origine de vouloir modifier le skill* :
	* Je veux régler le fameux 80/20 70/30 de vérité généré par l'AI pour les stories

---

### B. Casser la Boîte Noire : Comprendre d'abord ce que l'IA a compris

> 🎙️ **Les Propos Fondateurs** :  
> *« Ça fait plusieurs semaines, voir mois, que j'utilise le skill "Grill me" et souvent j'en venais au constat de me dire : "Pourquoi, il n'a pas posé de question". Donc je challenge mon agent pour savoir pourquoi et parfois il part une session en me disant qu'il avait oublié ou simplement en me répondant que l'agent n'avait pas besoin". C'est à partir de là que  j'ai réfléchi à comment je pouvais savoir sur quel extrait de documentation l'agent s'était basé pour établir son raisonnement, j'avais deux voix sur mes épaules — un peu comme l'ange et le démon, vous choisirez qui est qui !  
> 
> D'un côté, **JF** me dit : "Il faut vérifier ce que ton agent te rapporte, être convaincu à 100 % que c'est la vérité, mais sans que l'humain devienne le goulot d'étranglement qui passe des heures à tout relire !".  
> 
> De l'autre, **Jean-Philippe** me rappelle : "Prouve tes points, ne fais pas aveuglément confiance à l'IA ; utilise-la comme un assistant vérifiable, validable et cohérent, et reste en pleine possession de ton sujet !".  
> 
> Et c'est là que le Grill-Me ordinaire a une lacune pour moi : **c'est une boîte noire**. La séquence de question est vraiment bien, il sait cerner le sujet et te poser les bonnes questions qu'il n'a pas les réponses et soulève même de très bonnes pistes, par contre il n'expose jamais ce qu'il a compris au départ.  
> 
> Le Grill with Docs jumelé avec le Fact-Search / Check et les fichiers d'évidence inverse la charge de la preuve : l'IA m'expose d'abord ses faits sourcés et ses extraits textuels. Je valide ses preuves, je bonifie, et ensuite le Grill-Me déclenche sa session de question et soulève des explications et **des améliorations qu'on n'aurait jamais vues à l'analyse initiale** ! »*

---

### C. Le Skill en Action : Les 2 Captures Choc sur le Couvoir Boire & Frères (`INC-001-BE`)

Voici comment le skill matérialise cette promesse en direct sous les yeux de l'analyste :

#### 📸 Capture 1 : L'Anatomie du « Dossier de Preuves » (Ce que l'IA a compris)
![Capture 1 : Le Dossier de Preuves Documentaires structuré en 4 blocs](assets/screenshot_dossier_preuves_verbatims.png)

> **Ce que l'écran montre** : Avant de poser la moindre question, l'IA dresse son dossier d'évidences en 4 blocs étanches :
> 1. *Maquettes SVG* + Note photo d'atelier (`10_15_35...jpg` pour la colonne Lot).
> 2. *Extraits verbatim transcrits* avec citations mot à mot et lignes exactes.
> 3. *Modèle relationnel DBML* (`InventoryLot`, statuts, clés).
> 4. *Question d'arbitrage unitaire* avec Option A recommandée et motivée.

---

#### 📸 Capture 2 : L'Écran Scindé IDE (Le Choc de la Traçabilité Immédiate)
![Capture 2 : L'Écran Scindé IDE — À gauche le chat Grill-with-Docs, à droite la transcription brute](assets/screenshot_ide_split_screen.png)

* **💥 Pourquoi les collègues analystes ont « capoté » devant cet écran :**
  1. **Zéro hallucination & Preuve instantanée** : À gauche, l'agent cite les lignes **301–324** et **424–455**. À droite, la transcription brute est ouverte au même endroit. L'analyste valide la source en **2 secondes chrono**, sans réécouter 2 heures d'enregistrement.
  2. **Du québécois oral d'atelier aux règles d'ingénierie pures** : L'IA a traduit *« mes œufs les plus vieux overall »* et *« je me fous de ton troupeau »* en **3 règles univalentes** (`is_oldest_priority`, bascule Poule/Calendrier, contrainte de 2 à 3 buggies).
  3. **Réconciliation multimodale** : Convergence parfaite entre 11 maquettes SVG, 1 photo annotée sur place, 1 583 lignes de transcription et le schéma DBML.

---

### D. Le Flux Épistémique en 4 Temps & Le Verrou Fact-Check NLI

```mermaid
flowchart LR
    DOCS["Docs Sources<br/>(Transcriptions, DBML, SVG)"]
    --> SEARCH["1. Fact-Search FTS5<br/>Recherche amont des faits"]
    --> DOSSIER["2. Dossier de Preuves<br/>4 Blocs visibles (Grounding)"]
    --> CHECK["3. Fact-Check NLI<br/>Entailment vs Contradiction"]
    --> GRILL["4. Grill with Docs<br/>1 Arbitrage / Bonification"]
```

* **Le Verrou Aval Fact-Check NLI** : Les scénarios Gherkin sont certifiés automatiquement (`ENTAILMENT` = prouvé, `CONTRADICTION` = bloqué en 0.18s).

> 🌐 **Coup Double Live : Visualiser ce Flux avec Archify** :  
> 👉 [**`grill-with-docs-epistemic-flow.architecture.html`**](file:///C:/Memory%20Loop/tools/archify/showcase/grill-with-docs-epistemic-flow.architecture.html)  
> *(Projetez ce schéma interactif en direct : « Et ce visuel animé avec flux de particules que vous voyez à l'écran pour illustrer notre méthode ? Il a été modélisé et généré par notre propre moteur maison d'Architecture-as-Code : **Archify** ! »)*

---

# 🛡️ 3. 2ᵉ SUJET : Vibe Coding vs Vibe Check `[05:30 - 08:30]`

### A. La Transition : De la Rigueur sur les Faits à la Rigueur sur le Code
Une fois les faits validés et le récit exempt d'ambiguïté, l'agent doit passer à l'implémentation. Et c'est là que surgit le deuxième piège : **le Vibe Coding**.

---

### B. Le Mythe du Vibe Coding (Karpathy) vs La Réalité en Entreprise
* **La promesse Karpathy** : Coder au feeling, en langage naturel, sans lire le code produit (*« I just see stuff, say stuff, run stuff »*).
* **Le mur en entreprise (*The Scaling Cliff*)** :
  * *L'illusion de la vitesse* : On gagne 2 heures au départ, puis on perd 3 jours à déboguer des régressions fantômes.
  * *L'amnésie de session* : Après quelques échanges, le LLM oublie l'architecture, réinvente des patterns et casse des contrats d'API.
  * *La dette technique invisible* : Du code qui semble fonctionner en surface mais qui ne résiste à aucun cas limite en production.

---

### C. La Réponse mLoop : Le « Vibe Check » & l'Ingénierie de Harnais (ADR-0310)

> 🎙️ **La Métaphore de la Formule 1** :  
> *« Les freins d'une Formule 1 ne sont pas là pour ralentir le bolide, mais pour permettre au pilote de foncer à 300 km/h en toute confiance. Le Vibe Check, c'est exactement ça : un harnais d'ingénierie qui autorise l'IA à coder vite parce qu'elle est testée en continu. »*

```mermaid
flowchart LR
    A["Agent IA (Moteur)"] --> B["Vibe Check Déterministe Pré-Vol"]
    B --> C1["1. Directives Partagées<br/>(Même cerveau : Cursor, Claude, Gemini)"]
    B --> C2["2. Confinement de Périmètre<br/>(L'agent reste dans son carré de sable)"]
    B --> C3["3. Fact-Search Obligatoire<br/>(Zéro supposition avant de coder)"]
    B --> C4["4. Vérité du Backlog (SSOT)<br/>(Tâche réelle obligatoire, zéro fantôme)"]
    B --> C5["5. Respect des Standards d'Arborescence<br/>(Structure propre, zéro fichier parasite)"]
```

* **Le Pré-Vol en 5 Points Déterministe** :
  * Si un seul des 5 contrôles échoue, l'agent **a l'interdiction formelle de toucher au code** (*Zero-Fail Carryover*).
* **L'Anti-Amnésie (Session Resume)** :
  * Grâce à la commande `python src/swarm.py resume`, l'agent se réveille en **2 secondes** avec la mémoire exacte de la tâche, du backlog et des contraintes passées.

---

# 🚀 4. Conclusion & Message Clé `[08:30 - 10:00]`

### La Synthèse des Deux Sujets

| Dimension | Approche Naïve (Standard) | Solution mLoop Fondée sur les Preuves |
| :--- | :--- | :--- |
| **1ᵉʳ Sujet : Analyse & Vérité Métier** | **Grill-Me boîte noire** : questions vagues, hallucinations, suppositions | **Grill with Docs & Fact-Check** : Dossier de preuves en 4 blocs, L301-324 vérifiées en 2s, NLI déterministe |
| **2ᵉ Sujet : Code & Exécution** | **Vibe Coding amnésique** : code non relu, dérives d'API, perte de contexte | **Vibe Check & Harnais F1** : Pré-vol 5 points, Session Resume, Zero-Fail Carryover |
| **Outil Transversal Visuel** | Diagrammes statiques périmés sous Visio/Miro | **Archify** : Architecture-as-Code vivante et animée |

---

> ### 💬 La Phrase Choc à retenir pour la Table Ronde :
> *« L'IA ne doit pas être un devin complaisant qui improvise votre code ni une boîte noire qui interroge vos analystes à l'aveugle.  
> Elle doit être l'assistant le plus rigoureux de votre organisation : **adossée à des preuves documentaires irréfutables avec Grill-Me with Docs, et encadrée par un harnais déterministe impitoyable avec le Vibe Check.** »*

---

### 🧰 Liens vers les Ressources Clés du Kit
- 📄 [**Présentation Détaillée Grill with Docs & Fact-Check**](file:///C:/Memory%20Loop/tools/export/grill-with-docs-kit/docs/presentation_table_ronde.md)
- 📄 [**Présentation Vibe Coding vs Vibe Check**](file:///C:/Memory%20Loop/tools/export/grill-with-docs-kit/docs/presentation_vibe_coding_vs_vibe_check.md)
- 🌐 [**Visuel Interactif Archify (Flux Épistémique)**](file:///C:/Memory%20Loop/tools/export/grill-with-docs-kit/docs/assets/grill-with-docs-epistemic-flow.architecture.html)
- 📸 [**Capture Dossier de Preuves**](file:///C:/Memory%20Loop/tools/export/grill-with-docs-kit/docs/assets/screenshot_dossier_preuves_verbatims.png)
- 📸 [**Capture Écran Scindé IDE**](file:///C:/Memory%20Loop/tools/export/grill-with-docs-kit/docs/assets/screenshot_ide_split_screen.png)
