# 🏛️ ADR-0006 : Confinement Hermétique & Structure Multi-Projets (`projects/`)

* **Statut** : ACCEPTÉ (Fondateur)
* **Date** : 2026-09-02
* **Décideurs** : Équipe d'Architecture & Gouvernance Nmédia (Inspiré d'ADR-0330)
* **Domaine** : Sécurité, Confidentialité & Multi-Tenancy

---

## 1. Contexte & Problématique
En agence, les équipes (Analystes d'Affaires, Chargés de Projet, Designers, Développeurs) gèrent simultanément plusieurs mandats clients (ex: *Metro*, *Boire & Frères*, *Canac*).
L'absence d'un cloisonnement physique strict expose l'agence à trois risques majeurs :
1. **Fuite d'informations confidentielles croisées** : L'IA peut malencontreusement citer une règle d'affaires ou un chiffre sensible d'un Client A dans le devis d'un Client B si l'espace documentaire est partagé.
2. **Pollution de la base sémantique (FTS5)** : Une recherche plein-texte mélangerait les passages de documents hétérogènes.
3. **Multiplication chaotique des installations** : Devoir cloner et configurer l'outil mLoop dans 10 dossiers différents sur le disque dur.

---

## 2. Décision Retenue : Le Répertoire `projects/` & Confinement Hermétique

Chaque projet client est strictement confiné dans son propre sous-dossier sous `projects/<nom_projet>/` :

### 2.1 Cloisonnement Étanche à 100%
Chaque sous-projet hérite de son écosystème autonome :
* Son propre fichier d'état et profil : `projects/<nom>/mloop.json`
* Son propre index sémantique SQLite FTS5 : `projects/<nom>/memory/.fact_search_index.db`
* Son propre lexique métier : `projects/<nom>/docs/LEXIQUE.md`
* Son propre registre de questions : `projects/<nom>/docs/QUESTIONS_OUVERTES.md`
* Son propre registre de décisions : `projects/<nom>/docs/adr/`
* Ses propres livrables : `projects/<nom>/deliverables/`

### 2.2 Règle d'Or de l'Assistant IA (*Project Lock*)
* **Interdiction formelle** pour l'agent IA d'accéder, de lire ou de chercher des faits en dehors du sous-dossier du projet actif.
* Toute commande CLI (`mloop ingest`, `mloop plan`, `mloop validate`) cible exclusivement l'espace hermétique du projet via le flag `--project <nom>`.

### 2.3 Mode Hybride (Multi-Projets vs Dépôt Dédié)
* **Mode Multi-Projets (Agence)** : Utilisation du dossier `projects/<nom_client>/` pour centraliser la gestion de plusieurs clients sur une seule machine.
* **Mode Autonome (In-Repo)** : Si mLoop Lite est initialisé directement dans un dépôt Git dédié sans le flag `--project`, les 3 piliers sont placés à la racine du dépôt sans créer de sous-dossier `projects/`.

---

## 3. Conséquences & Bénéfices
* **Sécurité & Confidentialité Absolue** : Aucun risque de contamination croisée entre clients Nmédia.
* **Simplicité Opérationnelle** : Une seule installation de `mLoop Lite` sur la machine du collaborateur permet de gérer tous ses mandats en parallèle.
* **Reproductibilité & Archivage** : Pour archiver ou livrer un projet à un client, il suffit de zipper son sous-dossier `projects/<nom_projet>/`.
