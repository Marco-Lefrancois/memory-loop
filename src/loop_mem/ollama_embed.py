import json
import urllib.request
import math
from typing import List

# On utilise llama3.1:8b comme modèle par défaut car il est garanti d'être présent dans la configuration de l'agent.
OLLAMA_EMBED_MODEL = "llama3.1:8b"

def get_embedding(text: str, model: str = OLLAMA_EMBED_MODEL) -> List[float]:
    """Récupère le vecteur d'embedding depuis l'API locale Ollama."""
    url = "http://localhost:11434/api/embeddings"
    data = {"model": model, "prompt": text}
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("embedding", [])
    except Exception as e:
        print(f"[Ollama Embed] Erreur lors de la récupération de l'embedding : {e}")
        return []

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calcule la similarité cosinus entre deux vecteurs."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot / (norm_v1 * norm_v2)
