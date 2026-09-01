"""
Agent Plugins 1.0 Export Pipeline (ADR-0309)

Exports a portable Agent Plugin package from the .agents/ directory.
Copies skills/, plugin.json, mcp.json and extension namespaces into a
self-contained output directory ready for distribution to compatible clients.
"""

import json
import shutil
from pathlib import Path
from typing import Any

from src.pipelines.plugin_validate import run_plugin_validate


PLUGIN_ROOT_DEFAULT = Path(".agents")
EXPORT_DIR_DEFAULT = Path("dist/mloop-plugin")

# Files and dirs to include in the portable export
PORTABLE_COMPONENTS = ["plugin.json", "mcp.json", "skills"]


def run_plugin_export(project_name: str = None,
                      plugin_root: str | Path = None,
                      output_path: str | Path = None) -> dict[str, Any]:
    """
    Export a portable Agent Plugin package.

    Steps:
      1. Validate the plugin first (fail-fast if invalid)
      2. Copy portable components to the output directory
      3. Copy extension namespace directories
      4. Return export summary

    Args:
        project_name: Optional project name for context
        plugin_root: Source plugin root (default: .agents/)
        output_path: Output directory (default: dist/mloop-plugin/)

    Returns:
        Dictionary with export results
    """
    if plugin_root is None:
        plugin_root = PLUGIN_ROOT_DEFAULT
    else:
        plugin_root = Path(plugin_root)

    if output_path is None:
        output_path = EXPORT_DIR_DEFAULT
    else:
        output_path = Path(output_path)

    # Step 1: Validate first
    validation = run_plugin_validate(
        project_name=project_name,
        plugin_root=plugin_root,
        strict=False,
    )

    if validation["status"] != "PASS":
        return {
            "success": False,
            "reason": "Plugin validation failed — fix errors before exporting",
            "validation": validation,
        }

    # Step 2: Prepare output directory
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    copied_files: list[str] = []
    copied_skills: list[str] = []
    copied_namespaces: list[str] = []

    # Step 3: Copy plugin.json
    src_manifest = plugin_root / "plugin.json"
    if src_manifest.exists():
        shutil.copy2(src_manifest, output_path / "plugin.json")
        copied_files.append("plugin.json")

    # Step 4: Copy mcp.json
    src_mcp = plugin_root / "mcp.json"
    if src_mcp.exists():
        shutil.copy2(src_mcp, output_path / "mcp.json")
        copied_files.append("mcp.json")

    # Step 5: Copy skills/
    src_skills = plugin_root / "skills"
    if src_skills.exists() and src_skills.is_dir():
        dst_skills = output_path / "skills"
        shutil.copytree(src_skills, dst_skills)
        # Enumerate copied skills
        for entry in sorted(dst_skills.iterdir()):
            if entry.is_dir() and (entry / "SKILL.md").exists():
                copied_skills.append(entry.name)

    # Step 6: Copy extension namespace directories (reverse-domain pattern)
    for entry in sorted(plugin_root.iterdir()):
        if entry.is_dir() and "." in entry.name and not entry.name.startswith("."):
            # Looks like a reverse-domain namespace (e.g., com.nmedia.opencode)
            dst_ns = output_path / entry.name
            shutil.copytree(entry, dst_ns)
            copied_namespaces.append(entry.name)

    return {
        "success": True,
        "project": project_name or "default",
        "source": str(plugin_root),
        "output": str(output_path),
        "files_copied": copied_files,
        "skills_exported": copied_skills,
        "namespaces_exported": copied_namespaces,
        "summary": {
            "file_count": len(copied_files),
            "skill_count": len(copied_skills),
            "namespace_count": len(copied_namespaces),
        },
        "validation": validation,
    }
