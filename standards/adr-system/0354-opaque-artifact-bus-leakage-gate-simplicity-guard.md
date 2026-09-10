# ADR-0354 : Bus d'Artefacts par Handles Opaques, Porte Anti-Fuite de Vérification & Garde-Fou de Simplicité

- **Statut** : Accepté
- **Date** : 2026-09-07
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Moteur d'Artefacts (`src/engine/artifacts/`), Élagage Contextuel (`src/bridges/context_pruner.py`), Portes de Vérification (`src/engine/gates/verification_leakage.py`, `src/engine/gates/simplicity_guard.py`), Deep Search (`src/engine/deep_search/`)
- **Références** : Google Research (*Planetary Prediction Engine: Automating Global Models via Earth AI*, Août 2026 / arXiv:2608.26088v1), ADR-0335 (Epistemic Grounding Diptyque), ADR-0341 (Runnable Gates), ADR-0345/0349 (Crawler Dual-Stack), ADR-0353 (Trust & Evidence in Agentic RAG)

---

## 1. Contexte & Problématique

Dans les systèmes multi-agents autonomes tels que mLoop, les exécutions longues (supérieures à plusieurs dizaines ou centaines d'étapes) se heurtent à trois pathologies récurrentes identifiées lors de nos travaux de recherche :

1. **La Saturation Contextuelle par Sérialisation Brute** :
   Le passage direct de charges utiles volumineuses (résultats de crawl web, listings FTS5, arbres AST complets, diffs étendus) dans les prompts des agents provoque l'épuisement de la fenêtre contextuelle, augmente drastiquement la latence et les coûts, et induit des dérives d'attention et des hallucinations (*lost in the middle*).
2. **La Fuite de Spécification & Vérification Tautologique (*Verification Leakage*)** :
   Les modèles de langage générant des tests unitaires ou des scénarios Gherkin BDD ont tendance à concevoir des tests qui s'auto-valident (tests tautologiques affirmant sur des mocks injectés localement ou violant l'encapsulation en testant des membres privés ad-hoc), produisant de faux positifs ("tests verts" mais code fragile).
3. **Le Surapprentissage Architectural & Hyper-Complexité (*Over-Engineering*)** :
   Face à des tâches élémentaires ou moyennes, les agents génèrent fréquemment des abstractions excessives (microservices inutiles, modèles à 4 couches d'indirection, dépendances externes superflues), s'écartant du principe de simplicité et du diff minimal viable.

Le **Planetary Prediction Engine (PPE)** de Google Research a démontré qu'un système d'IA autonome pouvait enchaîner plus de 790 étapes séquentielles avec une fidélité prédictive supérieure aux experts humains en appliquant trois verrous stricts : un découplage de bus par *handles opaques*, un *Feature Gate* anti-fuite fondé sur la causalité, et un protocole d'auto-correction borné contre le surapprentissage.

---

## 2. Décision d'Architecture

mLoop adopte formellement les quatre principes constitutifs suivants :

### 1. Le Bus d'Artefacts par Handles Opaques (`OpaqueArtifactBus`)
- Tout résultat d'outil, document ingéré, crawl ou extrait de code dépassant le seuil de concision ($> 2\,000$ caractères ou $> 30$ lignes) est immédiatement persisté dans `memory/artifacts/` sous son empreinte immuable SHA-256 (`mloop://artifacts/{sha256}`).
- L'agent ne reçoit dans son invite de contexte qu'un **descripteur compact** contenant :
  - L'identifiant de handle opaque (`handle_id` / URI `mloop://...`) ;
  - Un résumé sémantique concis et la signature de schéma ;
  - La taille en octets et le nombre de lignes ;
  - Un extrait fenêtré de prévisualisation (en-tête de 5 lignes et pied de 5 lignes).
- Si l'agent doit inspecter ou exploiter le contenu, il utilise des outils de projection fenêtrée (`bus.get_slice(start, end)`) ou de recherche ciblée, sans jamais charger l'artefact brut dans la mémoire vive de son prompt.

### 2. La Porte Anti-Fuite de Vérification (`VerificationLeakageGate`)
Toute spécification (Gherkin BDD) ou test unitaire (pytest) généré par un agent doit obligatoirement franchir la porte anti-fuite évaluant quatre critères fondamentaux :
- **Critère 1 (Black-Box Strict)** : Interdiction formelle d'assertion sur des attributs ou méthodes privées (`obj._internal`). Le test doit interroger exclusivement l'interface publique contractuelle.
- **Critère 2 (Anti-Tautologie Mocks)** : Interdiction formelle de comparer la valeur de sortie avec une valeur codée en dur directement injectée dans le mock au sein du corps du même test (`assert actual == expected_mock`).
- **Critère 3 (Invariant Causal Métier)** : Les assertions doivent valider un état persistant, un retour fonctionnel ou une transition d'invariant métier, et non un simple effet collatéral éphémère (ex: message de log console).
- **Critère 4 (Isolation d'État Pur)** : Chaque suite de test doit garantir une isolation totale et une réinitialisation de l'état (fixtures de nettoyage, bases mémoire dédiées).

### 3. Le Garde-Fou de Simplicité & Anti-Surapprentissage (`SimplicityGuard`)
- **Évaluation Pré-Conception du Risque (Heuristic Budget)** :
  Avant toute génération de code, le système évalue la complexité de la demande. Pour une demande de portée unitaire ou corrective, un plafond strict est imposé : **maximum 3 fichiers modifiés, maximum 150 lignes de code ajoutées, interdiction de créer de nouveaux packages ou d'importer de nouvelles dépendances tierces**.
- **Auto-Correction Post-Conception (Single-Shot Pruning)** :
  Si l'implémentation générée dépasse le budget alloué ou crée des indirections superflues, une passe unique d'auto-correction est déclenchée pour simplifier le code et converger vers le diff minimal viable.

### 4. Découverte de Proxys Causaux par Deep Search (`CausalProxyDiscovery`)
- En cas de spécification utilisateur incomplète ou ambiguë lors du cadrage (Drill/Grill), mLoop formule des hypothèses de signaux et interroge son moteur `deep-search`.
- Le moteur applique une distinction stricte entre **Signaux Directs** (présents dans le code et la base SSOT locale) et **Proxys Causaux** (spécifications de référence, RFCs, patterns reconnus).
- Une pondération préférentielle **$5\times$** est appliquée aux sources faisant autorité institutionnelle ou technique officielle.

---

## 3. Conséquences

* **Positives** :
  - Confinement strict de l'empreinte mémoire des invites de prompt, autorisant des exécutions multi-agents quasi-illimitées sans saturation contextuelle.
  - Fiabilité drastique des suites de tests automatisées, éliminant les faux positifs tautologiques.
  - Production systématique d'un code sobre, modulaire et sans sur-ingénierie.
* **Neutres / Légères Contraintes** :
  - Nécessite un appel d'outil supplémentaire (`get_slice`) lorsqu'un agent doit inspecter les lignes intermédiaires d'un artefact volumineux.
  - Rejet immédiat par la porte des tests qui contournent l'encapsulation objet.
