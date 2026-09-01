# Gates: Phase Ingestion Documentaire & Normalisation MarkItDown
OWNS: docs/00-ingested/**, docs/05-assets/**

Scope: Ingestion normalisée de la matière brute (reference/) vers le SSOT Markdown (docs/00-ingested/) et optimisation des assets

- [ ] G1: Tous les fichiers bruts de reference/ sont convertis en Markdown sous docs/00-ingested/
  CHECK: python -c "from pathlib import Path; ref=list(Path('reference').glob('*.*')) if Path('reference').exists() else []; ing=list(Path('docs/00-ingested').glob('*.md')) if Path('docs/00-ingested').exists() else []; print('INGEST_OK' if len(ing) >= len(ref) else f'INGEST_PARTIAL: {len(ing)}/{len(ref)}')"
  EXPECT: INGEST_OK
  EVIDENCE: pending

- [ ] G2: Les maquettes visuelles SVG sont optimisées et exemptes de métadonnées éditeur
  CHECK: python src/swarm.py svg-optimize --input docs/05-assets
  EXPECT: /optimisé|aucun fichier|PASS/i
  EVIDENCE: pending

- [ ] G3: L'index sémantique et la base de recherche SQLite FTS5 sont synchronisés
  CHECK: python src/swarm.py sync --project {PROJECT_NAME}
  EXPECT: /Synchronisation terminée|WikiFix/i
  EVIDENCE: pending
