"""
Reinforcement Learning (Trial and Error) Engine for CodeLan.
Implements environment evaluation, reward/punishment calculation,
Q-table / policy updates, and human-in-the-loop feedback persistence.
"""

import os
import re
import json
import random
import threading
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

from knowledge_base import knowledge_base, LanguageKnowledgeBase

# Import CodeLan parser and lexer
try:
    from codelan.lexer import Lexer, LexerError
    from codelan.parser import Parser, ParserError
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from codelan.lexer import Lexer, LexerError
    from codelan.parser import Parser, ParserError


class EvaluationReport:
    """Detailed score and diagnostics from evaluating a CodeLan program."""
    def __init__(self):
        self.total_reward: float = 0.0
        self.is_valid_syntax: bool = False
        self.syntax_error: Optional[str] = None
        self.rewards_breakdown: List[Dict[str, Any]] = []
        self.punishments_breakdown: List[Dict[str, Any]] = []
        self.matched_builtins: List[str] = []
        self.matched_lifecycle: List[str] = []
        self.hallucinations: List[str] = []
        self.game_mechanics: List[str] = []

    def add_reward(self, reason: str, points: float):
        self.total_reward += points
        self.rewards_breakdown.append({"reason": reason, "points": points})

    def add_punishment(self, reason: str, points: float):
        self.total_reward -= abs(points)
        self.punishments_breakdown.append({"reason": reason, "points": -abs(points)})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_reward": round(self.total_reward, 2),
            "is_valid_syntax": self.is_valid_syntax,
            "syntax_error": self.syntax_error,
            "rewards": self.rewards_breakdown,
            "punishments": self.punishments_breakdown,
            "matched_builtins": self.matched_builtins,
            "matched_lifecycle": self.matched_lifecycle,
            "hallucinations": self.hallucinations,
            "game_mechanics": self.game_mechanics
        }


