# Gates: Phase 1 — Ingestion Documentaire & Exploration (Gate 1)
OWNS: docs/00-ingested/**, docs/05-assets/**, memory/lifecycle_state.json

Scope: Ingestion normalisée de la matière brute (reference/) vers le SSOT Markdown (docs/00-ingested/), optimisation des assets (docs/05-assets/), synchronisation sémantique et respect du Check 13 (ADR-0332, ADR-0335, ADR-0375, ADR-0377).

- [ ] G1: Tous les fichiers bruts de reference/ sont convertis en Markdown sous docs/00-ingested/
  CHECK: python -c "from pathlib import Path; ref=[f for f in Path('reference').glob('*.*') if f.name.lower() != 'readme.md'] if Path('reference').exists() else []; ing=list(Path('docs/00-ingested').glob('**/*.md')) if Path('docs/00-ingested').exists() else []; print('INGEST_OK' if (len(ing) > 0 and len(ing) >= len(ref)) else f'INGEST_PARTIAL: {len(ing)}/{len(ref)}')"
  EXPECT: INGEST_OK
  EVIDENCE: pending

- [ ] G2: Les maquettes visuelles SVG sont optimisées et exemptes de métadonnées éditeur sous docs/05-assets/
  CHECK: python src/swarm.py svg-optimize --input docs/05-assets
  EXPECT: /optimisé|aucun fichier|PASS/i
  EVIDENCE: pending

- [ ] G3: L'index sémantique et la base de recherche SQLite FTS5 sont synchronisés
  CHECK: python src/swarm.py sync --project {PROJECT_NAME}
  EXPECT: /Synchronisation terminée|WikiFix/i
  EVIDENCE: pending

- [ ] G4: Le manifeste canonique d'ingestion (source_manifest.json) et les sidecars LOD (.overview.md) sont présents
  CHECK: python -c "from pathlib import Path; m=Path('docs/00-ingested/source_manifest.json').exists(); print('MANIFEST_OK' if m else 'MANIFEST_MISSING')"
  EXPECT: MANIFEST_OK
  EVIDENCE: pending

- [ ] G5: Règle Check 13 (Anti-Ghost-Bias) : 0 story sous backlog/stories/ et aucun statut engagé avant validation de Gate 1
  CHECK: python -c "from pathlib import Path; stories=[s for s in Path('backlog/stories').glob('*.md') if s.name.lower() != 'readme.md'] if Path('backlog/stories').exists() else []; print('CHECK13_PASS' if len(stories) == 0 else f'CHECK13_FAIL: {len(stories)} premature stories')"
  EXPECT: CHECK13_PASS
  EVIDENCE: pending
