# ADR-0392 : Harnais de Fidélité Visuelle & Intégrité Topologique des Artefacts Système (Barrière Déterministe Anti-Raster, Anti-Connector Collapse & Sonde Vibe-Check)

* **Statut** : ACCEPTÉ *(validé par Macro-Grill PO le 25 septembre 2026 — épopée EPIC-30)*
* **Date** : 25 septembre 2026
* **Décideurs** : Product Owner (Marco), Lead Architect mLoop, Agent Orchestrateur
* **Dépendances / Références** : [ADR-0202](0202-modularite-fichiers-source-et-documentation.md) (Modularité ≤ 300 L), [ADR-0375](0375-orchestration-canonique-5-phases-cycle-de-vie.md) (5 Phases Canoniques), [ADR-0376](0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md) (Rigueur Zéro Blindspot), [ADR-0377](0377-runtimes-agents-aval-et-herdr-operationnels.md) (Runtimes Aval & Herdr), [ADR-0389](0389-grill-v2-frontier-rounds-ungrillable-handoff-context-budget.md) (Grill v2 & Ungrillable Context), [ADR-0391](0391-harmonisation-cycle-de-vie-recits-5-phases-fsm.md) (Cycle de Vie 5 Phases & Auto-Clôture Gate 5).
* **Référence Scientifique** : *ReFigBench: Benchmarking Scientific Figure Reconstruction as Editable PowerPoint Artifacts* (arXiv:2609.18844, 2026).

---

## 🚀 1. Contexte & Problématique

Dans son rôle de **Fournisseur Universel de Spécifications (*Universal Dev Handoff*)**, Memory Loop génère et valide des artefacts d'architecture (diagrammes vectoriels Archify, graphes de dépendances, toiles Canvas, maquettes d'IHM) destinés aux ingénieurs et aux agents autonomes avals (Claude Code, OpenCode, Cursor, Codex).

La publication de l'étude scientifique **ReFigBench** (arXiv:2609.18844) met en évidence trois défaillances structurelles majeures chez les agents multimodaux modernes :
1. **L'usurpation par collage matriciel (*Raster Paste*)** : Les agents ont tendance à insérer une simple image raster (PNG/JPEG) pour simuler visuellement un schéma complexe sans avoir à en construire les composants vectoriels éditables. L'artefact est visuellement convaincant mais mort et inexploitable.
2. **L'effondrement des connecteurs (*Connector Collapse*)** : Lors de tâches de reconstruction ou de refactorisation visuelle, les modèles sacrifient jusqu'à 100 % des connecteurs logiques relationnels natifs (`edges` avec source `from` et cible `to`), les remplaçant par des segments décoratifs sans adhérence sémantique.
3. **L'illusion cosmétique et l'inversion de flux causaux** : Un diagramme peut être évalué très favorablement sur des critères purement visuels alors même que les dépendances logiques, le sens des flèches ou les flux de données ont été silencieusement inversés.
4. **La primauté de l'outillage de harnais (*Harness Primacy*)** : L'infrastructure de contrôle déterministe et les règles d'intégrité imposées par le harnais expliquent des variations de performance supérieures à 5 points à modèle LLM strictement invariant.

---

## 💡 2. Décisions d'Architecture

### A. Barrière Déterministe Binaire Anti-Raster ($g(P) \in \{0, 1\}$)
- **Module** : `src/pipelines/artifact_gate.py` (`DeterministicArtifactGate`).
- **Règle Stricte** : Évaluation binaire sans ambiguïté. Tout livrable d'architecture (Archify, SVG, Canvas) dont la surface occupée par des données matricielles (PNG, JPEG, WebP) excède **80 % de la surface utile** sans nœuds et connecteurs vectoriels éditables associés est **immédiatement rejeté** ($g(P) = 0$, motif `RASTER_PASTE_DETECTED`).
- **Frugalité Cognitive** : Zéro consommation de jetons LLM (Sentinel, relecteur ou juge) tant que la barrière déterministe $g(P)$ n'a pas validé l'openability, l'intégrité syntaxique et l'absence de collage raster.

### B. Règle du Graphe Fermé Strict & Anti-Effondrement dans Archify
- **Module** : `tools/archify/` et `src/commands/handlers/archify_core.py`.
- **Intégrité des Arêtes** :
  - Chaque connecteur (`edge`) doit obligatoirement déclarer un `from` (nœud source existant dans le graphe) et un `to` (nœud cible existant) valides.
  - Tout connecteur orphelin ou point d'ancrage indéterminé lève une erreur bloquante au build : `CONNECTOR_INTEGRITY_FAIL`.
  - Tout schéma comportant plus de 3 blocs modulaires dépourvu de connecteurs relationnels formels est rejeté avec l'erreur `CONNECTOR_COLLAPSE_DETECTED`.

