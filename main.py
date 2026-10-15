"""
Main Unified Executable Entry Point for CodeLan AI.
Launches the Native Desktop Window Studio by default, Web Studio via --web, or accepts CLI arguments.
"""

import sys
import os
from pathlib import Path

# Add bundle directory or current directory to sys.path
bundle_dir = getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)
sys.path.insert(0, str(bundle_dir))

from codelan_ai_cli import main as cli_main


def run_desktop():
    """Launches the native PyQt6 desktop application window."""
    try:
        from desktop_app import main as run_desktop_app
        run_desktop_app()
    except Exception as ex:
        print(f"[LAUNCHER] Desktop window launch error: {ex}. Falling back to web studio...")
        from app import main as run_web_app
        run_web_app()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Default with no arguments: Launch the native desktop window
        run_desktop()
    elif "--web" in sys.argv:
        # Explicit web studio requested
        from app import main as run_web_app
        run_web_app()
    elif "--desktop" in sys.argv:
        run_desktop()
    else:
        cli_main()
