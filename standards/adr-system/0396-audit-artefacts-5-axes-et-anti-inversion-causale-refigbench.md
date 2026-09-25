# ADR-0396 : Grille d'Audit Découplée 5-Axes, Détection Matricielle d'Inversion Causale & Handoff Multi-Harnais (Extension ReFigBench)

* **Statut** : ACCEPTÉ *(validé par Macro-Grill PO le 25 septembre 2026 — épopée EPIC-35)*
* **Date** : 25 septembre 2026
* **Décideurs** : Product Owner (Marco), Lead Architect mLoop, Agent Orchestrateur
* **Dépendances / Références** : [ADR-0202](0202-modularite-interne-agents.md) (Modularité ≤ 300L), [ADR-0375](0375-standard-preuve-epistemique-et-tracabilite-radicale.md) (Traçabilité Radicale), [ADR-0376](0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md) (Rigueur 360° Zéro Blindspot), [ADR-0377](0377-runtimes-agents-aval-et-herdr-operationnels.md) (Runtimes Aval & Herdr), [ADR-0392](0392-harnais-fidelite-visuelle-integrite-artefacts-topologiques.md) (Standard Topologique Artefacts v1), [ADR-0393](0393-decouplage-modalite-grill-scope-anti-cascade.md) (Modalités de Grill & Arrêt Formel), [ADR-0394](0394-tracabilite-bidirectionnelle-code-exigences-preuves-programmation-ast.md) (EvidencePack 2.0).
* **Référence Scientifique** : *ReFigBench: Benchmarking Scientific Figure Reconstruction as Editable PowerPoint Artifacts* (arXiv:2609.18844, Septembre 2026).

---

## 🚀 1. Contexte & Problématique

L'ADR-0392 a introduit dans mLoop une première protection contre la triche par image matricielle (barrière anti-raster paste $g(P) \in \{0, 1\}$) et une formule de notation à 2 variables dans `src/pipelines/audit_decoupler.py`. Cependant, l'étude scientifique approfondie de **ReFigBench** (*arXiv:2609.18844*) met en évidence deux faiblesses persistantes chez les agents multimodaux modernes :

1. **L'Inversion Causale Silencieuse (Figure 6 de ReFigBench)** : Un agent peut générer un schéma d'architecture visuellement impeccable et doté d'une éditabilité irréprochable (22/25), tout en ayant **inversé le sens de toutes les flèches du pipeline de dépendances**. Une telle inversion est fatale pour le Universal Dev Handoff, car elle enjoint les développeurs ou agents de codage avals à coder le système à l'envers.
2. **L'Effondrement des Connecteurs (*Connector Collapse*)** : Lors de l'usage de toolchains spécialisées, les modèles éliminent entre 91% et 100% des connecteurs relationnels natifs au profit de formes dessinées statiques.
3. **La Primauté du Harnais (*Harness Primacy*)** : Les performances d'un même modèle varient radicalement selon le profil d'outils et de contexte fourni par son harnais hôte.

Ce standard perfectionne la gouvernance des artefacts mLoop en déployant l'ensemble de l'appareil de mesure ReFigBench.

---

## 💡 2. Décisions d'Architecture

### A. Grille d'Audit Pénétrante Standard ReFigBench à 5 Axes ($Q = T + S + L + E + V$)
* **Module** : `src/pipelines/audit_decoupler.py`.
* **Échelle Normalisée sur 100 Points** :
  * **$T$ (Exactitude Textuelle - 20 pts)** : Conformité terminologique avec le lexique officiel (`src/utils/lexicon/`), lisibilité des étiquettes.
  * **$S$ (Structure Sémantique - 30 pts)** : Modules, hiérarchie et graphe des relations dirigées.
  * **$L$ (Fidélité de Disposition - 15 pts)** : Ordre de lecture (gauche-droite / haut-bas) et groupements.
  * **$E$ (Éditabilité Native - 25 pts)** : Présence de connecteurs vivants ancrés et absence d'aplatissement.
  * **$V$ (Détails Visuels - 10 pts)** : Palette graphique, alignements, badges.
* **Seuils d'Admissibilité** : Certification accordée si le score global $s(P) \ge 85/100$ ET si $S \ge 22/30$.