### C. Ingestion Documentaire Hybride Ancrée (Algorithme ORBIT)
- **Module** : `src/pipelines/ingest_file_processors.py`.
- **Heuristique de Moisson** : Les figures et schémas d'architecture directeurs sont obligatoirement extraits et ancrés avec :
  1. Leurs légendes techniques contextuelles (*captions*).
  2. Les paragraphes et phrases du corps de texte qui les référencent.
  3. L'empreinte SHA-256 consécutive enregistrée dans `source_manifest.json`.

### D. Grille d'Audit à Barrière Multiplicative
- **Formule Déterministe** : Découplage de la fidélité topologique $S_{\text{topo}}$ et du rendu esthétique $S_{\text{visuel}}$ :
  $$\text{Score} = S_{\text{topo}} \times (0.7 + 0.3 \times S_{\text{visuel}})$$
- **Sanction Éliminatoire** : Si une relation causale est erronée ou manquante ($S_{\text{topo}} < 1.0$), la note globale subit un effondrement immédiat, rendant impossible la validation de la Gate sur de simples mérites cosmétiques.

### E. Standard Dual de Dev Handoff Multi-Harnais
- **Format Normatif** : Tout livrable d'architecture exporté par mLoop comporte simultanément :
  1. Un schéma abstrait déclaratif `JSON IR` (graphe de nœuds et arêtes typées).
  2. Un rendu vectoriel `SVG Sémantique` enrichi d'attributs `data-node-id`, `data-edge-from`, `data-edge-to` nativement interrogeables par Claude Code, OpenCode et Cursor sans inférence visuelle floue.

### F. Sonde Vibe-Check Check 27 & Commande CLI `artifact-check`
- **Commande CLI** : `python src/swarm.py artifact-check [--project <projet>] [--file <chemin>]`.
- **Intégration Pré-Vol** : Le **Check 27 (Fidélité Topologique & Intégrité des Artefacts)** est intégré à la suite de vol `vibe-check`.
- **Gouvernance de Phase** :
  - Phase 2 (`STAGE_2_PLAN_ANALYSE`) : Bloquant avant validation DoR (Gate 2).
  - Phase 4 (`STAGE_4_VALIDATE`) : Bloquant avant certification QA (Gate 4).

---

## 🛡️ 3. Impact sur les Récits de l'Épopée EPIC-30

| Récit | Rôle dans l'Architecture | Décision Clé Associée |
| :--- | :--- | :--- |
| **`MLOOP-300-BE`** | `DeterministicArtifactGate` & Anti-Raster Paste | Barrière déterministe binaire $g(P) \in \{0, 1\}$, plafond raster 80%. |
| **`MLOOP-301-BE`** | Validation Topologique Anti-Effondrement Archify | Règle du graphe fermé strict, interdiction des arêtes orphelines. |
| **`MLOOP-302-BE`** | Filtre d'Ingestion ORBIT pour Schémas | Ingestion hybride ancrée (Figure + Caption + Paragraphe référant). |
| **`MLOOP-303-BE`** | Grille d'Audit Découplée (Topologie vs Rendu) | Formule multiplicative $\text{Score} = S_{\text{topo}} \times (0.7 + 0.3 \times S_{\text{visuel}})$. |
| **`MLOOP-304-FULL`**| Contrats Dev Handoff & Commande CLI `artifact-check` | Standard dual JSON IR + SVG sémantique, Check 27 Vibe-Check. |

---

## ⚖️ 4. Conséquences

### Positives
* **Éditabilité Pérenne** : Tous les artefacts livrés restent modifiables sans dégradation.
* **Intégrité Causale Garantie** : Les schémas d'architecture reflètent strictement la vérité du code et des modèles.
* **Bouclier Anti-Triche Agentique** : Rejet mécanique des simulations par image bitmap avant tout coût d'inférence.
* **Contrat de Handoff Clair** : Les agents avals disposent de métadonnées topologiques certaines.

### Négatives / Contraintes
* **Rigueur de Modélisation Accrue** : Obligation d'attribuer des identifiants et ancres explicites à chaque bloc et arête.
* **Plafond Modulaire** : Chaque nouveau module (`artifact_gate.py`, etc.) doit respecter le plafond strict de 300 lignes (`RULE-AST-01`).
