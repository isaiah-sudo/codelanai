"""
Main Unified Executable Entry Point for CodeLan AI.
Launches the Web Studio GUI by default, or accepts CLI arguments.
"""

import sys
import os
from pathlib import Path

# Add bundle directory or current directory to sys.path
bundle_dir = getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)
sys.path.insert(0, str(bundle_dir))

from codelan_ai_cli import main as cli_main

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Default with no arguments: start the Studio UI
        from app import main as run_web_app
        run_web_app()
    else:
        cli_main()
