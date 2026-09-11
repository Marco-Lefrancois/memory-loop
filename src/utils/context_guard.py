"""
Context Guard (ADR-0352 / HarnessDev).
Garantit l'intégrité des flux de messages agentiques :
1. Intégrité des paires tool_call <-> tool_result (évite les erreurs HTTP 400 sur Gemini/OpenAI).
2. Tronquage non-destructif des sorties d'outils volumineuses avec empreinte SHA256.
"""
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

class ContextGuard:
    """
    Garde-fou d'intégrité conversationnelle et de compaction sémantique.
    """

    @staticmethod
    def validate_tool_message_pairing(messages: List[Dict[str, Any]]) -> bool:
        """
        Vérifie qu'aucun appel d'outil n'est orphelin et qu'aucun résultat d'outil n'est dissocié.
        Supporte les formats OpenAI/Anthropic/Gemini standard.
        """
        pending_tool_calls = set()

        for msg in messages:
            role = msg.get("role")
            
            # Détection des tool_calls émis par l'assistant
            if role == "assistant":
                tool_calls = msg.get("tool_calls") or []
                for tc in tool_calls:
                    tc_id = tc.get("id") or tc.get("name")
                    if tc_id:
                        pending_tool_calls.add(tc_id)
            
            # Détection des retours d'outils
            elif role == "tool":
                tool_call_id = msg.get("tool_call_id") or msg.get("name")
                if tool_call_id in pending_tool_calls:
                    pending_tool_calls.remove(tool_call_id)
                elif tool_call_id is None:
                    # Résultat sans ID associé
                    return False

        # Si des appels d'outils n'ont pas reçu de réponse, le flux est corrompu
        return len(pending_tool_calls) == 0

    @staticmethod
    def truncate_tool_output(output_text: str, max_lines: int = 70, head_lines: int = 50, tail_lines: int = 20) -> str:
        """
        Tronque une sortie volumineuse en conservant les têtes et queues utiles avec empreinte SHA256.
        """
        lines = output_text.splitlines()
        if len(lines) <= max_lines:
            return output_text

        content_hash = hashlib.sha256(output_text.encode("utf-8")).hexdigest()[:16]
        head = lines[:head_lines]
        tail = lines[-tail_lines:]
        omitted = len(lines) - head_lines - tail_lines

        separator = f"\n... [{omitted} lignes omises pour préserver le budget de contexte. SHA256: {content_hash}] ...\n"
        return "\n".join(head) + separator + "\n".join(tail)

    INJECTION_PATTERNS = [
        re.compile(r'(?i)\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|prompts|rules|commands)\b'),
        re.compile(r'(?i)\bdisregard\s+(?:all\s+)?(?:previous|prior|above)\b'),
        re.compile(r'(?i)\bsystem\s+override\b'),
        re.compile(r'(?i)\byou\s+are\s+now\s+(?:an?\s+unrestricted|in\s+developer\s+mode|dan|a\s+new\s+agent)\b'),
        re.compile(r'(?i)\bforget\s+(?:all\s+)?your\s+(?:rules|instructions|directives)\b'),
        re.compile(r'(?i)\bnew\s+instructions\s*:\s*you\s+must\b'),
    ]

    @classmethod
    def sanitize_prompt_injection(cls, content: str) -> tuple[str, bool, List[str]]:
        """
        Détecte et neutralise les motifs d'injection de consignes indirectes
        au sein des documents ou données récupérées (ADR-0353 - Content as Data, Never Policy).
        """
        if not content:
            return ("", False, [])

        detected = []
        sanitized = content
        for pattern in cls.INJECTION_PATTERNS:
            matches = pattern.findall(sanitized)
            if matches:
                detected.extend([m if isinstance(m, str) else m[0] for m in matches])
                sanitized = pattern.sub("[CONSIGNE_NEUTRALISÉE: TENTATIVE_INJECTION_DÉTECTÉE]", sanitized)

        was_modified = len(detected) > 0
        return (sanitized, was_modified, detected)

    @classmethod
    def encapsulate_retrieved_data(
        cls,
        content: str,
        source_id: str = "unknown",
        is_untrusted: bool = True,
        sanitize: bool = True,
    ) -> str:
        """
        Encapsule un extrait documentaire récupéré dans un bloc de données XML étanche.
        Garantit que le modèle LLM traite le texte comme de la donnée brute et non comme une instruction.
        """
        cleaned_content = content
        if sanitize:
            cleaned_content, _, _ = cls.sanitize_prompt_injection(content)

        untrusted_attr = "true" if is_untrusted else "false"
        return f'<retrieved_data source="{source_id}" untrusted="{untrusted_attr}">\n{cleaned_content}\n</retrieved_data>'

    @classmethod
    def offload_heavy_tool_output(
        cls,
        output_text: str,
        max_chars: int = 2000,
        project_name: Optional[str] = None,
        base_dir: Optional[Path] = None,
    ) -> str:
        """
        Déporte les sorties d'outils volumineuses (> 2000 caractères) dans un fichier sidecar
        sous memory/artifacts/sidecars/<hash>.txt et retourne un résumé compact avec Micro-URI.
        Évite l'explosion du contexte tout en garantissant la récupérabilité totale (ADR-0364).
        """
        if not output_text or len(output_text) <= max_chars:
            return output_text

        content_hash = hashlib.sha256(output_text.encode("utf-8")).hexdigest()[:12]

        from src.engine.hooks.path_resolver import PathAliasResolver
        proj_root = PathAliasResolver.get_project_root(project_name, base_dir)
        sidecar_dir = proj_root / "memory" / "artifacts" / "sidecars"
        try:
            sidecar_dir.mkdir(parents=True, exist_ok=True)
            sidecar_file = sidecar_dir / f"{content_hash}.txt"
            sidecar_file.write_text(output_text, encoding="utf-8")
        except Exception:
            pass

        preview = cls.truncate_tool_output(output_text, max_lines=20, head_lines=15, tail_lines=5)

        return (
            f"{preview}\n\n"
            f"[⚠️ Sortie volumineuse ({len(output_text)} chars) déportée dans le sidecar: "
            f"`evidence://../artifacts/sidecars/{content_hash}.txt` - Consultation complète via view_file si nécessaire]"
        )