### B. Sanction Éliminatoire Radicale sur Inversion Causale (Arbitrage PO Q3)
* **Module** : `src/pipelines/causal_flow_linter.py`.
* **Principe Inviolable** : Confrontation formelle de la matrice d'adjacence dirigée du code AST / des exigences INVEST ($\mathbf{A}_{\text{spec}}$) avec la matrice d'adjacence observée sur le diagramme Archify/Canvas ($\mathbf{A}_{\text{diag}}$).
* **Sanction Radicale Validée** : Si une seule flèche de dépendance asymétrique est inversée ($\mathbf{A}_{\text{spec}}[u, v] = 1$ et $\mathbf{A}_{\text{diag}}[v, u] = 1$), le linter lève immédiatement `CAUSAL_FLOW_INVERSION_DETECTED`.
  * Le sous-score sémantique est forcé à zéro : **$S = 0$**.
  * Le score global est forcé à zéro : **$\text{Score} = 0.0$**.
  * La Gate associée est **immédiatement bloquée** ($g(P) = 0$).

### C. Moteur d'Audit Déterministe d'Arbre d'Objets Natifs ($O(P)$)
* **Module** : `src/pipelines/object_tree_auditor.py`.
* **Contrôle Mécanique** : Dénombrement exact des boîtes texte, formes vectorielles et connecteurs relationnels rattachés (`from` et `to`).
* **Plafonnement Anti-Collage $c(P)$** : Si une image bitmap couvre $\ge 85\%$ de la surface avec peu d'objets natifs, le score global est bridé à un maximum de 50/100.

### D. Profils de Universal Dev Handoff Adaptés au Harnais Cible
* **Module** : `src/pipelines/harness_adapter.py`.
* **Génération Calibrée** : Adaptation des paquets de spécifications selon l'agent aval visé :
  * *Claude Code* : Consignes directes concises, arborescence Markdown navigable avec WikiLinks, commandes CLI directes `uv run`.
  * *OpenCode* : Spécifications JSON IR déclaratives, découpage de sous-tâches ordonnées.
  * *Codex* : Stubs AST typés, signatures d'interfaces et assertions de tests unitaires explicites.
  * *Cursor* : Commentaires d'ancrage contextuel et chemins de symboles qualifiés.
* **Clause Anti-Flattening Universelle** : Injection formelle interdisant la fusion de modules en fichiers monolithiques.

### E. Extension CLI `artifact-check` & Vibe-Check Check 27
* **Commande CLI** : `python src/swarm.py artifact-check [--file <chemin>] --rubric-5x [--format json]`.
* **Check 27 Vibe-Check** : Exécution combinée de la barrière binaire $g(P)$, de l'audit d'objets, du linter d'inversion causale et du calcul 5-axes avant certification sprint.
* **Scellement EvidencePack 2.0** : Enregistrement du certificat d'audit dans `memory/evidence/<STORY_ID>_evidence.json` (ADR-0394).

---

## 🛡️ 3. Impact sur les Récits de l'Épopée EPIC-35

| Récit ID | Composant | Décision Clé Associée |
| :--- | :--- | :--- |
| **`MLOOP-350-BE`** | `Audit/Objects` | Analyseur déterministe d'arbre d'objets natifs pour SVG, Canvas et Archify IR. |
| **`MLOOP-351-BE`** | `Audit/Scoring` | Grille 5-axes ReFigBench ($T_{20} + S_{30} + L_{15} + E_{25} + V_{10}$) et plafond $c(P)$. |
| **`MLOOP-352-BE`** | `Linter/Causality` | Linter matriciel d'inversion causale ($\mathbf{A}_{\text{spec}} \text{ vs } \mathbf{A}_{\text{diag}}$) avec sanction $S=0$. |
| **`MLOOP-353-BE`** | `Handoff/Harness` | Profils de Dev Handoff sur-mesure (Claude Code, OpenCode, Codex, Cursor). |
| **`MLOOP-354-FULL`**| `CLI/VibeCheck` | CLI `artifact-check --rubric-5x`, Check 27 enrichi et intégration EvidencePack 2.0. |

---

## ⚖️ 4. Conséquences

### Positives
* **Élimination Définitive des Schémas Inversés** : La comparaison matricielle d'adjacence garantit mathématiquement que les flèches du schéma pointent dans le sens prescrit par le code et les règles métier.
* **Éditabilité Réelle Préservée** : Détection sans concession de la triche par dessin plat statique.
* **Efficience Maximale des Agents Avals** : Des paquets de handoff calibrés selon le harnais récepteur évitent les régressions et les boucles de correction coûteuses.

### Négatives / Contraintes
* **Exigence de Déclaration des Dépendances** : Nécessite que le modèle INVEST ou le code AST dispose d'un graphe de dépendances clair pour construire $\mathbf{A}_{\text{spec}}$.
* **Plafond Modulaire** : Chaque nouveau module (`object_tree_auditor.py`, `causal_flow_linter.py`, etc.) doit strictement respecter la limite de 300 lignes (`RULE-AST-01`).
