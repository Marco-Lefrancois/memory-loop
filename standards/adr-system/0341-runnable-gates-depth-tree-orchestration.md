# ADR-0341 : Runnable Gates, Depth Tree Orchestration & Empreintes Déterministes

## 🏛️ Statut
**Accepté** — Standard Normatif mLoop Core Architecture (29 août 2026)

---

## 🎯 Contexte & Problématique
Les agents d'ingénierie logicielle autonomes (LLMs) souffrent d'un biais documenté de complétion prématurée et de paresse (*Agent Laziness*), où un agent déclare une tâche achevée et testée sans avoir exécuté les commandes de vérification ou après avoir ignoré silencieusement des sous-objectifs.

Dans l'écosystème mLoop, les User Stories sont définies selon le standard Gherkin 4 piliers et le score INVEST. Cependant, il manquait une passerelle déterministe entre ces spécifications déclaratives no-code et leur exécution physique infalsifiable par les sous-agents (Herdr workers).

---

## 💡 Décision Architecturale

Nous adoptons les principes de complétion déterministe issus de la méthodologie `unlazy` (v2.1.0) et instituons le standard **Runnable Gates & Depth Tree** au sein de mLoop :

### 1. Séparation Stricte Fonctionnel vs Portails d'Exécution
*   **User Story (`backlog/stories/<JIRA_KEY>.md`)** : Reste 100% no-code, purement fonctionnelle et orientée métier (Gherkin 4 piliers).
*   **Grand Livre de Portails (`backlog/gates/<STORY_ID>.gates.md` ou `GATES.md`)** : Fichier compagnon machine-checked contenant les oracles d'exécution (`CHECK:`, `EXPECT:`, `CWD:`, `EVIDENCE:`, `OWNS:`, `ABANDON:`).
*   **Preuves Cryptographiques (`memory/evidence/<STORY_ID>_evidence.json`)** : Stockage sidecar des empreintes d'exécution SHA-256 sans pollution de la fenêtre de contexte.

### 2. Le Contrat d'Exécution Strict (Double Condition d'Oracle)
Un portail exécutable (*runnable gate*) n'est validé (`met`) que si et seulement si :
1. Le sous-processus démarre et se termine avec un code de retour `0` (`Exit Code == 0`).
2. Le motif `EXPECT:` (texte exact ou expression régulière `/pattern/flags`) est trouvé dans la sortie combinée `stdout + stderr`.

### 3. Économie de Jetons & Empreinte Légère
Pour éviter la saturation de la fenêtre d'attention des agents, la sortie brute n'est jamais persistée dans le grand livre. Le moteur enregistre l'empreinte :
`EVIDENCE: met | shell:<nom> | exit:0 | out:sha256:<hash> (<N>B) | path:<hash> (<N> dirs)`

### 4. Baux de Propriété de Chemins (`OWNS:`) & Vagues de Lancement Scellées
*   Chaque feuille (*leaf*) déclare les chemins relatifs exclusifs qu'elle est autorisée à modifier (`OWNS: src/module/**, tests/module/**`).
*   Le verrouillage atomique (`claim_lease`) interdit toute collision disque entre workers simultanés.
*   Protocole de vague de lancement (*Launch Waves*) : `open` → `start all` → `seal` → `wait` → `return` → `reverify`.

### 5. Re-vérification Parente Obligatoire (`--reverify`)
Lors du moissonnage d'un sous-agent (`worker-harvest`), l'orchestrateur parent ne se fie jamais aux déclarations de l'agent : il réexécute mécaniquement l'ensemble des oracles de la feuille avant d'accorder le statut `VERIFIED`.

### 6. Règle d'Abandon Non-Trompeur (`ABANDON`)
L'abandon d'une exigence impossible (`ABANDON: <id> <raison non-vide>`) constitue une restitution obligatoire (*Handoff Required*) avec code d'erreur `1`, et ne peut jamais être promu en succès silencieux.

---

## ⚖️ Conséquences & Impacts

*   **Positif** : Élimination mathématique de la fausse complétion et des tests simulés.
*   **Positif** : Protection du budget de tokens grâce aux empreintes SHA-256 compactes.
*   **Positif** : Textualisation visuelle claire et temps réel de l'avancement pour l'utilisateur.
*   **Mitigation** : Le linter `gate-lint` prévient la création d'oracles tautologiques (`echo ok`).
