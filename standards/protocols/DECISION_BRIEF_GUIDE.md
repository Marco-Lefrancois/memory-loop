# Guide Normatif : Protocole « Push-Right » & Briefs Décisionnels (ADR-0368)

- **Statut** : Approuvé (Norme d'Interaction Système 2)
- **Date** : 2026-09-15
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Origine Conceptuelle** : Doctrine « Push Right » & « Brief vs Draft » (Matt Pocock `loop-me`)

---

## 1. Principe Fondateur : Le « Push-Right »

Dans tout cycle d'ingénierie assisté par agents autonomes, **l'attention humaine est la ressource la plus rare et la plus coûteuse**.
Le protocole **Push-Right** impose de reporter toute interruption ou point de contrôle humain (*checkpoint*) le plus loin possible en aval dans le cycle :

```
❌ ANTI-PATTERN (Pollution Cognitive) :
Agent ──(Question floue)──> Humain ──(Réponse)──> Agent ──(Ébauche brute)──> Humain ──> Code

✅ PATTERN PUSH-RIGHT (mLoop / Matt Pocock) :
Agent ──(Ingestion + Recherche + Task Graph + Tests)──> [CHECKPOINT TARDIF] ──(Brief Décisionnel)──> Humain (Approuve en 1 clic)
```

### Règle d'Or
> **« L'opérateur humain lit un Brief, jamais une ébauche brute. »**  
> Un agent ne doit solliciter l'humain que lorsqu'il a préparé l'intégralité du travail exploratoire, calculé le rayon d'impact (*Blast Radius*), exécuté les vérifications déterministes, et formulé une recommandation forte.

---

## 2. Anatomie d'un « Decision Brief »

Tout livrable présenté à un checkpoint de validation (Phase 2 : Plan & Archi, Phase 4 : Validate & QA) doit obligatoirement respecter la structure quintuple suivante :

### 1. Synthèse d'Impact (3 lignes maximum)
- Quel est le problème résolu ?
- Quel composant est modifié et quel est son statut ?
- Risque global évalué : `FAIBLE`, `MODÉRÉ`, `ÉLEVÉ`.

### 2. Rayon d'Impact & Conflits (Blast Radius)
- Nœuds du graphe d'architecture affectés (CodeGraph / Graphify).
- Dépendances transitives ou régressions potentielles.

### 3. Preuves Déterministes Déjà Récoltées
- Résultat des linters AST et des vérifications mécaniques (`deterministic_checks`).
- Résultat des tests de non-régression (`pytest` / `vitest`).
- Preuves d'exécution PTY (`EvidencePack`).

### 4. Arbitrage & Recommandation Forte
- Option A (Recommandée avec justification technique chiffrée).
- Option B (Alternative considérée et motif d'écartement).
- **Interdiction formelle de poser une question ouverte sans proposer de choix argumenté.**

### 5. Pointeur vers l'Actif Clé
- Lien Markdown navigable direct vers l'artefact produit (`file:///...`).

---

## 3. Matrice d'Évaluation de Conformité

| Critère | Rejet Immédiat (Red Flag) | Conforme (Done) |
| :--- | :--- | :--- |
| **Volume de texte** | Plus de 40 lignes de prose non structurée. | Brief synthétique (< 25 lignes) pointant vers l'artefact. |
| **État d'avancement** | Demande d'orientation alors que le code ou l'arbre n'a pas été inspecté. | Travail autonome mené jusqu'au bout du possible avant arbitrage. |
| **Options proposées** | « Que voulez-vous faire ? » sans proposition. | « Nous recommandons l'Option A pour les raisons X, Y. Validez-vous ? » |
| **Preuves fournies** | Affirmations verbales non étayées. | Logs de tests ou assertions déterministes cités avec numéros de lignes. |
