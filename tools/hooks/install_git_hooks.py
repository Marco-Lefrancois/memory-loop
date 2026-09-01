import os
import sys
from pathlib import Path

def install_hooks():
    git_dir = Path(".git")
    if not git_dir.exists() or not git_dir.is_dir():
        print("[ERREUR] Le dossier .git n'a pas été trouvé. Assurez-vous d'être à la racine du projet.")
        sys.exit(1)
        
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    
    post_commit_path = hooks_dir / "post-commit"
    
    post_commit_script = """#!/bin/sh
# Hook mLoop Auto-Healing
# Exécute la mise à jour de l'index Graphify en arrière-plan après chaque commit.

echo "[mLoop] Lancement de l'Auto-Healing (Graphify)..."
graphify update . > /dev/null 2>&1 &
"""
    
    try:
        with open(post_commit_path, "w", encoding="utf-8") as f:
            f.write(post_commit_script)
            
        # Rendre le script exécutable sous Linux/macOS (sans effet bloquant sous Windows)
        if os.name != 'nt':
            os.chmod(post_commit_path, 0o755)
            
        print("[SUCCÈS] Le hook Git 'post-commit' pour l'Auto-Healing a été installé avec succès.")
    except Exception as e:
        print(f"[ERREUR] Impossible d'écrire le hook : {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_hooks()
