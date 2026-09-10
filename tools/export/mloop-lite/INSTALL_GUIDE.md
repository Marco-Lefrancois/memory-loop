# 🛠️ Guide d'Installation de l'Écosystème d'Ingestion mLoop Lite

> **Guide officiel pour Windows (10/11) & MacOS**  
> Ce guide vous permet d'installer en quelques minutes tous les outils nécessaires pour que votre mLoop Lite puisse ingérer automatiquement des **PDFs**, des **fichiers Microsoft Office (.docx, .xlsx, .pptx)**, des **pages web** et des **documents numérisés (OCR)**.

---

## ⚡ Méthode 1 : Installation Automatique en 1 Clic (Recommandée)

Si vous êtes sous Windows, double-cliquez simplement sur :
👉 **`setup.bat`** (ou lancez `powershell -ExecutionPolicy Bypass -File setup.ps1`)

Ce script :
1. Vérifie si Python est installé (sinon vous guide pour l'installer).
2. Crée un environnement virtuel sécurisé (`.venv`).
3. Installe automatiquement **MarkItDown**, **l'OCR**, le **Crawler Web** et les parsers **Office**.

---

## 🔧 Méthode 2 : Installation Manuelle Pas-à-Pas

### Étape 1 : Installer Python 3.10 ou supérieur
1. Ouvrez un terminal PowerShell et vérifiez si Python est présent :
   ```bash
   python --version
   ```
2. Si Python n'est pas installé, installez-le en 1 commande avec Windows Package Manager :
   ```bash
   winget install Python.Python.3.11
   ```
   > ⚠️ **Important lors de l'installation manuelle** : Cochez impérativement la case **"Add Python to PATH"** !

---

### Étape 2 : Créer un environnement virtuel (Recommandé)
Dans le dossier de votre projet :
```bash
python -m venv .venv
# Sous Windows :
.venv\Scripts\activate
# Sous Mac/Linux :
source .venv/bin/activate
```

---

### Étape 3 : Installer les modules d'ingestion
Lancez la commande suivante :
```bash
pip install -r requirements.txt
```

---

## 📦 Détail des Outils d'Ingestion Intégrés

### 1. 📑 Microsoft MarkItDown (`markitdown`)
* **Formats pris en charge** : `.pdf`, `.docx` (Word), `.xlsx` (Excel), `.pptx` (PowerPoint), `.csv`, `.html`.
* **Fonctionnement** : Convertit fidèlement la structure des documents (titres, tableaux, listes à puces) en Markdown normalisé prêt pour l'indexation FTS5 et l'IA.
* **Commande** : Déposez vos fichiers dans `reference/` et lancez `python mloop.py ingest`. La conversion est automatique !

### 2. 👁️ RapidOCR (`rapidocr_onnxruntime`)
* **Pourquoi cet OCR ?** : 100% autonome, fonctionne en local sur le processeur (CPU) sous Windows sans nécessiter l'installation complexe de binaires externes comme Tesseract OCR.
* **Fonctionnement** : Détecte et extrait le texte des maquettes graphiques (.png, .jpg) et des vieux PDFs numérisés (scans papier) pour les rendre lisibles par le moteur Fact-Search.

### 3. 🌐 mLoop Crawler (`core/crawler.py`)
* **Fonctionnement** : Télécharge n'importe quelle URL (documentation concurrente, article, page client), nettoie le bruit (bannières de cookies, menus de navigation, publicités) et génère un Markdown propre et sourcé dans votre projet.
* **Commande** :
  ```bash
  python mloop.py crawl "https://exemple.com/documentation-api"
  ```

---

## ❓ Foire Aux Questions & Dépannage

* **Erreur `pip n'est pas reconnu`** :  
  Relancez l'installateur Python et choisissez "Modify", puis cochez "pip" et "Add Python to environment variables".
* **Dois-je avoir Microsoft Office installé sur ma machine ?**  
  **NON !** Les librairies Python lisent directement le format OpenXML binaire. Aucune licence ni installation d'Office n'est requise.
* **Que faire avec des fichiers audio / vidéos d'ateliers ?**  
  Passez par un outil de transcription (ex: Teams/Zoom transcription automatique ou Whisper) pour obtenir le fichier `.txt` ou `.vtt`, et déposez-le dans `reference/`.
