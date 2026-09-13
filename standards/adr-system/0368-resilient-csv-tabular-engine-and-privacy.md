# ADR-0368 : Moteur Tabulaire Résilient & Étanche — Normalisation Multi-Encodage, Streaming à Mémoire Constante, Diff Sémantique et Anonymisation PII

- **Statut** : Approuvé (Constitutionnel)
- **Date** : 2026-09-13
- **Auteurs** : Équipe mLoop Swarm & Co-Architecte Agentique
- **Périmètre** : Ingestion documentaire (`src/pipelines/ingest_agent.py`), Moteur Tabulaire (`src/converters/csv_engine.py`), Outillage CLI (`src/commands/handlers/tooling.py`), Contrôles Vibe-Check (`src/commands/handlers/validation.py`)
- **Autorité** : [ADR-0101](0101-ingestion-markitdown-local.md), [ADR-0102](0102-structure-ssot-dossier-docs.md), [ADR-0326](0326-fact-search-socle-factuel.md), [ADR-0353](0353-agentic-rag-trust-evidence-retrieval-flight-recorder.md), [ADR-0365](0365-harmonisation-symbiotique-skills-et-standard-agent-skills.md)
- **Références R&D** : KDnuggets (*5 Useful Python Scripts to Automate CSV Processing*, Bala Priya C, Sep 2026), RGPD / PIPEDA (Privacy by Design), Python Standard Library `csv.Sniffer` & `csv.DictReader`

---

## 1. Contexte & Problématique

Dans les projets gérés par Memory Loop, les clients fournissent fréquemment des jeux de données de cadrage (exports CRM, inventaires, catalogues d'entités, données financières) sous format `.csv` déposés dans `reference/`.

L'implémentation initiale de l'ingestion (`IngestAgent._ingest_file`) présentait des risques opérationnels et de sécurité majeurs :
1. **Fragilité aux Encodages et Séparateurs** : Une lecture monolithique `filepath.read_text(encoding="utf-8")` lève une `UnicodeDecodeError` dès qu'un fichier Windows CP1252 ou Latin-1 est ingéré, ou injecte des artefacts `\ufeff` (BOM UTF-8). De plus, l'absence de détection des séparateurs (`;` standard Excel européen/québécois, `\t`, `|`) rendait le texte inintelligible.
2. **Saturation Brutale de la Fenêtre de Contexte LLM** : L'injection intégrale de CSV volumineux (plusieurs mégaoctets, dizaines de milliers de lignes) dans `docs/00-ingested/` saturait les prompts d'analyse, diluait l'attention des modèles et augmentait inutilement les coûts de calcul.
3. **Risque Critique de Fuite PII (Privacy Violation)** : Les exports de production contiennent des données personnelles identifiables (noms, emails, salaires, numéros de téléphone). Les envoyer sans anonymisation vers les APIs LiteLLM / Cloud constituait une violation directe des principes de confidentialité.
4. **Cécité Différentielle lors des Synchronisations** : Lors de l'ingestion d'une nouvelle version de fichier (`sync`), aucune détection au niveau des lignes ne permettait aux agents d'identifier ce qui avait été ajouté, supprimé ou altéré entre deux itérations.

---

## 2. Décisions d'Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                     MÂT TABULAIRE & CONFIDENTIALITÉ CSV (ADR-0368)                     │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   1. NORMALISATION UNIVERSELLE (CSVNormalizer)                                         │
│      - Auto-détection de l'encodage (BOM UTF-8, UTF-8, CP1252, ISO-8859-1)            │
│      - Sniffing automatique du délimiteur via csv.Sniffer                              │
│      - Réécriture unifiée en UTF-8 pur avec délimiteur virgule et saut de ligne \n    │
│                                                                                        │
│   2. VALIDATION STRICTE EN STREAMING (CSVSchemaValidator)                             │
│      - Lecture flux ligne à ligne (csv.DictReader) à mémoire constante O(1)           │
│      - Validation de types (int, float, date, email, regex, required)                  │
│      - Rapport d'erreurs d'audit avec numéros de lignes et colonnes en échec           │
│                                                                                        │
│   3. ANONYMISATION PII DÉTERMINISTE (CSVAnonymizer)                                   │
│      - Reservoir Sampling (échantillon représentatif de N lignes sans surcharger RAM)  │
│      - Masquage par SHA-256 tronqué avec sel de projet (Pseudonymisation déterministe) │
│      - Préservation intégrale des relations référentielles (clés étrangères)           │
│                                                                                        │
│   4. DIFF SÉMANTIQUE LIGNE À LIGNE (CSVRowDiff)                                       │
│      - Comparaison par clé primaire ou composite entre Snapshot N et Snapshot N+1      │
│      - Journalisation des lignes ajoutées, supprimées et cellules modifiées            │
│                                                                                        │
│   5. TRANSFORMATION DÉCLARATIVE SÉCURISÉE (CSVColumnTransformer)                      │
│      - Projections, renommages et dérivations de colonnes sans code arbitraire         │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Règle 1 : Ingestion Normalisée Obligatoire dans `IngestAgent`
Tout fichier `.csv` ingéré sous `reference/` DOIT passer par `CSVNormalizer` :
- Nettoyage automatique du BOM et transcodage transparent en UTF-8.
- Sniffing automatique du délimiteur.
- Génération sous `docs/00-ingested/` d'une synthèse Markdown structurée comprenant les métadonnées (nombre de lignes, colonnes, types) et un aperçu propre, plutôt que la copie brute du fichier complet.

### Règle 2 : Sanctuarisation PII par Masquage Déterministe
Avant toute transmission de données tabulaires au contexte des agents ou génération d'EvidencePacks :
- Les colonnes sensibles désignées sont masquées de manière irréversible via un hachage salé : `hash_token = sha256(valeur + project_salt)[:10]`.
- La cohérence relationnelle est strictement conservée : une même valeur d'entrée produit toujours le même jeton masqué au sein du projet.

### Règle 3 : Mémoire Plate Constante via Streaming
Toute manipulation de fichier CSV dans mLoop doit impérativement s'effectuer en streaming via `csv.DictReader` ou échantillonnage réservoir. Le chargement d'un fichier entier en mémoire (`f.read()`, `f.readlines()`) est interdit pour les fichiers tabulaires.

---

## 3. Conséquences & Invariants

- **Positives** : Zéro crash d'ingestion sur les fichiers clients exotiques ; respect strict de la confidentialité et du RGPD ; consommation de tokens LLM maîtrisée et ciblée ; traçabilité granulaire des évolutions de données.
- **Vérification Obligatoire** : Les tests unitaires et fonctionnels sous `tests/test_csv_engine.py` doivent valider avec succès le passage de 100% des formats d'encodage et la consistance du hachage PII.
