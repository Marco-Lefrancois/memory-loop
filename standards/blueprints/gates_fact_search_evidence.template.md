# Gates: Fact-Search Sémantique & Génération des EvidencePacks (ADR-0326 / ADR-0341)
OWNS: memory/evidence/**, memory/fact_search_log.jsonl

Scope: Validation de la rigueur épistémique Fact-Search, grounding sans hallucination et génération autonome des EvidencePacks JSON

- [ ] G1: Interrogation Fact-Search FTS5 documentée et consignée dans le journal d'audit
  CHECK: python -c "from pathlib import Path; log=Path('memory/fact_search_log.jsonl'); print('LOG_ACTIVE' if log.exists() and len(log.read_text(encoding='utf-8').strip()) > 0 else 'LOG_EMPTY_OR_MISSING')"
  EXPECT: LOG_ACTIVE
  EVIDENCE: pending

- [ ] G2: 100% des citations et sources référencées existent physiquement sur le disque (Zéro Citation Fantôme)
  CHECK: python src/swarm.py vibe-check --project {PROJECT_NAME}
  EXPECT: /Intégrité SSOT & Absence de Références Fantômes : PASS/
  EVIDENCE: pending

- [ ] G3: L'EvidencePack sidecar JSON (<STORY_ID>_evidence.json) et le Dossier de Preuves (<STORY_ID>_fact_dossier.md) sont générés avec empreintes
  CHECK: python -c "from pathlib import Path; import json; evs=list(Path('memory/evidence').glob('*_evidence.json')); docs=list(Path('memory/evidence').glob('*_fact_dossier.md')); valid=(len(evs)>0 and len(docs)>0); print('EVIDENCE_PACK_VALID' if valid else 'EVIDENCE_PACK_MISSING_OR_INVALID')"
  EXPECT: EVIDENCE_PACK_VALID
  EVIDENCE: pending

- [ ] G4: Pureté no-code du récit Markdown préservée (zéro injection de notes IA après Scénarios de test)
  CHECK: python src/swarm.py story-clean --verbose --project {PROJECT_NAME}
  EXPECT: /Nettoyage terminé|conforme/i
  EVIDENCE: pending
