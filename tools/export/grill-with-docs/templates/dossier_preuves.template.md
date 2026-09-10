# 🐣 Session *Grill with Docs* — `<STORY_ID>` (<Titre Fonctionnel Pur>)

---

### 📂 Dossier de Preuves Documentaires (Sources Physiques & Extraits)

#### 1. 🖼️ Maquettes & Notes d'Atelier (SSOT Visuelle)
* **Maquette Principale** : [`docs/05-assets/.../<fichier>.svg`](file:///chemin/vers/fichier.svg) ou [Lien Figma](https://www.figma.com/...)
* **Note d'ajustement UI (Grooming / Cadrage)** : [`reference/.../<image>.jpg`](file:///chemin/vers/image.jpg)
  > 📌 **Ajustement validé** : <Description précise de l'ajustement validé>.

---

#### 2. 🎙️ Extraits de la Transcription d'Atelier / Spécifications
Source : [`docs/00-ingested/.../<doc>.md`](file:///chemin/vers/doc.md)

> **Extrait 1 — <Titre de la Règle> (Lignes X–Y) :**  
> *« <Citation mot-à-mot du texte source> »*  
> ➔ **Fait établi** : <Traduction fonctionnelle concise de la règle métier>.

> **Extrait 2 — <Titre de la Règle> (Lignes X–Y) :**  
> *« <Citation mot-à-mot du texte source> »*  
> ➔ **Fait établi** : <Traduction fonctionnelle concise de la règle métier>.

---

#### 3. 🗄️ Structure de Données (Wiki Azure DevOps & DBML)
* **Sources** : [`docs/00-ingested/.../<spec>.md`](file:///chemin/vers/spec.md)
* **Entités & Champs Clés** :
  ```json
  {
    "id": "UUID",
    "champMetier": "Type (Description)"
  }
  ```

---

### 🎯 Contrat Déclaratif Cible (Profil B / Matrice CTA)
* **Route / Action** : `METHOD /api/...` ou `Composant UI ➔ Action`
* **Comportement attendu** : <Résumé du contrat fonctionnel>.

---

### ❓ Question d'Arbitrage #N pour `<STORY_ID>` (Règle d'Or de l'Interview)

<Contexte précis de l'arbitrage adossé aux faits vérifiés ci-dessus>.

* **Option A (Recommandée — <Motivation Technique>)** : <Description claire de l'option recommandée>.
* **Option B** : <Description de l'alternative>.
* **Option C** : <Description de l'alternative>.

👉 **<Question fermée d'arbitrage / validation> ?**