class CodeLanEvaluator:
    """
    Evaluates CodeLan code against language rules, syntax parser,
    and game design principles to calculate rewards or punishments.
    """
    def __init__(self, kb: LanguageKnowledgeBase = knowledge_base):
        self.kb = kb

    def evaluate(self, code: str, intent_spec: Optional[Dict[str, Any]] = None) -> EvaluationReport:
        report = EvaluationReport()
        if not code or not code.strip():
            report.add_punishment("Empty code provided", 50.0)
            return report

        # ---------------------------------------------------------
        # 1. HALLUCINATION CHECK (Foreign Language Penalties)
        # ---------------------------------------------------------
        for forbidden in self.kb.forbidden_hallucinations:
            if forbidden in code:
                count = code.count(forbidden)
                penalty = 20.0 * count
                report.hallucinations.append(forbidden.strip())
                report.add_punishment(f"Hallucination: used non-CodeLan syntax '{forbidden.strip()}' ({count}x)", penalty)

        # ---------------------------------------------------------
        # 2. LEXICAL & SYNTACTIC VALIDATION (Compiler Trial)
        # ---------------------------------------------------------
        try:
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            parser = Parser(tokens, filename="ai_trial.clan")
            ast_program = parser.parse()
            report.is_valid_syntax = True
            report.add_reward("Syntax Passed: AST compiled with zero errors", 25.0)
        except LexerError as le:
            report.is_valid_syntax = False
            report.syntax_error = f"Lexer Error: {le}"
            report.add_punishment(f"Syntax Error (Lexer): {le}", 30.0)
        except ParserError as pe:
            report.is_valid_syntax = False
            report.syntax_error = f"Parser Error: {pe}"
            report.add_punishment(f"Syntax Error (Parser): {pe}", 30.0)
        except Exception as ex:
            report.is_valid_syntax = False
            report.syntax_error = f"Compilation Error: {ex}"
            report.add_punishment(f"General Compilation Error: {ex}", 30.0)

        # ---------------------------------------------------------
        # 3. LIFECYCLE HOOKS (setup, update, draw)
        # ---------------------------------------------------------
        has_setup = bool(re.search(r'\bsetup\s*\{', code))
        has_update = bool(re.search(r'\bupdate\s*\{', code))
        has_draw = bool(re.search(r'\bdraw\s*\{', code))

        if has_setup:
            report.matched_lifecycle.append("setup")
            report.add_reward("Lifecycle: 'setup { ... }' block present", 10.0)
            if "window(" in code:
                report.add_reward("Setup: window() initialized", 5.0)
            if "fps(" in code:
                report.add_reward("Setup: fps() frame rate set", 5.0)
        else:
            report.add_punishment("Missing core lifecycle: 'setup { ... }'", 15.0)

        if has_update:
            report.matched_lifecycle.append("update")
            report.add_reward("Lifecycle: 'update { ... }' logic block present", 10.0)
        else:
            report.add_punishment("Missing core lifecycle: 'update { ... }'", 15.0)

        if has_draw:
            report.matched_lifecycle.append("draw")
            report.add_reward("Lifecycle: 'draw { ... }' rendering block present", 10.0)
            if "clear(" in code:
                report.add_reward("Draw: clear() background canvas call present", 5.0)
        else:
            report.add_punishment("Missing core lifecycle: 'draw { ... }'", 15.0)

        # ---------------------------------------------------------
        # 4. BUILT-IN FUNCTIONS REWARD (From Language File)
        # ---------------------------------------------------------
        found_builtins = set()
        for b_name in self.kb.builtins:
            pattern = r'\b' + re.escape(b_name) + r'\s*\('
            if re.search(pattern, code):
                found_builtins.add(b_name)

        for b_name in sorted(found_builtins):
            report.matched_builtins.append(b_name)
            report.add_reward(f"Language built-in verified: '{b_name}()'", 3.0)

        # Audio effects check
        sound_calls = re.findall(r'\bsound\s*\(\s*["\']([^"\']+)["\']\s*\)', code)
        for s in sound_calls:
            if s in self.kb.audio_effects:
                report.add_reward(f"Procedural 8-bit sound verified: sound('{s}')", 5.0)
            else:
                report.add_punishment(f"Unknown sound effect name: sound('{s}')", 8.0)

        # ---------------------------------------------------------
        # 5. INTENT & GAMEPLAY MECHANICS REWARDS
        # ---------------------------------------------------------
        # Controls check
        if "key(" in code or "key_down(" in code or "mouse_x" in code:
            report.game_mechanics.append("player_input")
            report.add_reward("Gameplay: Interactive player input handling detected", 10.0)

        # Collision detection check
        if any(c in code for c in ["collide_rect", "collide_circle", "distance("]):
            report.game_mechanics.append("collision_physics")
            report.add_reward("Gameplay: Collision detection & physics logic present", 10.0)

        # Score & UI text check
        if re.search(r'\bscore\b', code, re.I) and "text(" in code:
            report.game_mechanics.append("score_tracking")
            report.add_reward("Gameplay: Score tracking and HUD text rendering present", 10.0)

        # Intent-specific verification
        if intent_spec:
            if intent_spec.get("require_sound") and not ("sound(" in code or "beep(" in code):
                report.add_punishment("Intent Violation: Sound was requested but not implemented", 15.0)
            if intent_spec.get("require_sound") and ("sound(" in code or "beep(" in code):
                report.add_reward("Intent Satisfied: Audio effects included as requested", 10.0)

            if intent_spec.get("genre") and intent_spec.get("genre") != "custom":
                genre = intent_spec["genre"]
                if genre in ["space", "shooter"] and not ("ship" in code or "bullet" in code or "alien" in code or "enemy" in code):
                    report.add_punishment("Intent Weakness: Missing space shooter entities (ship, bullets, enemies)", 10.0)

        return report


