---
name: svg-ocr
description: Extraction OCR headless Chromium pour maquettes SVG/PNG à texte vectorisé en chemins. Use when extracting text from vectorized SVG mockups, inspecting button labels in headless mode, or reading non-selectable asset text.
---

# 🔍 Skill : Extraction de Texte Maquettes (`/svg-ocr`)

Ce skill régit la **récupération du contenu textuel réel** d'une maquette (`.svg` ou `.png`)
lorsque deux blocages se cumulent :

1. **Texte vectorisé** : le SVG exporté depuis un outil de design (Figma, Sketch, Illustrator)
   encode chaque lettre en tracé `<path>` — il n'existe **aucune** balise `<text>`/`<tspan>`
   lisible. Le parsing texte du SVG renvoie donc zéro libellé exploitable.
2. **Modèle sans vision** : le modèle LLM actif (ex. `claude-opus-4.8`) ne supporte pas
   l'entrée image, donc lire directement le rendu est impossible.

La solution : **rendu headless du SVG en PNG** (Chromium via Playwright global) puis
**OCR par le moteur natif Windows** (`Windows.Media.Ocr`, déjà présent dans `System32`,
aucune installation requise). Le résultat est un texte brut ancré sur la maquette,
utilisable pour établir le **Contrat Visuel (Maquettes = SSOT)** sans jamais l'inventer.

> ⚠️ **Garde-fou Contrat Visuel** : l'OCR sert à établir la **structure et les libellés**
> de référence. Les accents peuvent être mal encodés par l'OCR (`é`➔`�`) — traiter la sortie
> comme une transcription indicative à recouper, jamais comme une chaîne à recopier verbatim
> dans du code. Pour les projets Metro OneTrust, rappeler que les textes affichés proviennent
> du **portail CMP OneTrust** (SDK), pas du code applicatif.

---

## 🛠️ Procédure (2 étapes)

### Étape 1 — Rendu SVG ➔ PNG (Chromium headless)

Prérequis : Playwright + Chromium installés globalement (fourni par le crawler MCP mLoop).
Vérifier : `npm root -g` doit contenir `playwright` et `~/AppData/Local/ms-playwright/chromium-*`.

Le script réutilisable est fourni : [`render_svg.js`](./render_svg.js).

```powershell
# NPM_GLOBAL_ROOT permet à Node de résoudre le module playwright global
$env:NPM_GLOBAL_ROOT = (npm root -g).Trim()
node ".agents/skills/svg-ocr/render_svg.js" `
  --src "C:\chemin\vers\dossier_svg" `
  --out "C:\Users\<user>\AppData\Local\Temp\opencode\ocr_work" `
  --files "cookies-consent-improved.svg,privacy-preferences-center.svg"
```

> Le SVG est injecté dans une page HTML (`display:inline-block`, `margin:0`) et capturé via
> `element.screenshot()` sur la balise `<svg>` — respecte les dimensions natives du viewBox.
> `deviceScaleFactor: 2` améliore la netteté pour l'OCR.

### Étape 2 — OCR natif Windows (Windows.Media.Ocr)

Le script réutilisable est fourni : [`ocr_png.ps1`](./ocr_png.ps1).

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File ".agents/skills/svg-ocr/ocr_png.ps1" `
  -Files "C:\...\ocr_work\cookies-consent-improved.png,C:\...\ocr_work\privacy-preferences-center.png"
```

La sortie est le texte reconnu, ligne par ligne, préfixé du nom de fichier.

---

## 🧭 Arbre de décision (quel outil pour lire une maquette ?)

| Situation | Outil |
| :--- | :--- |
| SVG avec balises `<text>`/`<tspan>` | Parsing regex direct (pas besoin de ce skill) |
| SVG à texte vectorisé (`<path>` uniquement) + modèle **vision** | Rendu PNG puis lecture image directe |
| SVG à texte vectorisé + modèle **sans vision** | **Ce skill** (rendu PNG ➔ OCR natif) |
| PNG/JPG maquette + modèle sans vision | Étape 2 seule (OCR natif) |
| Besoin d'une description sémantique riche (couleurs, layout) | Déléguer à un worker multimodal (`worker-spawn` + modèle vision) |

---

## 🩺 Diagnostic rapide (vérifier qu'un SVG est vectorisé)

```powershell
$raw = Get-Content -LiteralPath "maquette.svg" -Raw
"text tspan path" -split ' ' | ForEach-Object {
  "<$_> : " + ([regex]::Matches($raw, "<$_[\s>]")).Count
}
# <text> : 0 et <tspan> : 0 + <path> élevé  ➔  texte vectorisé, ce skill s'applique.
```

---

## 📎 Notes de robustesse (retours d'expérience)

- **`cairosvg` inutilisable sur Windows** : dépend de la DLL native `libcairo-2.dll` absente
  par défaut ➔ ne pas s'appuyer dessus. Préférer le rendu Chromium (toujours dispo via crawler).
- **`convert.exe` de `System32` n'est PAS ImageMagick** (c'est l'outil de conversion FAT➔NTFS).
- **Interpréteur Python** : `pip`/`python` du PATH peuvent différer de l'interpréteur cible ;
  vérifier `pip show <pkg>` ➔ `Location` avant de conclure à un module manquant.
- **`Windows.Media.Ocr`** requiert un pack de langue installé pour la langue cible
  (`TryCreateFromUserProfileLanguages()` prend la langue du profil ; fr-CA/fr-FR/en-US OK par défaut).
- Travail temporaire hors workspace : utiliser `C:\Users\<user>\AppData\Local\Temp\opencode`.

---

## 🛡️ Résilience & Dégradation Gracieuse
Si Chromium ou Playwright échouent lors du rendu headless (timeout ou binaire absent), consigner l'anomalie dans `memory/logs/` et déléguer l'extraction à un sous-agent multimodal disposant de capacités de vision native via `worker-spawn` sans bloquer le cycle.
