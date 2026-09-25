# Gates: Validation du Pipeline Python & Runnable Gates
OWNS: src/core/gates.py, src/pipelines/gatekeeper.py

Scope: Vérification de l'intégrité du moteur de portails exécutables et de l'arbre Depth Tree

- [x] G1: Moteur core gates.py opérationnel
  CHECK: python -m unittest tests/test_gates_engine.py
  EXPECT: OK
  CWD: ../..
  EVIDENCE: met | shell:pwsh | exit:0 | out:sha256:26b530f8 (110B) | path:5450a8 (48 dirs)

- [x] G2: Commande CLI gates disponible dans le registre
  CHECK: python -c "from src.commands._registry import COMMANDS; print('GATES_REGISTERED' if 'gates' in COMMANDS else 'MISSING')"
  EXPECT: GATES_REGISTERED
  CWD: ../..
  EVIDENCE: met | shell:pwsh | exit:0 | out:sha256:69264ec2 (17B) | path:5450a8 (48 dirs)

- [x] G3: Revue sémantique et documentaire du standard ADR-0341
  EVIDENCE: met | reviewed by orchestrator
