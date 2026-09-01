# ADR-0325 : Signature Lexicale & Garde-fou Intégrité Tokenizer

**Statut** : Accepté  
**Date** : 18 août 2026  
**Auteurs** : Équipe mLoop & Co-Architecte Agentique  
**Domaine** : Interopérabilité Multi-Agents, Sécurité des Handoffs, Normalisation Unicode, Prévention du Syndrome de Babel  

---

## 1. Contexte et Problématique

Dans les chaînes de traitement multi-agents (ex: Orchestrator ➔ Plan ➔ Build / Herdr Worker ➔ Sentinel), le partage de représentations (tokens, prompts enrichis, EvidencePacks JSON, embeddings) est exposé au **« Syndrome de Babel Silencieux »** (*Silent Babel Drift*) :

1. **La Non-Détection des Incompatibilités Lexicales** :
   Une inadéquation de vocabulaire entre deux modèles ne lève aucune exception Python. Elle produit un texte superficiellement fluide et grammaticalement correct mais sémantiquement faux ou inverse de la directive d'origine (*Confidently Fluent Nonsense*).
2. **La Pollution par Fuite de Tokens de Contrôle (*Role Hijacking*)** :
   Les délimiteurs de tours de rôle propres aux différents formats (`<|im_start|>`, `<|im_end|>`, `[INST]`, `<start_of_turn>`) injectés sans neutralisation passive peuvent tromper le parser du modèle aval.
3. **La Décomposition Unicode Silencieuse (NFC vs NFD)** :
   Les systèmes d'exploitation et tokenizers gèrent les caractères accentués français de façon disparate, altérant les représentations sous-jacentes.

---

## 2. Décisions Architecturales

Nous actons l'intégration du moteur **`LexicalIntegrityGuard`** (`src/utils/lexical_guard.py`) et son ancrage obligatoire dans le protocole de pré-vol `vibe-check` :

### A. Empreinte de Calibration Déterministe (*Rosetta Canary Hash*)
* Une phrase étalon canonique immuable est soumise au calcul d'intégrité :
  `"mLoop SSOT: Règles RM-01 & isolation d'état. BPE-Check [!NOTE] 🚀"`
* Le hash SHA-256 tronqué (`canary_hash`) sert de sceau d'intégrité lexicale partagée.

### B. Normalisation Unicode Stricte (NFC Enforced)
* Tout transfert de données d'un EvidencePack, d'un fichier OKF ou d'un prompt inter-agents est converti en **Unicode NFC (Canonical Composition)**.

### C. Barrière de Neutralisation des Balises de Contrôle (*Control Token Shield*)
* Détection stricte et échappement automatique de tous les délimiteurs sensibles (`<|im_start|>`, `<|im_end|>`, `[INST]`, etc.) pour garantir leur transit passif en tant que données brutes.

### D. Intégration Native dans `vibe-check`
* La commande `python src/swarm.py vibe-check --project <nom>` intègre le contrôle `Check 6 : Intégrité Lexicale & Signature de Vocabulaire`.

---

## 3. Conséquences

### Positives
* **Zéro Inversion Silencieuse de Règle** : L'adhésion sémantique entre modèles de différentes tailles est verrouillée.
* **Sécurité Anti-Injection de Rôles** : Les balises de contrôle sont neutralisées avant d'atteindre le prompt d'un worker.
* **Compatibilité Multi-Runtimes** : Standardisation parfaite entre les formats Windows (CRLF/NFC), Linux (LF) et les tokenizers hétérogènes.

---

## 4. Références & Alignement

* **Article de Référence** : Towards Data Science — *« How to Utilize OKF Efficiently to Enable Knowledge Exchange Among LLMs »* (Août 2026)
* **ADR Associés** :
  - `ADR-002` : OKF Standard pour mLoop
  - `ADR-0310` : Vibe Code Common Sense & Session Resume
  - `ADR-0325` : Semantic Chunking et Extraction Documentaire Agentique
  - `ADR-0326` : Moisson d'Evals et Moniteur de Contexte
