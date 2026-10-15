"""
CodeLan Language Knowledge Base & File Rule Extractor.
Parses language files (README.md, grammar specs, .clan examples, custom docs)
and extracts syntax rules, valid builtins, lifecycle hooks, and forbidden tokens.
"""

import os
import re
from typing import Dict, List, Set, Any


class LanguageKnowledgeBase:
    """
    Extracts and manages CodeLan language knowledge from specification files.
    """
    def __init__(self, spec_file: str = "CODELAN_README.md"):
        self.spec_file = spec_file
        self.raw_content = ""
        self.builtins: Set[str] = set()
        self.lifecycle_hooks: Set[str] = {"setup", "update", "draw"}
        self.event_handlers: Set[str] = {"key_down", "mouse_down"}
        self.audio_effects: Set[str] = {"laser", "jump", "coin", "hit", "explosion", "powerup", "gameover", "click"}
        self.keywords: Set[str] = {
            "let", "fn", "return", "if", "else", "while", "for", "in", "repeat",
            "setup", "update", "draw", "on", "true", "false", "null", "nil", "and", "or", "not"
        }
        self.forbidden_hallucinations: Set[str] = {
            "def ", "import ", "from ", "class ", "function ", "var ", "console.log",
            "document.", "window.onload", "pygame.", "ctx.", "System.out", "public static",
            "elif", "lambda", "async", "await", "throw", "try", "catch"
        }
        self.builtin_signatures: Dict[str, Dict[str, Any]] = {}
        self.load_file(spec_file)

    def load_file(self, filepath: str) -> bool:
        """Loads and parses a language file."""
        if not os.path.exists(filepath):
            # Fallback to local default if given path is not found
            alt_path = os.path.join(os.path.dirname(__file__), filepath)
            if os.path.exists(alt_path):
                filepath = alt_path
            else:
                return False

        self.spec_file = filepath
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                self.raw_content = f.read()
        except Exception as e:
            print(f"Error reading file {filepath}: {e}")
            return False

        self._extract_knowledge()
        return True

    def _extract_knowledge(self):
        """Extracts language functions, keywords, arguments from the documentation."""
        # 1. Default standard builtins in CodeLan
        standard_builtins = {
            # Window & Global
            "window": {"min_args": 3, "max_args": 3, "desc": "Sets window title and canvas dimensions"},
            "fps": {"min_args": 1, "max_args": 1, "desc": "Sets target frames per second"},
            "time": {"min_args": 0, "max_args": 0, "desc": "Total elapsed game time"},
            # Graphics
            "clear": {"min_args": 0, "max_args": 1, "desc": "Clears canvas with color"},
            "color": {"min_args": 1, "max_args": 3, "desc": "Sets default fill/stroke color"},
            "rect": {"min_args": 4, "max_args": 7, "desc": "Draws rectangle"},
            "circle": {"min_args": 3, "max_args": 6, "desc": "Draws circle"},
            "oval": {"min_args": 4, "max_args": 7, "desc": "Draws oval"},
            "line": {"min_args": 4, "max_args": 6, "desc": "Draws line"},
            "triangle": {"min_args": 6, "max_args": 8, "desc": "Draws triangle"},
            "text": {"min_args": 3, "max_args": 7, "desc": "Renders text"},
            "text_centered": {"min_args": 3, "max_args": 5, "desc": "Renders centered text"},
            "grid": {"min_args": 0, "max_args": 2, "desc": "Draws background grid"},
            "camera": {"min_args": 2, "max_args": 2, "desc": "Offsets rendering camera"},
            # Input
            "key": {"min_args": 1, "max_args": 1, "desc": "True if key is held down"},
            "key_down": {"min_args": 1, "max_args": 1, "desc": "True only on frame key was pressed"},
            "mouse_down": {"min_args": 0, "max_args": 0, "desc": "True while left mouse is held"},
            "mouse_clicked": {"min_args": 0, "max_args": 0, "desc": "True only on frame mouse clicked"},
            # Audio
            "sound": {"min_args": 1, "max_args": 1, "desc": "Plays 8-bit procedural sound effect"},
            "beep": {"min_args": 2, "max_args": 2, "desc": "Plays frequency tone in Hz for ms"},
            # Collisions
            "collide_rect": {"min_args": 8, "max_args": 8, "desc": "Checks rectangle overlap"},
            "collide_circle": {"min_args": 6, "max_args": 6, "desc": "Checks circle intersection"},
            "collide_point_rect": {"min_args": 6, "max_args": 6, "desc": "Checks point inside rect"},
            "collide_point_circle": {"min_args": 5, "max_args": 5, "desc": "Checks point inside circle"},
            "distance": {"min_args": 4, "max_args": 4, "desc": "Euclidean distance between two points"},
            # Math
            "random": {"min_args": 2, "max_args": 2, "desc": "Random number between min and max"},
            "rand": {"min_args": 2, "max_args": 2, "desc": "Alias for random"},
            "random_choice": {"min_args": 1, "max_args": 1, "desc": "Random element from list"},
            "clamp": {"min_args": 3, "max_args": 3, "desc": "Restricts value between min and max"},
            "min": {"min_args": 1, "max_args": 99, "desc": "Smallest value"},
            "max": {"min_args": 1, "max_args": 99, "desc": "Largest value"},
            "abs": {"min_args": 1, "max_args": 1, "desc": "Absolute value"},
            "floor": {"min_args": 1, "max_args": 1, "desc": "Floor round"},
            "ceil": {"min_args": 1, "max_args": 1, "desc": "Ceiling round"},
            "round": {"min_args": 1, "max_args": 2, "desc": "Round number"},
            "sin": {"min_args": 1, "max_args": 1, "desc": "Sine in degrees"},
            "cos": {"min_args": 1, "max_args": 1, "desc": "Cosine in degrees"},
            "atan2": {"min_args": 2, "max_args": 2, "desc": "Arc tangent degrees"},
            "lerp": {"min_args": 3, "max_args": 3, "desc": "Linear interpolation"},
            "map_range": {"min_args": 5, "max_args": 5, "desc": "Re-maps value between ranges"},
            "rgb": {"min_args": 3, "max_args": 3, "desc": "Converts RGB to hex color string"},
            # Collections
            "len": {"min_args": 1, "max_args": 1, "desc": "Length of list or string"},
            "length": {"min_args": 1, "max_args": 1, "desc": "Alias for len"},
            "push": {"min_args": 2, "max_args": 2, "desc": "Appends item to list"},
            "append": {"min_args": 2, "max_args": 2, "desc": "Alias for push"},
            "pop": {"min_args": 1, "max_args": 2, "desc": "Removes and returns item at index"},
            "remove": {"min_args": 2, "max_args": 2, "desc": "Removes first occurrence of item"},
            "contains": {"min_args": 2, "max_args": 2, "desc": "True if item in collection"},
            "keys": {"min_args": 1, "max_args": 1, "desc": "List of dictionary keys"},
            "values": {"min_args": 1, "max_args": 1, "desc": "List of dictionary values"},
            "range": {"min_args": 2, "max_args": 3, "desc": "List of integers from start to end"},
            "str": {"min_args": 1, "max_args": 1, "desc": "Converts value to string"},
            "int": {"min_args": 1, "max_args": 1, "desc": "Converts value to integer"},
            "float": {"min_args": 1, "max_args": 1, "desc": "Converts value to float"},
            "bool": {"min_args": 1, "max_args": 1, "desc": "Converts value to bool"},
            "print": {"min_args": 1, "max_args": 99, "desc": "Prints to console"},
        }
        self.builtin_signatures = standard_builtins
        self.builtins = set(standard_builtins.keys())

        # 2. Extract dynamically from loaded file text
        # Look for function calls in backticks, e.g. `rect(...)`, `sound(...)`
        matches = re.findall(r'`([a-zA-Z_][a-zA-Z0-9_]*)\(([^)]*)\)`', self.raw_content)
        for name, args in matches:
            if name not in self.builtins:
                arg_count = len([a.strip() for a in args.split(",") if a.strip()]) if args.strip() else 0
                self.builtins.add(name)
                self.builtin_signatures[name] = {
                    "min_args": arg_count,
                    "max_args": arg_count + 2,
                    "desc": f"Discovered in {os.path.basename(self.spec_file)}"
                }

        # Look for sound effects mentioned in strings
        sound_matches = re.findall(r'"(laser|jump|coin|hit|explosion|powerup|gameover|click)"', self.raw_content)
        for s in sound_matches:
            self.audio_effects.add(s)

    def get_summary(self) -> Dict[str, Any]:
        """Returns structured summary of the knowledge base."""
        return {
            "source_file": os.path.basename(self.spec_file),
            "file_size": len(self.raw_content),
            "total_builtins": len(self.builtins),
            "builtins": sorted(list(self.builtins)),
            "lifecycle_hooks": sorted(list(self.lifecycle_hooks)),
            "audio_effects": sorted(list(self.audio_effects)),
            "keywords": sorted(list(self.keywords)),
            "forbidden_hallucinations": sorted(list(self.forbidden_hallucinations))
        }


# Global knowledge base singleton
knowledge_base = LanguageKnowledgeBase()
