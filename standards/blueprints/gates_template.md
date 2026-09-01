# Gates: <Nom de la Tâche ou ID Récit>

OWNS: <chemins_relatifs_autorisés_ex: src/module/**, tests/module/**>

Scope: <Description concise de l'objectif et de la portée de la feuille>

- [ ] G1: <Description de l'issue vérifiable 1>
  CHECK: <commande_exécutable_ex: pytest tests/test_module.py -k test_g1>
  EXPECT: <motif_attendu_ex: 1 passed ou /OK|PASSED/>
  EVIDENCE: pending

- [ ] G2: <Description de l'issue vérifiable 2>
  CHECK: <commande_exécutable_ex: python scripts/verify_schema.py>
  EXPECT: schema valid
  CWD: .
  EVIDENCE: pending

- [ ] G3: <Description d'un portail manuel sans commande shell>
  EVIDENCE: pending

<!--
Règles strictes de rédaction :
- ID unique obligatoire (ex: G1, G2, N1, L1) suivi de deux-points.
- Indenter CHECK, EXPECT, CWD, EVIDENCE avec 2 espaces.
- Pour une gate exécutable, CHECK et EXPECT sont obligatoires.
- Pour un abandon, ajouter à la colonne 1 : ABANDON: G3 <raison explicite non-vide>.
-->
