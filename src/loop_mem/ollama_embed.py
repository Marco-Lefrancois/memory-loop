import json
import logging
import urllib.request
import math
from typing import List

logger = logging.getLogger(__name__)

# Modèle d'embedding local dédié installé via Ollama pour la mémoire RHO.
# `mxbai-embed-large` a été retenu après benchmark sur la tâche RHO réelle
# (meilleure marge discriminante positif/négatif et meilleur cross-lingue EN->FR
# que `bge-m3`). Dimension de sortie : 1024 (compatible table `rho_memory`).
OLLAMA_EMBED_MODEL = "mxbai-embed-large"

# Deadline explicite pour l'appel réseau synchrone (ADR-0369 : Zero-Unbounded-Wait).
OLLAMA_EMBED_TIMEOUT_SECONDS = 30.0

# Borne de sécurité sur la longueur du texte soumis à l'embedding.
# `mxbai-embed-large` a une fenêtre de contexte d'environ 512 tokens : au-delà,
# l'API renvoie une erreur serveur (HTTP 500). On tronque donc sur un préfixe
# représentatif (~512 tokens, marge de sécurité), largement suffisant pour la
# proximité sémantique d'une trace d'erreur RHO ou d'un préambule documentaire.
OLLAMA_EMBED_MAX_CHARS = 1500


def get_embedding(text: str, model: str = OLLAMA_EMBED_MODEL) -> List[float]:
    """Récupère le vecteur d'embedding depuis l'API locale Ollama."""
    if text and len(text) > OLLAMA_EMBED_MAX_CHARS:
        text = text[:OLLAMA_EMBED_MAX_CHARS]
    url = "http://localhost:11434/api/embeddings"
    data = {"model": model, "prompt": text}
    req = urllib.request.Request(
        url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_EMBED_TIMEOUT_SECONDS) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("embedding", [])
    except Exception as exc:
        logger.warning(
            "Échec de récupération de l'embedding Ollama (RHO en mode dégradé)",
            exc_info=True,
            extra={"model": model, "url": url, "text_len": len(text)},
        )
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
