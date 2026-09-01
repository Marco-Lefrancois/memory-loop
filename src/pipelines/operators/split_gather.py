"""
Opérateurs DocETL : Split & Gather pour Memory Loop (mLoop).
- Split : Découpage déterministe d'un texte/document en chunks cohérents.
- Gather : Fenêtrage contextuel (windowing sémantique) injectant le contexte amont/aval,
  les résumés de chunks précédents et les métadonnées globales.
"""

import math
import re
import uuid
from typing import Any, Dict, List, Optional


def split_document(
    text: str,
    chunk_size: int = 1200,
    method: str = "token_count",
    doc_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Divise un document volumineux en chunks gérables avec préservation des frontières de paragraphes.
    
    Args:
        text: Texte intégral du document.
        chunk_size: Taille cible en tokens (estimation 4 caractères/token) ou caractères.
        method: 'token_count' ou 'character_count'.
        doc_id: Identifiant unique du document source (généré si non fourni).
        metadata: Métadonnées documentaires globales.
        
    Returns:
        Liste d'objets chunks prêts pour Gather / Map.
    """
    if not text or not text.strip():
        return []

    assigned_doc_id = doc_id or str(uuid.uuid4())[:8]
    char_chunk_size = chunk_size * 4 if method == "token_count" else chunk_size
    
    # Découpage par paragraphes pour respecter les blocs logiques
    paragraphs = re.split(r'\n\s*\n', text.strip())
    raw_chunks: List[str] = []
    current_chunk = []
    current_len = 0

    for p in paragraphs:
        p_len = len(p)
        if current_len + p_len > char_chunk_size and current_chunk:
            raw_chunks.append("\n\n".join(current_chunk))
            current_chunk = [p]
            current_len = p_len
        else:
            current_chunk.append(p)
            current_len += p_len + 2

    if current_chunk:
        raw_chunks.append("\n\n".join(current_chunk))

    # Si aucun paragraphe ou texte en un seul bloc géant, découpage dur
    if not raw_chunks:
        raw_chunks = [text[i:i + char_chunk_size] for i in range(0, len(text), char_chunk_size)]

    total_chunks = len(raw_chunks)
    chunks: List[Dict[str, Any]] = []

    for idx, chunk_content in enumerate(raw_chunks):
        chunks.append({
            "doc_id": assigned_doc_id,
            "chunk_num": idx + 1,
            "total_chunks": total_chunks,
            "chunk_text": chunk_content,
            "metadata": metadata or {},
            "est_tokens": len(chunk_content) // 4,
        })

    return chunks


def gather_context(
    chunks: List[Dict[str, Any]],
    prev_count: int = 1,
    next_count: int = 0,
    summaries: Optional[List[str]] = None,
    doc_metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Augmente chaque chunk de son contexte périphérique (Gather Operator).
    
    Permet d'injecter :
    1. Les chunks immédiatement précédents / suivants.
    2. Les résumés cumulés de tous les chunks précédents (évite l'amnésie globale).
    3. Les métadonnées globales du document (titre, dates, parties prenantes).
    """
    gathered_chunks: List[Dict[str, Any]] = []
    total = len(chunks)

    for i, c in enumerate(chunks):
        prev_contexts = []
        # Chunks précédents immédiats
        start_prev = max(0, i - prev_count)
        for p_idx in range(start_prev, i):
            prev_contexts.append(f"[Chunk {p_idx+1} Excerpt]:\n{chunks[p_idx]['chunk_text']}")

        # Résumé des chunks antérieurs si disponible
        preceding_summary = ""
        if summaries and i > 0 and i - 1 < len(summaries):
            preceding_summary = f"[Résumé des chunks 1 à {i}]:\n{summaries[i-1]}"

        # Chunks suivants
        next_contexts = []
        end_next = min(total, i + 1 + next_count)
        for n_idx in range(i + 1, end_next):
            next_contexts.append(f"[Chunk {n_idx+1} Excerpt]:\n{chunks[n_idx]['chunk_text']}")

        peripheral_context = {
            "preceding_summary": preceding_summary,
            "previous_chunks": prev_contexts,
            "next_chunks": next_contexts,
            "doc_metadata": doc_metadata or c.get("metadata", {}),
        }

        # Construction du prompt contextualisé unifié
        context_header_parts = []
        if doc_metadata:
            meta_str = ", ".join(f"{k}: {v}" for k, v in doc_metadata.items())
            context_header_parts.append(f"--- Document Metadata: {meta_str} ---")
        if preceding_summary:
            context_header_parts.append(preceding_summary)
        if prev_contexts:
            context_header_parts.append("\n".join(prev_contexts))

        header = "\n\n".join(context_header_parts)
        
        enriched_item = dict(c)
        enriched_item["peripheral_context"] = peripheral_context
        enriched_item["contextualized_text"] = (
            f"{header}\n\n=== CHUNK CIBLE ({c['chunk_num']}/{total}) ===\n{c['chunk_text']}"
            if header else c["chunk_text"]
        )
        gathered_chunks.append(enriched_item)

    return gathered_chunks
