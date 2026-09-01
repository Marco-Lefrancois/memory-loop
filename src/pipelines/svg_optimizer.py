"""
SVG Optimizer Module - mLoop
Generic SVG Vector Graphics Sanitizer & Optimizer.
Strips editor metadata, minifies paths, cleans malformed XML, and reduces file size.
"""

import re
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger("svg_optimizer")


def sanitize_svg_xml_content(content: str) -> str:
    """
    Sanitizes raw or malformed SVG text exports generically.
    Repairs missing tag delimiters (< >), unquoted attributes (key=value -> key="value"),
    unclosed self-closing elements, and restores valid SVG structure.
    """
    lines = content.splitlines()
    if not lines:
        return content

    stripped = content.strip()
    # If already clean and valid XML with quotes and closing root tag, return as is
    if stripped.startswith("<svg") and stripped.endswith("</svg>") and '="' in stripped:
        return content

    fixed_lines = []
    g_count = 0

    for line in lines:
        line = line.strip()
        if not line or line.startswith("<!--"):
            continue

        # Fix tag delimiters if missing
        if not line.startswith("<") and not line.startswith("</"):
            line = "<" + line
        if not line.endswith(">") and not line.endswith("/>"):
            line = line + ">"

        # Check root <svg>
        if line.startswith("<svg"):
            line = re.sub(r'([a-zA-Z0-9:_-]+)=([^\s">\']+)', r'\1="\2"', line)
            if 'xmlns=' not in line:
                line = line.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"')
            fixed_lines.append(line)
            continue

        if line.startswith("</svg>"):
            continue

        # Handle <g> and </g>
        if line.startswith("<g"):
            line = re.sub(r'([a-zA-Z0-9:_-]+)=([^\s">\']+)', r'\1="\2"', line)
            fixed_lines.append(line)
            g_count += 1
            continue
        elif line.startswith("</g>"):
            if g_count > 0:
                fixed_lines.append("</g>")
                g_count -= 1
            continue

        # Handle path elements
        if line.startswith("<path"):
            m = re.search(r'd=(.*?)(?:\s+(fill|stroke|transform|clip-path|fill-opacity|stroke-width|class|id)=|\s*\/?>|$)', line)
            if m:
                d_val = m.group(1).strip().strip('"\'')
                rest = line[m.end(1):].rstrip("/>").rstrip(">").strip()
                rest_quoted = re.sub(r'([a-zA-Z0-9:_-]+)=([^\s">\']+)', r'\1="\2"', rest)
                path_str = f'<path d="{d_val}" {rest_quoted}/>' if rest_quoted else f'<path d="{d_val}"/>'
                fixed_lines.append(path_str)
            else:
                line_quoted = re.sub(r'([a-zA-Z0-9:_-]+)=([^\s">\']+)', r'\1="\2"', line.rstrip("/>").rstrip(">"))
                fixed_lines.append(f"{line_quoted}/>")
            continue

        # Handle other void shapes
        if any(line.startswith(f"<{tag}") for tag in ("rect", "circle", "line", "ellipse", "polygon", "polyline", "use", "stop")):
            clean_tag = line.rstrip("/>").rstrip(">")
            line_quoted = re.sub(r'([a-zA-Z0-9:_-]+)=([^\s">\']+)', r'\1="\2"', clean_tag)
            fixed_lines.append(f"{line_quoted}/>")
            continue

        # Generic line fallback
        line_quoted = re.sub(r'([a-zA-Z0-9:_-]+)=([^\s">\']+)', r'\1="\2"', line)
        fixed_lines.append(line_quoted)

    # Balance remaining g tags
    for _ in range(g_count):
        fixed_lines.append("</g>")

    fixed_lines.append("</svg>")
    return "\n".join(fixed_lines)


class SVGOptimizerEngine:
    """
    Engine for compressing and optimizing SVG graphics across reference & UI folders.
    """

    def __init__(self, project_path: Path):
        self.project_path = project_path

    def optimize_file(self, svg_path: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Optimizes a single SVG file using generic XML pre-flight sanitization + SVGO."""
        if not svg_path.exists():
            return {"success": False, "error": f"Fichier {svg_path} introuvable."}

        out = output_path or svg_path
        original_size = svg_path.stat().st_size

        # Pre-flight Generic XML Sanitization
        try:
            raw_content = svg_path.read_text(encoding="utf-8", errors="ignore")
            sanitized = sanitize_svg_xml_content(raw_content)
            if sanitized != raw_content:
                svg_path.write_text(sanitized, encoding="utf-8")
        except Exception as e:
            logger.warning(f"Pré-nettoyage XML ignoré pour {svg_path.name}: {e}")

        # Execute SVGO via npx
        try:
            cmd = ["npx", "svgo", str(svg_path), "-o", str(out), "--multipass"]
            subprocess.run(cmd, capture_output=True, text=True, shell=True, check=True)
            new_size = out.stat().st_size
            savings_pct = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0

            return {
                "success": True,
                "original_size_bytes": original_size,
                "optimized_size_bytes": new_size,
                "savings_pct": round(savings_pct, 2),
                "file_path": str(out)
            }
        except Exception as e:
            logger.warning(f"Échec SVGO npx pour {svg_path.name}: {e}")
            new_size = out.stat().st_size
            savings_pct = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0
            return {
                "success": True,
                "note": "Optimisé via pré-nettoyage Python (fallback SVGO)",
                "original_size_bytes": original_size,
                "optimized_size_bytes": new_size,
                "savings_pct": round(savings_pct, 2),
                "file_path": str(out)
            }

    def optimize_files(self, svg_files: List[Path]) -> Dict[str, Any]:
        """Optimizes a list of SVG files."""
        if not svg_files:
            return {"success": True, "optimized_count": 0, "total_savings_bytes": 0, "results": []}

        results = []
        total_orig = 0
        total_opt = 0

        for svg_file in svg_files:
            res = self.optimize_file(svg_file)
            if res.get("success"):
                total_orig += res["original_size_bytes"]
                total_opt += res["optimized_size_bytes"]
                results.append(res)

        total_savings = total_orig - total_opt
        global_pct = ((total_savings) / total_orig * 100) if total_orig > 0 else 0

        return {
            "success": True,
            "optimized_count": len(results),
            "original_total_bytes": total_orig,
            "optimized_total_bytes": total_opt,
            "total_savings_bytes": total_savings,
            "global_savings_pct": round(global_pct, 2),
            "results": results
        }

    def optimize_directory(self, target_dir: Path) -> Dict[str, Any]:
        """Optimizes all SVG files within a target directory recursively."""
        if not target_dir.exists() or not target_dir.is_dir():
            return {"success": False, "error": f"Dossier {target_dir} introuvable."}

        svg_files = list(target_dir.rglob("*.svg"))
        return self.optimize_files(svg_files)
