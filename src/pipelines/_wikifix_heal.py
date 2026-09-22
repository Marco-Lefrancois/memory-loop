"""Guérison ligne à ligne WikiFix : callouts, liens et audit-heal fichiers (MLOOP-145-BE — extraction ADR-0202)."""

from __future__ import annotations

import os
import re
import urllib.parse
from pathlib import Path
from typing import Dict, List, Set, Tuple

from src.cli import ZeroFluffConsole
from src.utils.logger import get_logger

logger = get_logger("pipelines.wikifix_heal")


def os_relative_path(from_dir: Path, to_file: Path) -> str:
    return os.path.relpath(str(to_file), start=str(from_dir)).replace("\\", "/")


class WikiFixHealMixin:
    """Méthodes de guérison de lignes et d'audit-heal — dépend de self.supported_callouts / self._normalize_callout."""

    supported_callouts: Set[str]

    def _normalize_callout(self, callout_type: str) -> str | None:  # pragma: no cover - surchargé
        raise NotImplementedError

    def _heal_line_callout(
        self, line: str, line_idx: int, file_rel: str, healed_callouts: list, callouts_alerts: list
    ) -> Tuple[str, bool]:
        match = re.search(r"^\s*>\s*\[!([^\]]+)\](.*)$", line)
        if not match:
            return line, False
        raw_type = match.group(1)
        if raw_type not in self.supported_callouts:
            normalized = self._normalize_callout(raw_type)
            if normalized:
                new_line = re.sub(r"\[![^\]]+\]", f"[!{normalized}]", line)
                healed_callouts.append(
                    {"file": file_rel, "line": line_idx, "from": raw_type, "to": normalized}
                )
                ZeroFluffConsole.success(
                    f"Callout auto-corrigé dans {file_rel}:{line_idx} ({raw_type} -> {normalized})"
                )
                return new_line, True
            callouts_alerts.append(
                {
                    "file": file_rel,
                    "line": line_idx,
                    "type": raw_type,
                    "msg": f"Callout non standard '{raw_type}'.",
                }
            )
        return line, False

    def _heal_line_links(
        self,
        line: str,
        line_idx: int,
        file_path: Path,
        file_rel: str,
        basename_map: dict,
        referenced_files: set,
        healed_links: list,
        broken_links_alerts: list,
    ) -> Tuple[str, bool]:
        matches = list(re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", line))
        if not matches:
            return line, False
        line_offset = 0
        file_modified = False
        for match in matches:
            link_target = match.group(2).strip()
            if link_target.startswith(("http://", "https://", "mailto:")) or link_target.startswith(
                "#"
            ):
                continue
            decoded = urllib.parse.unquote(link_target)
            target_str = decoded.split("#")[0]
            if not target_str:
                continue
            target_path = (
                Path(target_str.replace("file:///", ""))
                if target_str.startswith("file:///")
                else (file_path.parent / target_str).resolve()
            )
            if target_path.exists():
                referenced_files.add(target_path.resolve())
            else:
                target_name = Path(target_str).name.lower()
                if target_name in basename_map and len(basename_map[target_name]) == 1:
                    resolved = basename_map[target_name][0]
                    referenced_files.add(resolved.resolve())
                    try:
                        rel = os_relative_path(file_path.parent, resolved)
                    except Exception:
                        rel = resolved.resolve().as_uri()
                    anchor = ("#" + decoded.split("#")[1]) if "#" in decoded else ""
                    new_target = f"{rel}{anchor}"
                    sp, ep = match.start(2) + line_offset, match.end(2) + line_offset
                    line = line[:sp] + new_target + line[ep:]
                    line_offset += len(new_target) - len(link_target)
                    file_modified = True
                    healed_links.append(
                        {
                            "file": file_rel,
                            "line": line_idx,
                            "broken": link_target,
                            "healed": new_target,
                        }
                    )
                    ZeroFluffConsole.success(f"Lien auto-corrigé dans {file_rel}:{line_idx}")
                else:
                    broken_links_alerts.append(
                        {
                            "file": file_rel,
                            "line": line_idx,
                            "target": link_target,
                            "msg": "Lien brisé.",
                        }
                    )
        return line, file_modified

    def _audit_and_heal_files(
        self,
        project_path: Path,
        markdown_files: list[Path],
        basename_map: dict,
        cache_data: dict,
        verbose: bool,
    ) -> tuple:
        b_alerts, h_links, c_alerts, h_callouts, ref_files, new_cache = [], [], [], [], set(), {}
        for file_path in markdown_files:
            file_rel = str(file_path.relative_to(project_path))
            mtime = os.path.getmtime(file_path)
            cached = cache_data.get(file_rel, {})
            if cached.get("mtime") == mtime and not verbose:
                new_cache[file_rel] = cached
                for ref in cached.get("referenced_files", []):
                    if Path(ref).exists():
                        ref_files.add(Path(ref).resolve())
                continue
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception as e:
                ZeroFluffConsole.error(f"Impossible de lire {file_rel}: {e}")
                continue
            file_mod = False
            new_lines = []
            for idx, line in enumerate(content.splitlines(), 1):
                line, c_mod = self._heal_line_callout(line, idx, file_rel, h_callouts, c_alerts)
                line, l_mod = self._heal_line_links(
                    line, idx, file_path, file_rel, basename_map, ref_files, h_links, b_alerts
                )
                file_mod = file_mod or c_mod or l_mod
                new_lines.append(line)
            if file_mod:
                try:
                    file_path.write_text("\n".join(new_lines), encoding="utf-8")
                    mtime = os.path.getmtime(file_path)
                except Exception as e:
                    ZeroFluffConsole.error(f"Échec écriture {file_rel}: {e}")
            new_cache[file_rel] = {
                "mtime": mtime,
                "referenced_files": [str(p) for p in ref_files if p.exists()],
            }
        return b_alerts, h_links, c_alerts, h_callouts, ref_files, new_cache
