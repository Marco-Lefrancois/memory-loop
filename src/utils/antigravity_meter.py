"""
Moteur d'extraction et d'audit des tokens et interactions Antigravity (Google DeepMind).
Analyse les transcripts locaux de l'IDE Antigravity et injecte la consommation dans le Token Ledger mLoop.
Distinction de source : source = 'Google'.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from src.utils.logger import get_logger
from src.utils.token_ledger import TokenLedger

logger = get_logger("antigravity_meter")

DEFAULT_BRAIN_DIR = Path.home() / ".gemini" / "antigravity-ide" / "brain"
ACTIVE_CONVERSATION_ID = "01eb191b-bf1c-448a-afeb-618a55bdfabe"


class AntigravityMeter:
    """Analyseur de logs et transcripts de l'IDE Antigravity."""

    @classmethod
    def get_existing_fingerprints(cls, ledger_path: Path) -> Set[str]:
        """Collecte les empreintes uniques déjà présentes dans le ledger pour éviter les doublons."""
        fps = set()
        if not ledger_path.exists():
            return fps
        try:
            with open(ledger_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                        meta = e.get("metadata", {})
                        if "antigravity_step" in meta and "conversation_id" in meta:
                            fps.add(f"{meta['conversation_id']}_{meta['antigravity_step']}")
                        else:
                            fps.add(f"{e.get('timestamp')}_{e.get('action')}_{e.get('target')}")
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.debug(
                            "Ligne fingerprint Antigravity invalide ignorée",
                            exc_info=True,
                            extra={"error": str(e)},
                        )
        except Exception as e:
            logger.debug(f"Erreur lecture fingerprints: {e}")
        return fps

    @classmethod
    def parse_conversation_transcript(
        cls,
        conv_dir: Path,
        existing_fps: Optional[Set[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Parse un dossier de conversation Antigravity et extrait les interactions
        en calculant prompt_tokens et completion_tokens pour chaque tour de parole.
        """
        conv_id = conv_dir.name
        log_file = conv_dir / ".system_generated" / "logs" / "transcript_full.jsonl"
        if not log_file.exists():
            log_file = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
        if not log_file.exists():
            return []

        existing = existing_fps or set()
        interactions: List[Dict[str, Any]] = []

        active_model = "gemini-3.8-flash"
        current_user_request = ""
        current_user_time = None
        turn_prompt_chars = 0
        turn_completion_chars = 0
        turn_step_indices: List[int] = []
        turn_actions: List[str] = []

        try:
            lines = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception as e:
            logger.warning(f"Impossible de lire le transcript de {conv_id}: {e}")
            return []

        def flush_turn():
            nonlocal \
                current_user_request, \
                current_user_time, \
                turn_prompt_chars, \
                turn_completion_chars, \
                turn_step_indices, \
                turn_actions
            if not turn_step_indices:
                return

            last_step = turn_step_indices[-1]
            fp = f"{conv_id}_{last_step}"
            if fp in existing:
                turn_step_indices = []
                turn_actions = []
                turn_prompt_chars = 0
                turn_completion_chars = 0
                return

            # Ratio de conversion standard SentencePiece/Gemini : ~3.8 caractères par token
            prompt_tokens = max(15, int(turn_prompt_chars / 3.8))
            completion_tokens = max(5, int(turn_completion_chars / 3.8))
            total_tokens = prompt_tokens + completion_tokens

            # Modèle & Tarification Gemini 3.8 Flash ($0.15 input / $0.60 output per 1M)
            pricing = TokenLedger.DEFAULT_PRICING_PER_1M.get(active_model, (0.15, 0.60))
            cost_usd = (prompt_tokens / 1_000_000.0) * pricing[0] + (
                completion_tokens / 1_000_000.0
            ) * pricing[1]

            target_text = (
                current_user_request[:120].strip()
                if current_user_request
                else f"Turn step {turn_step_indices[0]}-{last_step}"
            )
            target_text = re.sub(r"\s+", " ", target_text)

            ts = current_user_time or datetime.now(timezone.utc).isoformat()
            act = turn_actions[0] if turn_actions else "chat_turn"

            entry = {
                "timestamp": ts,
                "source": "antigravity-chat",
                "project": "Memory Loop",
                "key_label": "Google Workspace / Enterprise",
                "key_masked": "google-oauth",
                "action": act,
                "target": target_text,
                "model": active_model,
                "prompt_tokens_est": prompt_tokens,
                "completion_tokens_est": completion_tokens,
                "total_tokens_est": total_tokens,
                "cost_usd_est": round(cost_usd, 6),
                "context_contributors": ["antigravity-session", f"steps-{len(turn_step_indices)}"],
                "metadata": {
                    "conversation_id": conv_id,
                    "antigravity_step": last_step,
                    "total_steps_in_turn": len(turn_step_indices),
                    "model_source": "Google DeepMind",
                    "tools_used": list(dict.fromkeys(turn_actions)) if turn_actions else [],
                },
            }

            interactions.append(entry)
            existing.add(fp)

            turn_step_indices = []
            turn_actions = []
            turn_prompt_chars = 0
            turn_completion_chars = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except Exception as e:
                logger.debug(
                    "Ligne JSON du métrage antigravity illisible, ignorée",
                    exc_info=True,
                    extra={
                        "component": "utils.antigravity_meter",
                        "operation": "parse_meter_events",
                        "error": str(e),
                    },
                )

            s_type = data.get("type", "")
            step_idx = data.get("step_index", 0)
            c_at = data.get("created_at")

            # Détection de changement de modèle
            content = data.get("content", "") or ""
            if "Model Selection" in content:
                if "Gemini 3.8 Flash" in content:
                    active_model = "gemini-3.8-flash"
                elif "Gemini 3.7 Flash" in content:
                    active_model = "gemini-3.7-flash"

            if s_type == "USER_INPUT":
                flush_turn()
                current_user_time = c_at
                # Nettoyer les balises <USER_REQUEST> pour isoler le message métier
                req_match = re.search(r"<USER_REQUEST>(.*?)</USER_REQUEST>", content, re.DOTALL)
                if req_match:
                    current_user_request = req_match.group(1).strip()
                else:
                    current_user_request = content.strip()
                turn_prompt_chars += len(content)
                turn_step_indices.append(step_idx)

            elif s_type == "PLANNER_RESPONSE":
                turn_step_indices.append(step_idx)
                thinking = data.get("thinking", "") or ""
                resp_content = data.get("content", "") or ""
                tool_calls = data.get("tool_calls", []) or []

                turn_completion_chars += (
                    len(thinking) + len(resp_content) + len(json.dumps(tool_calls))
                )
                if tool_calls:
                    for tc in tool_calls:
                        t_name = tc.get("name") or "tool"
                        turn_actions.append(t_name)

            elif s_type in (
                "RUN_COMMAND",
                "VIEW_FILE",
                "GREP_SEARCH",
                "CODE_ACTION",
                "LIST_DIRECTORY",
                "READ_URL_CONTENT",
                "BROWSER_SUBAGENT",
            ):
                turn_step_indices.append(step_idx)
                turn_prompt_chars += len(content)

            elif s_type in ("SYSTEM_MESSAGE", "ERROR_MESSAGE", "GENERIC"):
                turn_step_indices.append(step_idx)
                turn_prompt_chars += len(content)

        flush_turn()
        return interactions

    @classmethod
    def sync(
        cls,
        root_dir: Optional[Path] = None,
        conversation_id: Optional[str] = None,
        all_conversations: bool = False,
    ) -> Dict[str, Any]:
        """
        Synchronise les interactions d'Antigravity vers memory/token_ledger.jsonl.
        """
        root = root_dir or Path(".")
        ledger_file = root / "memory" / "token_ledger.jsonl"
        existing_fps = cls.get_existing_fingerprints(ledger_file)

        brain_dir = DEFAULT_BRAIN_DIR
        if not brain_dir.exists():
            return {
                "synced": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "message": "Répertoire brain introuvable",
            }

        conv_dirs: List[Path] = []
        if conversation_id:
            c_dir = brain_dir / conversation_id
            if c_dir.exists():
                conv_dirs.append(c_dir)
        elif all_conversations:
            conv_dirs = [p for p in brain_dir.iterdir() if p.is_dir() and len(p.name) > 30]
        else:
            # Par défaut, session active en priorité
            active_dir = brain_dir / ACTIVE_CONVERSATION_ID
            if active_dir.exists():
                conv_dirs.append(active_dir)
            else:
                conv_dirs = [p for p in brain_dir.iterdir() if p.is_dir() and len(p.name) > 30][:3]

        all_new_entries: List[Dict[str, Any]] = []
        for c_dir in conv_dirs:
            entries = cls.parse_conversation_transcript(c_dir, existing_fps)
            all_new_entries.extend(entries)

        if all_new_entries:
            ledger_file.parent.mkdir(parents=True, exist_ok=True)
            with open(ledger_file, "a", encoding="utf-8") as f:
                for e in all_new_entries:
                    f.write(json.dumps(e, ensure_ascii=False) + "\n")

        total_toks = sum(e["total_tokens_est"] for e in all_new_entries)
        total_cost = sum(e["cost_usd_est"] for e in all_new_entries)

        logger.info(
            f"Synchronisation Antigravity : {len(all_new_entries)} tours synchronisés ({total_toks:,} tokens, ${total_cost:.4f})"
        )

        return {
            "synced_turns": len(all_new_entries),
            "total_tokens": total_toks,
            "total_cost_usd": round(total_cost, 4),
            "conversations_scanned": len(conv_dirs),
        }