class CodeLanRLAgent:
    """
    Reinforcement Learning Agent that maintains Q-values, policy weights,
    experience replay, and training trial-and-error sessions.
    """
    def __init__(self, model_file: str = "codelan_rl_model.json", kb: LanguageKnowledgeBase = knowledge_base):
        self.model_file = os.path.join(os.path.dirname(__file__), model_file)
        self.kb = kb
        self.evaluator = CodeLanEvaluator(kb)
        self.lock = threading.Lock()

        # RL Hyperparameters
        self.alpha: float = 0.15     # Learning rate
        self.gamma: float = 0.90     # Discount factor
        self.epsilon: float = 0.20   # Exploration rate
        self.min_epsilon: float = 0.05
        self.epsilon_decay: float = 0.98

        # State-Action Q-Table & Policy weights
        self.q_table: Dict[str, Dict[str, float]] = {}
        self.genre_weights: Dict[str, float] = {}
        self.feature_weights: Dict[str, float] = {}

        # Tracking metrics
        self.total_episodes: int = 0
        self.total_reward_lifetime: float = 0.0
        self.history: List[Dict[str, Any]] = []
        self.human_feedback_log: List[Dict[str, Any]] = []

        self._load_or_initialize()

    def _load_or_initialize(self):
        """Loads saved RL model weights or initializes default policy."""
        if os.path.exists(self.model_file):
            try:
                with open(self.model_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.q_table = data.get("q_table", {})
                    self.genre_weights = data.get("genre_weights", {})
                    self.feature_weights = data.get("feature_weights", {})
                    self.total_episodes = data.get("total_episodes", 0)
                    self.total_reward_lifetime = data.get("total_reward_lifetime", 0.0)
                    self.epsilon = data.get("epsilon", self.epsilon)
                    self.history = data.get("history", [])[-200:]
                    self.human_feedback_log = data.get("human_feedback_log", [])[-50:]
                    print(f"[RL Agent] Loaded model with {self.total_episodes} episodes, lifetime reward {self.total_reward_lifetime:.1f}")
                    return
            except Exception as e:
                print(f"[RL Agent] Could not load model file: {e}. Reinitializing.")

        self._initialize_defaults()

    def _initialize_defaults(self):
        """Initializes default Q-table and feature preference weights."""
        self.genre_weights = {
            "pong": 10.0,
            "snake": 10.0,
            "space_shooter": 10.0,
            "flappy": 10.0,
            "breakout": 10.0,
            "asteroid_dodger": 10.0,
            "platformer": 10.0,
            "clicker": 10.0,
            "custom": 10.0
        }
        self.feature_weights = {
            "sound_effects": 15.0,
            "smooth_controls": 15.0,
            "score_display": 15.0,
            "particles": 12.0,
            "collision_audio": 14.0,
            "high_score": 10.0,
            "procedural_speed": 10.0
        }
        # Initial Q-values for syntax decisions
        self.q_table = {
            "lifecycle_structure": {
                "full_three_tier": 25.0,
                "missing_draw": -20.0,
                "missing_update": -20.0,
                "missing_setup": -20.0
            },
            "drawing_paradigm": {
                "clear_and_shapes": 20.0,
                "unbuffered_draw": -10.0
            },
            "audio_trigger": {
                "procedural_sound": 15.0,
                "missing_audio": 2.0
            }
        }
        self.save()

    def save(self):
        """Persists model state to disk."""
        data = {
            "total_episodes": self.total_episodes,
            "total_reward_lifetime": round(self.total_reward_lifetime, 2),
            "epsilon": round(self.epsilon, 4),
            "genre_weights": self.genre_weights,
            "feature_weights": self.feature_weights,
            "q_table": self.q_table,
            "history": self.history[-200:],
            "human_feedback_log": self.human_feedback_log[-50:],
            "last_updated": datetime.now().isoformat()
        }
        try:
            with open(self.model_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[RL Agent] Error saving model: {e}")

    def update_step(self, state_key: str, action_key: str, reward: float):
        """
        Q-learning trial-and-error update:
        Q(s, a) = Q(s, a) + alpha * (reward - Q(s, a))
        """
        with self.lock:
            if state_key not in self.q_table:
                self.q_table[state_key] = {}
            current_q = self.q_table[state_key].get(action_key, 0.0)
            new_q = current_q + self.alpha * (reward - current_q)
            self.q_table[state_key][action_key] = round(new_q, 3)

            # Decay exploration rate
            if self.epsilon > self.min_epsilon:
                self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

            self.total_episodes += 1
            self.total_reward_lifetime += reward

    def record_human_feedback(self, game_genre: str, reward_points: float, note: str = ""):
        """
        Records human reinforcement (reward/punishment) directly into policy weights.
        """
        with self.lock:
            # Update genre weight
            if game_genre in self.genre_weights:
                self.genre_weights[game_genre] = max(1.0, self.genre_weights[game_genre] + reward_points * 0.5)

            # Update general Q-learning state
            state_key = f"human_feedback_{game_genre}"
            action_key = "generation_quality"
            self.update_step(state_key, action_key, reward_points)

            feedback_record = {
                "timestamp": datetime.now().isoformat(),
                "genre": game_genre,
                "reward_points": reward_points,
                "note": note,
                "status": "rewarded" if reward_points > 0 else "punished"
            }
            self.human_feedback_log.append(feedback_record)
            self.save()

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics for UI display."""
        with self.lock:
            recent_rewards = [h["reward"] for h in self.history[-30:]] if self.history else [0.0]
            avg_recent_reward = sum(recent_rewards) / len(recent_rewards) if recent_rewards else 0.0
            success_count = sum(1 for h in self.history[-50:] if h.get("is_valid_syntax", False))
            recent_total = min(len(self.history), 50)
            accuracy = (success_count / recent_total * 100.0) if recent_total > 0 else 100.0

            return {
                "total_episodes": self.total_episodes,
                "total_reward_lifetime": round(self.total_reward_lifetime, 1),
                "avg_recent_reward": round(avg_recent_reward, 1),
                "accuracy_percent": round(accuracy, 1),
                "epsilon": round(self.epsilon, 3),
                "total_q_states": len(self.q_table),
                "genre_weights": self.genre_weights,
                "feature_weights": self.feature_weights,
                "recent_history": self.history[-15:],
                "human_feedback_count": len(self.human_feedback_log)
            }


# Global RL Agent singleton
rl_agent = CodeLanRLAgent()
