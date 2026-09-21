"""Façade de compatibilité ADR-0202 pour WikiFixAgent.

L'implémentation est découpée dans wikifix_core.py et wikifix_auditors.py.
"""
from src.pipelines.wikifix_core import WikiFixAgent, os_relative_path

__all__ = ["WikiFixAgent", "os_relative_path"]
