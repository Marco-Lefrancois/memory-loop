import subprocess
import json
import os
from typing import Optional

OFFICE_BIN = r"C:\OfficeCLI\office.exe"

def run_office_cmd(args: list) -> str:
    """Exécute une commande OfficeCLI et retourne la sortie."""
    if not os.path.exists(OFFICE_BIN):
        return "Erreur : OfficeCLI non trouvé dans C:\\OfficeCLI\\office.exe"
    
    cmd = [OFFICE_BIN] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            return f"Erreur OfficeCLI : {result.stderr}"
        return result.stdout
    except Exception as e:
        return f"Exception lors de l'exécution : {str(e)}"

def office_read_excel(file_path: str, query: str = "sheet(1).all"):
    """Lit des données d'un fichier Excel."""
    # Exemple de commande : office view --input file.xlsx --query "sheet(1).cell(A1)"
    return run_office_cmd(["view", "--input", file_path, "--query", query])

if __name__ == "__main__":
    # Test simple sur le fichier RBC si présent
    test_file = r"C:\Memory Loop\Projects\rbc-avion-metro\reference\Offer codes mapping_June2026.xlsx"
    if os.path.exists(test_file):
        print("Lecture du fichier Excel via OfficeCLI...")
        # On tente de lire les premières lignes de la première feuille
        print(office_read_excel(test_file, "sheet(1).range(A1:C5)"))
    else:
        print(f"Fichier de test non trouvé : {test_file}")
