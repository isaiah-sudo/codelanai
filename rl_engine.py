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
        # ---------------------------------------------------------
        # 5. INTENT & GAMEPLAY MECHANICS REWARDS
        # ---------------------------------------------------------
        # Controls check
        if "key(" in code or "key_down(" in code or "mouse_x" in code:
            report.game_mechanics.append("player_input")
            report.add_reward("Gameplay: Interactive player input handling detected", 10.0)

        # Collision detection check
        if any(c in code for c in ["collide_rect", "collide_circle", "distance(", "ball_x - ball_r"]):
            report.game_mechanics.append("collision_physics")
            report.add_reward("Gameplay: Collision detection & physics logic present", 10.0)

        # Score & UI text check
        if re.search(r'\bscore\b', code, re.I) and "text(" in code:
            report.game_mechanics.append("score_tracking")
            report.add_reward("Gameplay: Score tracking and HUD text rendering present", 10.0)

        # Visual FX & Juice (Particles, Screenshake)
        if "particles" in code and "circle(" in code:
            report.game_mechanics.append("particles")
            report.add_reward("Visual Juice: Particle system logic detected", 8.0)

        if any(k in code for k in ["shake", "camera("]):
            report.game_mechanics.append("screenshake")
            report.add_reward("Visual Juice: Screen shake / camera offset detected", 5.0)

        if any(k in code for k in ["high_score", "best_score", "highscore"]):
            report.game_mechanics.append("high_score")
            report.add_reward("Gameplay: High score persistence detected", 6.0)

        # Intent-specific verification
        if intent_spec:
            if intent_spec.get("require_sound") is True and not ("sound(" in code or "beep(" in code):
                report.add_punishment("Intent Violation: Sound was requested but not implemented", 15.0)
            if intent_spec.get("require_sound") is True and ("sound(" in code or "beep(" in code):
                report.add_reward("Intent Satisfied: Audio effects included as requested", 10.0)

            if intent_spec.get("genre") and intent_spec.get("genre") != "custom":
                genre = intent_spec["genre"]
                if genre == "space_shooter" and not any(k in code for k in ["ship", "bullet", "alien", "laser"]):
                    report.add_punishment("Intent Weakness: Missing space shooter entities (ship, bullets, aliens)", 10.0)
                elif genre == "pong" and not any(k in code for k in ["paddle", "ball", "p1_score"]):
                    report.add_punishment("Intent Weakness: Missing pong mechanics (paddle, ball, score)", 10.0)
                elif genre == "snake" and not any(k in code for k in ["snake", "food", "body", "tail"]):
                    report.add_punishment("Intent Weakness: Missing snake mechanics (snake, food)", 10.0)

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
        self.gamma: float = 0.85     # Discount factor
        self.epsilon: float = 0.20   # Exploration rate
        self.min_epsilon: float = 0.05
        self.epsilon_decay: float = 0.985

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
                    self.history = data.get("history", [])[-300:]
                    self.human_feedback_log = data.get("human_feedback_log", [])[-100:]
                    print(f"[RL Agent] Loaded model with {self.total_episodes} episodes, lifetime reward {self.total_reward_lifetime:.1f}")
                    return
            except Exception as e:
                print(f"[RL Agent] Could not load model file: {e}. Reinitializing.")

        self._initialize_defaults()

    def _initialize_defaults(self):
        """Initializes default Q-table and feature preference weights."""
        self.genre_weights = {
            "pong": 12.0,
            "snake": 12.0,
            "space_shooter": 15.0,
            "flappy": 12.0,
            "breakout": 14.0,
            "asteroid_dodger": 12.0,
            "platformer": 12.0,
            "clicker": 10.0,
            "custom": 10.0
        }
        self.feature_weights = {
            "sound_effects": 20.0,
            "particles": 15.0,
            "high_score": 12.0,
            "screenshake": 10.0,
            "smooth_controls": 15.0,
            "collision_audio": 15.0
        }
        self.q_table = {
            "lifecycle_structure": {
                "full_three_tier": 25.0,
                "missing_draw": -20.0,
                "missing_update": -20.0,
                "missing_setup": -20.0
            },
            "syntax_discipline": {
                "valid_codelan_let": 25.0,
                "foreign_var": -30.0,
                "foreign_func": -30.0
            },
            "feature_particles": {
                "enabled": 18.0,
                "disabled": 5.0
            },
            "feature_sound_effects": {
                "enabled": 22.0,
                "disabled": 2.0
            },
            "feature_high_score": {
                "enabled": 14.0,
                "disabled": 8.0
            },
            "feature_screenshake": {
                "enabled": 12.0,
                "disabled": 8.0
            }
        }
        self.total_episodes = 0
        self.total_reward_lifetime = 0.0
        self.history = []
        self.human_feedback_log = []
        self.save()

    def reset_weights(self):
        """Resets the RL model back to pristine initial state."""
        with self.lock:
            self._initialize_defaults()

    def choose_action(self, state_key: str, available_actions: List[str]) -> Tuple[str, bool]:
        """
        Epsilon-greedy action selection.
        Returns (chosen_action, is_exploration).
        """
        with self.lock:
            if not available_actions:
                return "", False

            # Exploration
            if random.random() < self.epsilon:
                return random.choice(available_actions), True

            # Exploitation: pick action with maximum Q-value
            if state_key not in self.q_table:
                self.q_table[state_key] = {}

            state_q = self.q_table[state_key]
            best_action = max(available_actions, key=lambda a: state_q.get(a, 0.0))
            return best_action, False

    def decide_feature(self, genre: str, feature_name: str, requested: Optional[bool] = None) -> Tuple[bool, bool]:
        """
        Decides whether to enable a gameplay feature using RL policy.
        If requested is explicitly specified by user (not None), it weighs heavily.
        Returns (is_enabled, is_exploration).
        """
        if requested is not None:
            return bool(requested), False

        state_key = f"feat_{genre}_{feature_name}"
        if state_key not in self.q_table:
            # Fall back to general feature state
            state_key = f"feature_{feature_name}"

        action, is_explore = self.choose_action(state_key, ["enabled", "disabled"])
        return (action == "enabled"), is_explore

    def save(self):
        """Persists model state to disk."""
        data = {
            "total_episodes": self.total_episodes,
            "total_reward_lifetime": round(self.total_reward_lifetime, 2),
            "epsilon": round(self.epsilon, 4),
            "genre_weights": self.genre_weights,
            "feature_weights": self.feature_weights,
            "q_table": self.q_table,
            "history": self.history[-300:],
            "human_feedback_log": self.human_feedback_log[-100:],
            "last_updated": datetime.now().isoformat()
        }
        try:
            with open(self.model_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[RL Agent] Error saving model: {e}")

    def update_step(self, state_key: str, action_key: str, reward: float):
        """
        Single Q-learning trial-and-error update:
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

    def update_from_trial(self, genre: str, decisions: Dict[str, Any], report: EvaluationReport):
        """
        Multi-dimensional reinforcement learning attribution update.
        Attributes specific rewards/punishments to the corresponding Q-states.
        """
        with self.lock:
            # 1. Syntax discipline
            syntax_action = decisions.get("syntax_action", "valid_codelan_let")
            syntax_reward = 25.0 if report.is_valid_syntax else -30.0
            self._update_q_raw("syntax_discipline", syntax_action, syntax_reward)

            # 2. Lifecycle structure
            lifecycle_count = len(report.matched_lifecycle)
            if lifecycle_count == 3:
                self._update_q_raw("lifecycle_structure", "full_three_tier", 25.0)
            else:
                self._update_q_raw("lifecycle_structure", "partial_lifecycle", -20.0)

            # 3. Features attribution
            features_dict = decisions.get("features", {})
            for feat_name, is_enabled in features_dict.items():
                state_key = f"feat_{genre}_{feat_name}"
                act = "enabled" if is_enabled else "disabled"
                
                # Check if feature contributed positive points
                feat_points = 0.0
                if is_enabled:
                    if feat_name == "particles" and "particles" in report.game_mechanics:
                        feat_points = 10.0
                    elif feat_name == "sound_effects" and report.matched_builtins:
                        feat_points = 12.0
                    elif feat_name == "screenshake" and "screenshake" in report.game_mechanics:
                        feat_points = 8.0
                    elif feat_name == "high_score" and "high_score" in report.game_mechanics:
                        feat_points = 8.0
                    else:
                        feat_points = 2.0
                else:
                    feat_points = 0.0

                self._update_q_raw(state_key, act, feat_points)

                # Update global feature weight
                if feat_name in self.feature_weights:
                    delta = (feat_points - 3.0) * 0.1
                    self.feature_weights[feat_name] = round(max(2.0, self.feature_weights[feat_name] + delta), 2)

            # 4. Genre policy weight
            if genre in self.genre_weights:
                reward_factor = 0.1 if report.is_valid_syntax else -0.2
                self.genre_weights[genre] = round(max(2.0, self.genre_weights[genre] + report.total_reward * reward_factor * 0.05), 2)

            # 5. Decay epsilon
            if self.epsilon > self.min_epsilon:
                self.epsilon = max(self.min_epsilon, self.epsilon * self.epsilon_decay)

            self.total_episodes += 1
            self.total_reward_lifetime += report.total_reward

    def _update_q_raw(self, state_key: str, action_key: str, reward: float):
        """Internal helper to update Q-table without incrementing global episodes."""
        if state_key not in self.q_table:
            self.q_table[state_key] = {}
        current_q = self.q_table[state_key].get(action_key, 0.0)
        new_q = current_q + self.alpha * (reward - current_q)
        self.q_table[state_key][action_key] = round(new_q, 3)

    def record_human_feedback(self, game_genre: str, reward_points: float, note: str = ""):
        """
        Records human reinforcement (reward/punishment) directly into policy weights.
        """
        with self.lock:
            # Update genre weight
            if game_genre in self.genre_weights:
                self.genre_weights[game_genre] = max(1.0, round(self.genre_weights[game_genre] + reward_points * 0.5, 2))

            # Update Q-values for this genre
            state_key = f"human_feedback_{game_genre}"
            self._update_q_raw(state_key, "generation_quality", reward_points)

            # If rewarded, boost features
            feedback_mult = 0.2 if reward_points > 0 else -0.3
            for f in self.feature_weights:
                self.feature_weights[f] = max(2.0, round(self.feature_weights[f] + feedback_mult, 2))

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

    def get_learning_curve(self, max_points: int = 100) -> Dict[str, Any]:
        """Returns historical data points for real-time learning curve plotting."""
        with self.lock:
            entries = self.history[-max_points:] if self.history else []
            episodes = []
            rewards = []
            rolling_avg = []
            running_sum = 0.0

            for idx, item in enumerate(entries):
                ep = item.get("episode", idx + 1)
                rew = float(item.get("reward", 0.0))
                episodes.append(ep)
                rewards.append(rew)
                running_sum += rew
                rolling_avg.append(round(running_sum / (idx + 1), 2))

            return {
                "episodes": episodes,
                "rewards": rewards,
                "rolling_avg": rolling_avg
            }


# Global RL Agent singleton
rl_agent = CodeLanRLAgent()

