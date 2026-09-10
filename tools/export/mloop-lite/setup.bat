@echo off
setlocal
echo ======================================================================
echo 🚀 Installation & Initialisation de l'Environnement mLoop Lite
echo ======================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python n'est pas detecte sur votre machine.
    echo Veuillez installer Python depuis https://www.python.org/downloads/
    echo ou lancer dans un terminal administrateur : winget install Python.Python.3.11
    pause
    exit /b 1
)

echo [1/4] Creation de l'environnement virtuel (.venv)...
if not exist .venv (
    python -m venv .venv
)

echo [2/4] Activation de l'environnement virtuel...
call .venv\Scripts\activate

echo [3/4] Installation des modules (MarkItDown, Office, RapidOCR, Crawler)...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [4/4] Creation et verification des repertoires de travail...
if not exist projects mkdir projects
if not exist reference mkdir reference
if not exist docs mkdir docs
if not exist docs\adr mkdir docs\adr
if not exist deliverables mkdir deliverables
if not exist deliverables\templates mkdir deliverables\templates
if not exist memory mkdir memory
if not exist memory\evidence mkdir memory\evidence

echo.
echo ======================================================================
echo ✅ Installation et arborescence pretes a 100% !
echo.
echo 📁 Vos repertoires sont prets :
echo    ├── projects/     (Pour vos differents clients)
echo    ├── reference/    (Deposez vos documents bruts)
echo    ├── docs/         (Base SSOT, lexique, ADRs)
echo    ├── deliverables/ (Vos livrables finaux)
echo    └── memory/       (Index FTS5 et preuves)
echo.
echo 💡 Pour demarrer un nouveau client :
echo    mloop init --role ba --project NomClient
echo.
echo 💡 Ou pour travailler directement dans ce dossier :
echo    mloop resume
echo ======================================================================
pause
