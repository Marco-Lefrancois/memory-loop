---
id: MLOOP-110-BE
jira_key: '-'
epic_key: EPIC-11-ERROR-OBSERVABILITY
type: Feature
title: Persistance Rotative des Journaux d'Erreurs du Moteur de Logging mLoop
tags:
- logging
- observability
- error-log
- rotation
- opt-in
- adr-0369
status: SHIPPED
layer: backend
invest_score: 6/6
grill_me: DONE
ttl_cycles: 3
---
# Persistance Rotative des Journaux d'Erreurs du Moteur de Logging mLoop

---

## Description
**En tant qu'** Opérateur / Mainteneur du framework mLoop,
**je veux** que les erreurs capturées par le moteur de logging centralisé soient conservées sur disque de façon durable et bornée lorsque je l'active explicitement,
**afin de** pouvoir diagnostiquer après coup un incident survenu dans un processus non supervisé sans dépendre d'une console encore ouverte.

---

## Contexte & Périmètre

### Contexte Métier
Le moteur de logging centralisé du framework émet aujourd'hui l'intégralité de ses messages vers la sortie standard d'erreur de la console uniquement. Toute erreur capturée par un processus exécuté sans supervision interactive — traitement en arrière-plan, contrôle automatisé pré-opération, synchronisation planifiée — est donc affichée puis irrémédiablement perdue à la fermeture du processus. Ce récit ajoute une voie de conservation durable et bornée des erreurs, activable à la demande, afin de permettre l'analyse post-incident sans altérer le comportement existant tant qu'elle n'est pas explicitement demandée.

### In-Scope
- Ajout d'une voie de journalisation persistante vers un fichier, en complément de la sortie console existante, au sein de la fabrique de logger centralisée.
- Activation strictement volontaire : la persistance reste inactive tant que l'opérateur ne l'a pas explicitement demandée par configuration d'environnement.
- Capture ciblée des seules entrées de niveau erreur et supérieur, indépendamment du niveau d'affichage de la console.
- Bornage automatique de l'espace disque occupé par rotation à la taille, avec conservation d'un historique limité d'archives.
- Écriture des journaux sous le répertoire de mémoire du framework, cohérente avec les autres artefacts de traçabilité.
- Réglage optionnel du seuil de capture, de la taille de rotation et du nombre d'archives par configuration d'environnement, avec des valeurs par défaut sûres ne nécessitant aucun réglage.

### Out-of-Scope
- Convergence des composants utilisant encore un logger non centralisé vers la fabrique commune.
- Remplacement des écritures directes en console par de la journalisation structurée dans le reste du code source.
- Audit et correction des captures d'exception silencieuses existantes.
- Toute interface de visualisation, de filtrage ou d'exploration des journaux persistés.
- Envoi ou réplication des journaux vers un service distant ou un agrégateur externe.
- Toute commande dédiée de purge ou de rotation manuelle, la rotation automatique étant seule retenue.

---

## Critères d'acceptation

### Opérations Métier & Logique Backend

#### 1. Activation Volontaire de la Persistance des Erreurs
* **Entrée Métier** : Demande d'activation de la persistance exprimée par l'opérateur via la configuration d'environnement du framework.
* **Règles d'admissibilité & Validation** : En l'absence de demande explicite, aucune voie de persistance n'est créée et le comportement console reste strictement identique à l'existant.
* **Traitement & Algorithme Métier** : Lorsqu'elle est demandée, une voie de journalisation persistante est adjointe à la voie console, ciblant les entrées de niveau erreur et supérieur, avec un emplacement de sortie déterminé sous le répertoire de mémoire du framework.
* **Résultat Métier & Mutations** : Les erreurs émises après activation sont écrites de façon durable dans le fichier de journal et restent consultables après la fin du processus émetteur.
* **Cas de Rejet Métier** : Si l'emplacement de sortie ne peut être créé ou n'est pas accessible en écriture, la persistance est abandonnée sans interrompre l'exécution ni supprimer la sortie console.

#### 2. Bornage Automatique de l'Espace Occupé
* **Entrée Métier** : Accumulation progressive d'entrées d'erreur dans le fichier de journal actif.
* **Règles d'admissibilité & Validation** : La taille du fichier actif ne doit jamais croître indéfiniment ; un historique d'archives limité est conservé.
* **Traitement & Algorithme Métier** : Lorsque le fichier actif atteint le seuil de taille configuré, il est archivé et un nouveau fichier actif est ouvert ; au-delà du nombre d'archives conservées, la plus ancienne est supprimée automatiquement.
* **Résultat Métier & Mutations** : L'espace disque total occupé par l'ensemble des journaux reste plafonné sans intervention manuelle.
* **Cas de Rejet Métier** : Aucun ; la rotation est un mécanisme automatique et silencieux du point de vue métier.

---

## Règles d'affaires

