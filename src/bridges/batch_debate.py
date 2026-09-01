import argparse
import asyncio
import os
import sys
import subprocess
from pathlib import Path
from openai import AsyncOpenAI
import yaml

def load_env():
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip('"\'')

load_env()
LITELLM_BASE_URL = os.environ.get("LITELLM_BASE_URL", "https://api-ia.nmedia.ca").rstrip("/") + "/v1"

def get_api_key():
    api_key = os.environ.get("LITELLM_API_KEY")
    if api_key:
        return api_key
    for secret_name in ["litellm-key", "nmedia-key"]:
        secret_path = Path.home() / ".secrets" / secret_name
        if secret_path.exists():
            return secret_path.read_text().strip()
    print("ERROR: API Key not found. Please set LITELLM_API_KEY or create ~/.secrets/litellm-key")
    sys.exit(1)

def load_config():
    config_path = Path(__file__).parent / "debate_config.yaml"
    if not config_path.exists():
        print(f"ERROR: Config file not found at {config_path}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

from src.core.llm_client import AsyncLLMClient

async def extract_debate_query(client: AsyncLLMClient, model_id: str, file_path: Path, project_name: str = "mLoop") -> str:
    print(f"  > Lecture de {file_path.name} pour extraire la problématique...")
    content = file_path.read_text(encoding="utf-8")
    
    system_prompt = """Tu es un Analyste d'Affaires Expert.
Ton but est de lire un récit utilisateur (Story) et d'en extraire la question architecturale ou métier la plus complexe à débattre.
Concentre-toi sur les cas limites (edge cases), la concurrence, les contraintes réseau, la sécurité ou les règles d'affaires critiques.
Tu DOIS retourner UNIQUEMENT la question (une seule phrase), rien d'autre."""

    user_prompt = f"Voici le récit :\n\n{content}\n\nQuelle est la question de débat la plus critique pour l'Équipe d'Architecture ?"

    try:
        response = await client.complete(
            model=model_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            project_name=project_name,
            action_name="batch_debate_query",
            target_name=file_path.name,
        )
        return response["text"].strip()
    except Exception as e:
        print(f"  > Erreur lors de l'extraction: {e}")
        return "Comment garantir l'intégrité et la robustesse de ce récit en production ?"

async def main():
    parser = argparse.ArgumentParser(description="Batch Runner for Agentic Debate")
    parser.add_argument("--project", required=True, help="Nom du projet cible")
    args = parser.parse_args()

    project_dir = Path("Projects") / args.project
    stories_dir = project_dir / "backlog" / "stories"

    if not stories_dir.exists():
        print(f"ERREUR: Le dossier {stories_dir} n'existe pas.")
        sys.exit(1)

    # Récupérer tous les fichiers markdown
    story_files = list(stories_dir.rglob("*.md"))
    # Exclure les README, index ou autres fichiers non-récits si besoin
    story_files = [f for f in story_files if "REC-" in f.name]

    print(f"Trouvé {len(story_files)} récits à analyser dans {args.project}.")

    config = load_config()
    client = AsyncLLMClient(base_url=LITELLM_BASE_URL)
    model_id = config.get("strategies", {}).get("deep_architecture", {}).get("synthesizer", "claude-opus-4.7")

    for file_path in story_files:
        print(f"\n[{file_path.name}] Début de l'analyse en rafale...")
        
        # 1. Extraire la question
        query = await extract_debate_query(client, model_id, file_path)
        print(f"  > Question générée : {query}")

        # 2. Exécuter le débat
        debate_script = Path(__file__).parent / "agentic_debate.py"
        
        print("  > Lancement de l'équipe d'architecture (cela peut prendre 2-3 minutes)...")
        # On utilise subprocess pour lancer le script proprement
        cmd = [
            sys.executable,
            str(debate_script),
            "--project", args.project,
            "--context-file", str(file_path),
            "--query", query,
            "--strategy", "deep_architecture"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # Le script original sauvegarde dans debate_transcript.md. On va le renommer.
                original_output = project_dir / "memory" / "debate_transcript.md"
                new_output = project_dir / "memory" / f"debate_transcript_{file_path.stem}.md"
                if original_output.exists():
                    original_output.rename(new_output)
                    print(f"  > OK: Rapport sauvegardé dans {new_output}")
                else:
                    print("  > ATTENTION: Le fichier de rapport n'a pas été trouvé.")
            else:
                print(f"  > ERREUR: Le débat a échoué.\n{result.stderr}")
        except Exception as e:
            print(f"  > ERREUR: Échec de l'exécution: {e}")

    print("\n--- ANALYSE EN RAFALE TERMINÉE ---")

if __name__ == "__main__":
    asyncio.run(main())
