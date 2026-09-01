"""
Opérateur DocETL : Entity Resolution (Resolve Operator).
Permet de canoniser et dédupliquer les entités et concepts sémantiquement équivalents
(ex: 'Agent Smith', 'J. Smith', 'Officer Smith') à travers une collection documentaire.
Implémente l'Option A : Blocking vectoriel n-gram / Jaccard O(K*N) + Arbitrage LLM.
"""

import collections
import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from src.core.llm_client import AsyncLLMClient


class EntityResolver:
    """
    Résolveur d'entités avec blocking vectoriel et consolidation canonique.
    """

    def __init__(self, client: Optional[AsyncLLMClient] = None):
        self.client = client or AsyncLLMClient()

    @staticmethod
    def _get_char_ngrams(text: str, n: int = 3) -> Set[str]:
        """Extrait les n-grammes de caractères normalisés."""
        clean = re.sub(r'[^\w\s]', '', text.lower()).strip()
        if len(clean) < n:
            return {clean}
        return {clean[i:i+n] for i in range(len(clean) - n + 1)}

    @classmethod
    def compute_similarity(cls, str1: str, str2: str) -> float:
        """
        Calcule la similarité de Jaccard sur les 3-grammes de caractères.
        """
        set1 = cls._get_char_ngrams(str1)
        set2 = cls._get_char_ngrams(str2)
        if not set1 or not set2:
            return 1.0 if str1.strip().lower() == str2.strip().lower() else 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    def find_candidate_clusters(
        self,
        entities: List[str],
        blocking_threshold: float = 0.30
    ) -> List[List[str]]:
        """
        Étape 1 : Blocking Vectoriel & Lexical O(K*N).
        Regroupe les variantes candidates selon leur similarité lexicale/vectorielle et token overlap.
        """
        unique_entities = sorted(list(set(e.strip() for e in entities if e and e.strip())))
        if not unique_entities:
            return []

        clusters: List[List[str]] = []
        visited = set()

        for i, ent in enumerate(unique_entities):
            if ent in visited:
                continue

            current_cluster = [ent]
            visited.add(ent)
            ent_words = set(re.findall(r'\w{3,}', ent.lower()))

            for j in range(i + 1, len(unique_entities)):
                other = unique_entities[j]
                if other in visited:
                    continue

                sim = self.compute_similarity(ent, other)
                is_sub = (ent.lower() in other.lower()) or (other.lower() in ent.lower())
                other_words = set(re.findall(r'\w{3,}', other.lower()))
                word_overlap = bool(ent_words.intersection(other_words))

                if sim >= blocking_threshold or is_sub or word_overlap:
                    current_cluster.append(other)
                    visited.add(other)

            clusters.append(current_cluster)

        return clusters

    async def resolve(
        self,
        entities: List[str],
        domain_context: str = "Concepts et entités métier",
        model: str = "nmedia_cloud/claude-sonnet-4.6",
        project_name: str = "mLoop",
    ) -> Dict[str, str]:
        """
        Étape 2 : Canonisation des clusters via LLM.
        
        Args:
            entities: Liste de toutes les mentions brutes extraites.
            domain_context: Contexte du domaine pour orienter la forme canonique.
            model: Modèle LLM utilisé pour l'arbitrage.
            project_name: Projet cible.
            
        Returns:
            Dict mapping chaque variante brute vers sa forme canonique officielle.
        """
        clusters = self.find_candidate_clusters(entities)
        canonical_map: Dict[str, str] = {}

        system_prompt = f"""Tu es un Spécialiste en Résolution d'Entités et Alignement Sémantique.
Contexte du Domaine : {domain_context}

Ton rôle est de recevoir un groupe de variantes textuelles qui font référence à une même entité ou concept,
et de déterminer le **Nom Canonique Officiel** le plus complet, précis et représentatif.
Tu DOIS répondre STRICTEMENT au format JSON suivant :
{{
  "canonical_name": "Nom Canonique Retenu",
  "aliases": ["variante 1", "variante 2"]
}}"""

        requests_to_resolve = []
        multi_item_clusters = []

        for cluster in clusters:
            if len(cluster) == 1:
                canonical_map[cluster[0]] = cluster[0]
            else:
                multi_item_clusters.append(cluster)
                user_prompt = f"Voici les variantes détectées :\n" + "\n".join(f"- {item}" for item in cluster)
                requests_to_resolve.append({
                    "model": model,
                    "system_prompt": system_prompt,
                    "user_prompt": user_prompt,
                    "response_schema": {"type": "object"},
                    "action_name": "entity_resolution",
                    "temperature": 0.0,
                })

        if requests_to_resolve:
            responses = await self.client.batch_complete(requests_to_resolve, project_name=project_name)

            for cluster, resp in zip(multi_item_clusters, responses):
                res_json = resp.get("json") or {}
                canonical = res_json.get("canonical_name", cluster[0]).strip()
                for item in cluster:
                    canonical_map[item] = canonical

        return canonical_map
