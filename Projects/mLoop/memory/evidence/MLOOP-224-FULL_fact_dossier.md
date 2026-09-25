# 📁 Dossier de Preuves Documentaires — `MLOOP-224-FULL`

- **Récit** : `MLOOP-224-FULL` — Harnais de Certification E2E du Cycle Tooling (Phase -> Plan Visuel -> Build -> Vibe-Check) (EPIC-22-TOOLING-ECOSYSTEM-HARNESS)
- **Établi le** : 2026-09-24 — Cadrage Macro-Grill VALIDÉ
- **dossier_status**: VALIDATED
- **Décisions scellées** : Grill Macro EPIC-22 (Validation E2E par harnais d'intégration complet, zéro échec Vibe-Check) → `ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md`

---

## 1. Sources & Notes d'Atelier

- Épopée : `Projects/mLoop/backlog/epics/epic_tooling_ecosystem_harness.md`
- Fiches de Savoir SSOT : `KN-050`, `KN-051`, `KN-052`
- Normes souveraines : `standards/adr-system/0375-standard-preuve-epistemique-et-tracabilite-radicale.md`, `standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md`
- ADR de cadrage local : `Projects/mLoop/docs/01-architecture/ADR-014_epic-22_integration_operationnelle_ecosysteme_tooling.md`
- Code source ciblé : `tests/test_tooling_lifecycle_e2e.py` (≤ 300L), `standards/protocols/CLI_PIPELINE_GUIDE.md`

---

## 2. Matrice de Résolution des Conflits

| Conflit | Résolution |
| :--- | :--- |
| Test E2E sur projet de production vs Projet témoin | **Isolation Stricte** : Scénario E2E exécuté sur un projet de test isolé (`TestToolingProject`) avec nettoyage rigoureux. |
| Simulation de l'approbation humaine en CI | **Mode Headless Déterministe** : Utilisation du flag `--approve` pour certifier le flux sans boîte de dialogue bloquante. |
| Garantie de non-régression | **Vibe-Check 0 FAIL** : Exécution de la suite complète vérifiant 0 échec et parité SSOT. |

---

## 3. Extraits Verbatim Sourcés

**Extrait 1 — `standards/adr-system/0376-standard-rigueur-zero-blindspot-ecosysteme-mloop.md` :**
```text
"Toute nouvelle fonctionnalité transversale touchant la CLI et les protocoles doit être certifiée par un test E2E et documentée dans le guide CLI officiel."
```
➔ **Fait établi (F-01)** : `CLI_PIPELINE_GUIDE.md` doit intégrer les commandes `mloop opencode`, `mloop plannotator` et `mloop wayfinder`.

**Extrait 2 — `standards/adr-system/0375-standard-preuve-epistemique-et-tracabilite-radicale.md` :**
```text
"La traçabilité radicale impose la création de dossiers de preuves vérifiables avant tout passage au statut READY_FOR_DEV."
```
➔ **Fait établi (F-02)** : Les 5 récits de l'épopée EPIC-22 disposent d'un dossier de preuves au statut VALIDATED.
