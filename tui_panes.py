#!/usr/bin/env python3
"""
Root convenience shortcut for mLoop Herdr TUI Panes.
Forwards execution to plugins/mloop-herdr-plugin/tui_panes.py.
"""
import sys
import subprocess
from pathlib import Path

plugin_tui = Path(__file__).parent / "plugins" / "mloop-herdr-plugin" / "tui_panes.py"

if __name__ == "__main__":
    if plugin_tui.exists():
        sys.exit(subprocess.call([sys.executable, str(plugin_tui)] + sys.argv[1:]))
    else:
        print(f"Error: {plugin_tui} not found.")
        sys.exit(1)
