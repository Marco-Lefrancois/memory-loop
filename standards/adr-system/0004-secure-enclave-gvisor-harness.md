# ADR-0004 : Secure Enclave & Harnais gVisor

* **Statut** : SPECULATIVE / TARGET_INFRASTRUCTURE (Spécification de sécurité pour déploiement conteneurisé externe)
* **Date** : 30 Juillet 2026
* **Décideurs** : Équipe Architecture mLoop & Co-Architecte IA
* **Contexte** : Framework Memory Loop (mLoop v2.2.0)

---

## 1. Contexte et Problématique

L'architecture mLoop impose une séparation asymétrique stricte entre :
- **Le Système 2 (Cognition)** : IDE agentique, LLM Cloud, modélisation d'architecture.
- **Le Système 1 (Exécution Physique)** : Scripts Python locaux, modification de fichiers, tests unitaires.

L'exécution directe d'instructions Python arbitraires ou d'outils locaux par le Système 1 présente des risques majeurs : élévation de privilèges, exfiltration de données, duplication de processus non autorisés (*os.fork* / *process shadowing*) et attaques par injection de modules malveillants dans des répertoires inscriptibles (*module hijacking*).

---

## 2. Décision d'Architecture

Il est décidé de s'inspirer des enclaves d'exécution sécurisées de Google Bard/Gemini (gVisor / Borg Sandbox) pour durcir le harnais Système 1 de mLoop.

### A. Interception Sentry & Kernel User-Space (gVisor)
- **Principe** : Tout conteneur ou sandbox d'exécution Système 1 mLoop s'exécute au-dessus du noyau en espace utilisateur **gVisor (Sentry)**.
- **Isolation Syscall** : Sentry intercepte les appels système (syscalls Linux/Windows). Aucun accès direct au noyau de la machine hôte n'est permis.
- **Communication Hors-Bande** : Les télémétries et contrôles de la sandbox transitent par un socket parallèle dédié (`:8888`), séparé des flux `stdin`/`stdout`.

### B. Environnement Sans État (Stateless Runfiles)
- **Herméticité des Fichiers** : Le répertoire utilisateur de travail (`/home/bard` ou équivalent local) est vierge à chaque initialisation d'instance.
- **Extraction Éphémère** : Les dépendances et l'interpréteur sont extraits dans des sous-répertoires temporaires éphémères (`/tmp/*__unpar__.runfiles`).

### C. Recommandations de Durcissement mLoop Anti-Jailbreak
1. **Verrouillage `sys.executable` & Block Fork** : L'interpréteur Python du harnais mLoop est compilé/embrayé sous forme de bibliothèque partagée liée au processus parent, bloquant l'instanciation de sous-processus par duplication de chemin.
2. **Nettoyage Strict du `sys.path` (Anti-Module Hijacking)** : Élagage rigoureux de la variable `sys.path` pour supprimer tout chemin mort (`dead path`) non peuplé ou potentiellement inscriptible.
3. **Obfuscation de l'Environnement** : Masquage des variables système (`BORG_*`, `GVISOR`) pour interdire le *fingerprinting* d'infrastructure par une invite malveillante.
4. **Profil Minimaliste Headless** : Désactivation des dépendances de rendu graphique (Matplotlib, serveurs web Tornado) pour les agents d'analyse pure.

---

## 3. Conséquences

### Positives
* Isolation de niveau militaire empêchant toute évasion de conteneur ou falsification du système hôte.
* Élimination des vecteurs d'attaque par *module shadowing* ou *process fork*.
* Garanties d'étanchéité du Système 1 mLoop.

### Négatives / Risques
* Nécessite le support de gVisor / AppContainer / WSL2 Sandbox sur l'hôte Windows.
