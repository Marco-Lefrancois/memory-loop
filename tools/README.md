# 🛠️ Boîte à Outils Transverse — Memory Loop (Dev Tools)

Bienvenue dans l'index technique de la boîte à outils de **Memory Loop**. Ce répertoire regroupe l'ensemble des scripts utilitaires, de diagnostic, et de monitoring transverses mis à disposition des développeurs et des agents du swarm.

---

## 🗂️ Catalogue des Outils Disponibles

| Outil / Script | Description | Commande d'appel | Documentation |
| :--- | :--- | :--- | :---: |
| **`archify`** | Générateur et validateur de diagrammes d'architecture interactifs (HTML standalone, zoom SVG, vues animées). | `python tools/archify/archify_runner.py` | [README.md](archify/README.md) |
| **`budget`** | Suivi en temps réel de votre budget IA et de la consommation de votre clé LiteLLM (Nmédia Cloud). | `python tools/budget/check_budget.py` | [README.md](budget/README.md) |
| **`drawdb`** | Modélisation et conversion des bases de données relationnelles (Markdown, SQL, DrawDB). | `python src/swarm.py drawdb` | - |
| **`hooks`** | Script d'installation du hook Git post-commit (Auto-Healing Graphify). | `python tools/hooks/install_git_hooks.py` | - |
| **`jira`** | Suite complète d'outils Jira (Importation, conversion Markdown, inspection, recherche). | `python tools/jira/pull_jira.py` | - |
| **`office`** | Manipulations chirurgicales de fichiers Office (Word, Excel, PowerPoint sans Office). | `python tools/office/office_tool.py` | - |

---

## 💡 Bonnes Pratiques d'Ajout d'Outil

Lorsque vous ajoutez un nouvel utilitaire dans le répertoire `tools/` :

1. **Cloisonnement** : Créez un sous-dossier dédié pour votre outil (ex: `tools/mon-outil/`).
2. **Autonomie** : Votre script doit être autonome, typé et charger les variables d'environnement requises depuis le fichier `.env` de la racine du dépôt (via `Path(__file__).parent.parent.parent / ".env"` si nécessaire).
3. **Indexation** :
   - Ajoutez une courte ligne de documentation dans ce fichier central `tools/README.md`.
   - Fournissez un fichier `README.md` local dans le dossier de votre outil décrivant son usage précis et ses spécifications techniques.
4. **Graphe Vivant** : Exécutez `python loop.py ingest --project <votre-projet>` pour que `Graphify` indexe automatiquement votre nouvel outil et le rende disponible pour les agents du swarm.
