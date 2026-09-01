# ADR-0101 : Ingestion MarkItDown Local & Conversion Sémantique
## Statut : Accepté (Série 01xx - Ingestion & Conversion)

---

## 1. Contexte

Les architectures d'ingestion dépendant de serveurs RAG distants ou d'Open Notebook posaient des contraintes d'infrastructure, de dépendances d'API et de risques de confidentialité. mLoop doit pouvoir ingérer et analyser toute la matière première documentaire en local, de manière 100% autonome et déterministe.

---

## 2. Décision

Nous abandonnons toute dépendance à Open Notebook. Nous imposons le **Pipeline d'Ingestion Local MarkItDown (`markitdown_convert`)** :

```
[reference/] (PDF, DOCX, XLSX, PPTX) ──► [markitdown_convert] ──► [docs/00-ingested/*.md]
```

1. **Extraction Local Pure** : La matière première déposée dans `reference/` est convertie en fichiers Markdown autonomes sauvegardés sous `docs/00-ingested/`.
2. **Registre SHA256 Anti-Doublons** : Avant toute conversion, le registre persistant `memory/ingest_registry.json` et les empreintes SHA256 sont vérifiés pour interdire l'importation en doublon.
3. **Accès Direct Agentique** : Les agents lisent directement les fichiers `.md` générés sous `docs/00-ingested/`, qui sont immédiatement indexés par SQLite FTS5 et cartographiés par Graphify.

---

## 3. Conséquences

- **100% Local & Autonome** : Aucune dépendance vers un serveur RAG externe.
- **Transparence Markdown** : Fichiers lisibles directement par l'humain et l'IA dans l'IDE.
