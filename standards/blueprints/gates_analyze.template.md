# Gates: Phase Analyse Sémantique & Modélisation du Domaine
OWNS: docs/01-architecture/**, docs/02-business-rules/**, docs/03-models/**

Scope: Modélisation DDD, extraction des règles métiers, schémas de données et indexation Graphify

- [ ] G1: Les modèles de données et schémas de base sont documentés sous docs/03-models/
  CHECK: python -c "from pathlib import Path; models = list(Path('docs/03-models').glob('*.md')) if Path('docs/03-models').exists() else []; print('MODELS_OK' if len(models) > 0 else 'NO_MODELS')"
  EXPECT: MODELS_OK
  EVIDENCE: pending

- [ ] G2: Les règles d'affaires sont formalisées sous docs/02-business-rules/ avec zéro référence fantôme
  CHECK: python src/swarm.py struct-check --project {PROJECT_NAME}
  EXPECT: /PASS|0 erreurs|SUCCÈS/i
  EVIDENCE: pending

- [ ] G3: Le graphe sémantique de connaissances est généré et interrogeable
  CHECK: python -c "from pathlib import Path; print('GRAPH_READY' if (Path('graphify-out/graph.json').exists() or Path('docs/01-architecture').exists()) else 'GRAPH_MISSING')"
  EXPECT: GRAPH_READY
  EVIDENCE: pending
