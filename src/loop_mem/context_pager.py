"""
Virtual Context Pager — Gestion de Mémoire Paginée pour LLMs (Inspiré de MemGPT / Letta).

Découpe la mémoire de travail en Working Pages actives :
- Page 0 : System Core & Directives Fondatrices (AGENTS.md).
- Page 1 : Story Active & Spécifications Gherkin.
- Page 2 : EvidencePack JSON & Preuves.
- Page 3 : Contrats d'Interface & ADRs actifs.
Les pages froides sont paginées à la demande depuis SQLite FTS5.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class VirtualContextPage:
    """Représente une page de contexte atomique en mémoire vive."""

    def __init__(self, page_id: str, title: str, content: str, priority: int = 1) -> None:
        self.page_id = page_id
        self.title = title
        self.content = content
        self.priority = priority  # 1 = Haute priorité (Toujours en RAM), 3 = Faible (Paginable)
        self.token_estimate = max(1, len(content) // 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_id": self.page_id,
            "title": self.title,
            "priority": self.priority,
            "token_estimate": self.token_estimate,
        }


class VirtualContextPager:
    """Moteur de pagination de mémoire de contexte."""

    def __init__(self, max_working_tokens: int = 8000) -> None:
        self.max_working_tokens = max_working_tokens
        self.active_pages: Dict[str, VirtualContextPage] = {}
        self.page_access_history: List[str] = []

    def load_page(self, page_id: str, title: str, content: str, priority: int = 1) -> VirtualContextPage:
        """Charge ou remplace une page dans l'espace d'adressage virtuel."""
        page = VirtualContextPage(page_id, title, content, priority)
        self.active_pages[page_id] = page
        self.page_access_history.append(page_id)
        self._enforce_budget()
        return page

    def get_page(self, page_id: str) -> Optional[VirtualContextPage]:
        """Récupère une page active et met à jour son statut LRU."""
        if page_id in self.active_pages:
            self.page_access_history.append(page_id)
            return self.active_pages[page_id]
        return None

    def evict_page(self, page_id: str) -> bool:
        """Décharge une page de la mémoire vive."""
        if page_id in self.active_pages:
            del self.active_pages[page_id]
            return True
        return False

    def render_context_window(self) -> str:
        """Compile et rend le prompt système optimisé contenant uniquement les pages actives."""
        # Trier par priorité croissante (1 en premier)
        sorted_pages = sorted(self.active_pages.values(), key=lambda p: p.priority)
        
        rendered_sections = []
        for page in sorted_pages:
            rendered_sections.append(f"<!-- [PAGE: {page.page_id}] {page.title} (Priority: {page.priority}) -->\n{page.content}")

        return "\n\n---\n\n".join(rendered_sections)

    def total_tokens(self) -> int:
        """Calcule l'estimation totale des tokens en mémoire vive."""
        return sum(p.token_estimate for p in self.active_pages.values())

    def _enforce_budget(self) -> None:
        """Éviction LRU (Least Recently Used) si le budget mémoire est dépassé."""
        while self.total_tokens() > self.max_working_tokens and len(self.active_pages) > 1:
            # Chercher la page de plus faible priorité la moins récemment utilisée
            evict_candidate = None
            for pid in self.page_access_history:
                if pid in self.active_pages and self.active_pages[pid].priority > 1:
                    evict_candidate = pid
                    break
            
            if evict_candidate:
                self.evict_page(evict_candidate)
                self.page_access_history = [p for p in self.page_access_history if p != evict_candidate]
            else:
                break