- **Persistance Strictement Volontaire** : La conservation sur disque des erreurs n'existe que si l'opérateur l'a explicitement activée ; l'état par défaut du framework est inchangé.
- **Ciblage sur les Erreurs** : Seules les entrées de niveau erreur et supérieur sont persistées, indépendamment du niveau d'affichage retenu pour la console.
- **Espace Disque Plafonné** : Le volume total des journaux est borné par rotation à la taille et conservation d'un historique limité, sans purge manuelle.
- **Non-Régression du Cœur** : L'ajout de la persistance ne modifie ni la signature ni le comportement des points d'appel existants du moteur de logging.
- **Confinement Local** : Les journaux ne sont jamais transmis hors de la machine locale.
- **Dégradation Non Bloquante** : Une impossibilité d'écrire sur disque n'interrompt jamais l'exécution et préserve la sortie console.

---

## Références

### 2. Spécifications & Modèles de Données SSOT
- 📜 **ADR d'Architecture** : [ADR-0369 — Standards de Robustesse Python Senior](../../standards/adr-system/0369-standards-robustesse-python.md)
- 📜 **ADR d'Architecture** : [ADR-0362 — Zero-Bloat & Gouvernance de l'Écosystème](../../standards/adr-system/README.md)

---

## Contrats UI & API Backend → Profil B

### Matrice des Contrats API

> **Contexte** : Ce récit implémente une infrastructure de logging interne (pas d'API HTTP exposée). Les interfaces internes du module `src.utils.logger` sont documentées ci-dessous. Conformément à ADR-0319, l'absence de routes HTTP est consignée via la question ouverte **OQ-110-01**.

| Méthode | Route | Finalité |
|:---|:---|:---|
| `get_logger` | `src.utils.logger:get_logger` | Factory retournant un logger configuré (console + fichier rotatif si activé) |
| `MLoopLoggerAdapter.error` | `src.utils.logger:MLoopLoggerAdapter.error` | Log ERROR avec contexte structuré + stack trace optionnelle |
| `RotatingFileHandler` | `logging.handlers:RotatingFileHandler` | Fichier rotatif 5Mo/5 backups (errors.log) + 10Mo/3 backups (mloop.log) |

**Question Ouverte (Exemption ADR-0319)** :
- **OQ-110-01** : Ce récit implémente une infrastructure de logging interne (pas d'API HTTP). Les interfaces sont des appels de fonction Python internes, pas des routes HTTP. La matrice ci-dessus documente les interfaces internes pour la traçabilité. **[API de soumission à définir]**

**Variables d'environnement de configuration** :
- `MLOOP_LOG_PERSIST=1` — Active la persistance fichier (défaut: 0)
- `MLOOP_LOG_DIR` — Répertoire de sortie (défaut: `memory/logs/`)
- `MLOOP_ERROR_LOG_MAX_BYTES` — Taille max errors.log (défaut: 5242880 = 5Mo)
- `MLOOP_ERROR_LOG_BACKUP_COUNT` — Nombre d'archives errors.log (défaut: 5)
- `MLOOP_MAIN_LOG_MAX_BYTES` — Taille max mloop.log (défaut: 10485760 = 10Mo)
- `MLOOP_MAIN_LOG_BACKUP_COUNT` — Nombre d'archives mloop.log (défaut: 3)

---

## Scénarios de test

```gherkin
# language: fr
Fonctionnalité: Persistance Rotative des Journaux d'Erreurs du Moteur de Logging mLoop

  # CHEMIN NOMINAL (Happy Path & Persistance)
  Scénario: Une erreur émise après activation reste consultable après la fin du processus
    Étant donné un opérateur ayant explicitement activé la persistance des journaux
    Et un processus du framework qui rencontre une erreur avec sa trace complète
    Quand le processus se termine
    Alors l'erreur demeure consultable dans le fichier de journal persistant
    Et la trace d'exception associée y figure intégralement

  # EXCEPTIONS & REJETS MÉTIER (Règles d'affaires)
  Scénario: Aucune persistance n'est créée tant qu'elle n'est pas explicitement demandée
    Étant donné un framework dont la persistance des journaux n'a pas été activée
    Quand un composant émet une erreur
    Alors aucun fichier de journal n'est créé sur le disque
    Et le message d'erreur reste affiché sur la console comme auparavant

  # RÉSILIENCE TECHNIQUE & MODE DÉGRADÉ (Robustesse, Non-Régression)
  Scénario: Emplacement de sortie inaccessible sans interruption de l'exécution
    Étant donné une persistance activée mais un emplacement de sortie non accessible en écriture
    Quand un composant émet une erreur
    Alors l'exécution du processus se poursuit sans interruption
    Et la sortie console des erreurs reste assurée

  # UX, OBSERVABILITÉ & EMPTY STATE (Rotation, Bornage, Ciblage)
  Scénario: Bornage automatique de l'espace et ciblage sur les erreurs
    Étant donné une persistance activée accumulant de nombreuses entrées d'erreur
    Quand le fichier de journal actif atteint le seuil de taille configuré
    Alors le fichier est archivé et un nouveau fichier actif est ouvert
    Et le nombre d'archives conservées reste limité à l'historique configuré
    Et les entrées de niveau inférieur à l'erreur ne sont pas persistées
```
