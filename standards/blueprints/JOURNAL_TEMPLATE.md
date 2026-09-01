# Context Journal & Lessons Learned

Projet: [Nom du Projet]
Status: Actif
Dernière mise à jour: [YYYY-MM-DD]

---

## 🎯 Mémoire Opérationnelle Vive

- **Feature en cours** : [ID Feature — ex: ST-201]
- **Tâche active** : [Description courte de la tâche physique de Build en cours]
- **Étape A-SPEC** : [ANALYZE | PLAN | BUILD | VALIDATE]

---

## 📝 Décisions & Alignements Validés

<!--
Enregistrer ici les décisions structurantes prises lors des sessions Drill Me (Grill Me).
Format : "- [Date] [Décision]"
-->

- [YYYY-MM-DD] [Décision d'architecture marquante validée lors du Drill Me]

---

## 🛠️ Lessons Learned (Élimination des régressions)

<!--
Enregistrer ici les bugs, erreurs ou pièges rencontrés pendant le Build.
Ces entrées sont lues par l'agent de Build (DevAgent) avant toute modification de src/.
Format strict pour maximiser la lisibilité par l'IA :
-->

### Template d'entrée :
```
**Bug rencontré au cycle [N]** : [Description précise de l'erreur ou de l'exception]
**Fichier concerné** : [chemin/vers/fichier.py]
**Consigne de Résolution** : [Instruction concrète à suivre — ce qui a fonctionné]
**À éviter** : [Ce qui ne fonctionne PAS — pour ne pas répéter l'erreur]
```

---

## 🔗 Références Actives

<!--
Liens vers les artefacts OpenSpec actifs liés au sprint en cours.
Ces liens ne doivent PAS être copiés dans openspec/ — OpenSpec est réservé aux livrables de Build.
-->

- `openspec/changes/[feature-id]/proposal.md` — Intention fonctionnelle
- `openspec/changes/[feature-id]/tasks.md`    — Checklist d'exécution active
