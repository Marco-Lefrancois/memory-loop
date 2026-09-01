# 📜 Standard mLoop — Protocole d'Enrichissement des Scans OneTrust

**Référence** : `standards/protocols/scan-enrichment-protocol.md`  
**Statut** : Standard officiel mLoop  
**Sujet** : Normalisation, enrichissement technique/juridique et export des scans d'applications mobiles OneTrust.

---

## 1. Principes Généraux

L'enrichissement des scans OneTrust vise à transformer les fichiers Excel bruts d'inventaire automatisé en **livrables d'analyse d'impact technique et juridique**.

Chaque scan enrichi doit répondre aux 3 règles fondamentales :
1. **Traçabilité Totale (Zero Silent Reclassification)** : Tout changement de catégorie par rapport à la catégorie brute du scanner OneTrust doit être marqué comme reclassement (`reclassed = True`) et apparaître explicitement dans l'onglet dédié.
2. **Double Niveau d'Export (Sanitization)** :
   - **Mode `Clean` (Client & Légal)** : Français pur, exempt de tout jargon interne, d'identifiants de stories (`US-12`) ou de codes d'ADR bruts (`ADR-008`).
   - **Mode `GOLD` (Interne mLoop)** : Conservation de la traçabilité avec pointeurs vers les ADR, User Stories et EvidencePacks JSON (`memory/evidence/`).
3. **Strict Conformité aux Directives Métier** : Alignement rigoureux avec la Loi 25 (Québec), le RGPD, le Principe de Blindage Natif et Google Consent Mode v2 (Mode BASIC).

---

## 2. Structure Normée des Fichiers Excel Enrichis

Tout fichier Excel enrichi produit selon ce protocole comporte **3 composants obligatoires** :

### 2.1 L'Onglet `Overview` *(1ʳᵉ Position)*
* Titre officiel et métadonnées de l'analyse (Application, Bannière, Date, Plateforme, Modèle).
* Compteurs globaux : Nombre total de SDKs, Nombre de Reclassements.
* Tableau de distribution des SDKs par Catégorie Recommandée.
* Liste des textes de référence et normes juridiques applicables.

### 2.2 L'Onglet `Reclassifications` *(2ᵉ Position — Obligatoire)*
* Vue centralisée regroupant **uniquement les packages ayant fait l'objet d'un reclassement**.
* En-têtes (9 colonnes) :
  1. `Name`
  2. `Package Name`
  3. `Vendor`
  4. `Catégorie Originale (Scanner)`
  5. `Catégorie Recommandée`
  6. `Raison du Reclassement`
  7. `Règle de Conformité Applicable`
  8. `Impact CMP OneTrust`
  9. `Action Requise PO/Légal`

### 2.3 Les Onglets de Détails et Consolidation
* Feuilles thématiques par catégorie (`C0001 Strictly Necessary`, `C0002 Performance`, `C0003 Functionality`, `C0004 Targeting-Advert`).
* Feuille consolidée **`All SDKs (Consolidated)`** contenant la totalité des 14 colonnes normées.

---

## 3. Matrice des 14 Colonnes Normées

| # | Nom de la Colonne | Directives de Rédaction |
|:---:|:---|:---|
| **1** | `Name` | Nom usuel du SDK / package. |
| **2** | `Package Name` | Identifiant exact (`com.google.firebase...`, Pod, DLL). |
| **3** | `Vendor` | Éditeur officiel (Google, Apple, Microsoft, etc.). |
| **4** | `Version` | Version détectée ou `N/A`. |
| **5** | `Category Originale` | Libellé exact de la catégorie issue du scan OneTrust d'origine. |
| **6** | `Description Originale` | Description brute fournie par OneTrust. |
| **7** | `Catégorie Recommandée` | `Strictly Necessary (C0001)`, `Performance (C0002)`, `Functionality (C0003)` ou `Targeting/Advertising (C0004)`. |
| **8** | `Description Spécifique & Utilité Metro` | Rôle réel du composant dans l'application mobile de la bannière. |
| **9** | `Collecte PII` | Explicitation des données identifiantes collectées (AAID, IDFV, FCM Token, UserID, ou `Non`). |
| **10** | `Collecte Géolocalisation` | Indication claire (`Non`, GPS précis, ou approximation réseau). |
| **11** | `Profiling Utilisateur` | Indication de suivi comportemental ou de ciblage marketing. |
| **12** | `Référence Technique Officielle (Légal)` | Lien HTTPS public vers la documentation officielle du fournisseur (preuve pour le Légal). |
| **13** | `Justification Légal & Conformité CMP` | Argumentaire d'exonération sous C0001 ou d'encadrement par la CMP. |
| **14** | `Directives PO & Dev` | Actions techniques concrètes si refus du consentement par l'utilisateur. |

---

## 4. Règle d'Équivalence de Mapping (Nom C# .csproj vs Nom Natif Scan)

Lorsque le scanner OneTrust inspecte le binaire compilé (APK/IPA), il détecte les noms de packages Java/iOS natifs (ex: `com.google.firebase.analytics`), tandis que les développeurs travaillent avec des wrappers NuGet C# (ex: `Plugin.Firebase.Analytics`).

Le protocole impose d'afficher explicitement dans la colonne **`Description Spécifique & Utilité Metro`** le mapping sous la forme :  
`[Package Natif Scan: <nom_natif>] ➔ [Package C# .csproj: <nom_package_nuget> (<projet.csproj>)]`

Exemples :
- **Firebase Messaging** : `[Package Natif Scan: com.google.firebase.messaging] ➔ [Package C# .csproj: Plugin.Firebase.CloudMessaging (Food.Application.csproj)]`
- **AdMob** : `[Package Natif Scan: com.google.android.gms.ads] ➔ [Package C# .csproj: AUCUN (Non référencé dans .csproj - Dépendance transitive)]`

---

## 4. Charte Graphique & Visual Formatting (openpyxl)

* **En-têtes** : Fond Bleu Nuit (`#1F497D`), Texte Blanc Gras (`#FFFFFF`), Alignement centré avec renvoi à la ligne.
* **Cellules Reclassées** : Fond Rose Accentué (`#FFC7CE`), Texte Rouge Foncé (`#9C0006`) sur la catégorie recommandée.
* **Cellules Non Reclassées** : Fond Vert Clair (`#C6EFCE`), Texte Vert Foncé (`#006100`).
* **Bordures & Alignement** : Bordures minces (`thin`), alignement haut avec renvoi à la ligne automatique (`wrap_text=True`).
* **Volet Fige** : Figer la 1ʳᵉ ligne (`freeze_panes = "A2"`).
* **Filtres Automatiques** : Activer le filtre auto sur toutes les colonnes (`auto_filter.ref`).

---

## 5. Règle de Sanitization (Mode Clean vs Mode GOLD)

| Élément | Export Client (`Clean`) | Export Interne (`GOLD`) |
|:---|:---|:---|
| **Pointeurs ADR** | Traduits en normes publiques (ex: *"Principe de Blindage Natif"*) | Format direct (ex: `ADR-008`, `ADR-005`) |
| **Clés de Stories** | Purgées ou traduites en consignes PO | Format direct (ex: `US-12`, `US-10`) |
| **Mentions mLoop/Swarm** | Purgées des textes et métadonnées | Conservées dans le rapport Markdown |

---

*Protocole mLoop — Validé le 12 août 2026.*
