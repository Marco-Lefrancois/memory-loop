# Manifeste Qualité Gherkin - mLoop Standard

L'objectif de ce standard est de garantir que chaque récit (Story) dispose d'une couverture de test exhaustive et non-spéculative, permettant une validation fonctionnelle et technique sans ambiguïté.

## Les 4 Piliers Obligatoires de Couverture

Tout bloc Gherkin dans un récit mLoop **doit** couvrir les quatre catégories suivantes :

### 1. Le Chemin Nominal (Happy Path)
*   **Objectif** : Valider le fonctionnement idéal.
*   **Focus** : Succès de la transaction, persistance des données, affichage correct des informations.
*   **Exemple** : Finalisation réussie avec toutes les pré-conditions remplies.

### 2. Les Exceptions Métier (Business Rules)
*   **Objectif** : Valider le respect des règles RM-REC-XXX ou autres règles métier.
*   **Focus** : Rejets typés (HTTP 409/400), messages d'erreur contextualisés, blocages de boutons.
*   **Exemple** : Écart de shipment hors seuil, absence de contrôle qualité requis.

### 3. Les Cas Limites Techniques (Edge Cases)
*   **Objectif** : Valider la robustesse du système face aux aléas techniques.
*   **Focus** : Idempotence, Transactional Outbox, perte de connectivité (Frontend), timeouts.
*   **Exemple** : Doublon de requête avec la même clé, échec de publication vers l'inventaire.

### 4. Le Comportement UX & Observabilité (UX pour FE, Traces pour BE)
*   **Objectif** : Valider l'expérience utilisateur et les transitions d'état de l'interface (Frontend), ou la traçabilité et l'observabilité système (Backend).
*   **Focus Frontend** : Feedback visuel (couleurs, spinners, toasts), redirection automatique, états de contrôle grisés.
*   **Focus Backend** : Retour structuré, codes HTTP explicites, identifiants de corrélation de transaction et journalisation dans les tables de logs/audit.
*   **Exemple (FE)** : Redirection vers l'accueil après succès avec un toast vert de confirmation.
*   **Exemple (BE)** : La réponse inclut l'identifiant unique de transaction et le journal système (Logs) consigne l'opération et son auteur.

## Directives de Rédaction & Propreté (Anti-Pollution)

1.  **Langue** : Français technique professionnel.
2.  **Précision** : Éviter le jargon vague ("ça marche"). Utiliser des termes précis ("État FINALISEE", "HTTP 409").
3.  **Lien vers le savoir** : Chaque scénario doit, si possible, faire écho à une règle métier (`RM-XXX`) citée plus haut dans le récit.
4.  **Isolation** : Un scénario = une intention claire. Ne pas tester 5 règles métier dans un seul scénario.
5.  **Pureté du Titre de Fonctionnalité** : La ligne `Fonctionnalité:` contient **exclusivement le titre métier pur**. Ne JAMAIS inclure d'identifiants entre parenthèses comme `(REC-007 / COUVBOIRE-736)`.
6.  **Nettoyage des Commentaires d'Échafaudage** : Ne JAMAIS conserver les commentaires d'en-tête (`# PILIER 1 : CHEMIN NOMINAL`, `# PILIER 2...`) dans le bloc Gherkin final. Ces marqueurs sont uniquement des aides à la réflexion pendant le premier jet ; le résultat final doit consister uniquement en des scénarios purs (`Scénario: ...`).
