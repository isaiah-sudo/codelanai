"""
Automated Reinforcement Learning Trial-and-Error Trainer.
Feeds a language specification file into the AI, runs trial-and-error code generation
episodes, verifies code against compiler and file rules, awards rewards or punishments,
and trains the AI's Q-values and policy weights.
"""

import os
import time
import random
from typing import Dict, List, Any, Callable, Optional

from knowledge_base import knowledge_base, LanguageKnowledgeBase
from rl_engine import rl_agent, CodeLanRLAgent, CodeLanEvaluator
from game_generator import game_generator, CodeLanGameGenerator


TRAINING_CHALLENGES = [
    {"prompt": "Make a retro space shooter with laser sounds and exploding aliens", "genre": "space_shooter", "require_sound": True},
    {"prompt": "Create a 2-player neon pong game with bouncing ball and paddle sounds", "genre": "pong", "require_sound": True},
    {"prompt": "Make a cyber snake game that eats glowing food pellets", "genre": "snake", "require_sound": True},
    {"prompt": "Build a flappy bird game with gravity and pipe obstacles", "genre": "flappy", "require_sound": True},
    {"prompt": "Make a breakout brick breaker with colored bricks and bounce physics", "genre": "breakout", "require_sound": True},
    {"prompt": "Dodge falling asteroids with arrow keys and collect energy gems", "genre": "asteroid_dodger", "require_sound": True},
    {"prompt": "Create a vertical platformer where player bounces higher and higher", "genre": "platformer", "require_sound": True},
    {"prompt": "Click on fast disappearing targets for high score", "genre": "clicker", "require_sound": True},
    {"prompt": "Universal arcade orb collector with roaming hazards", "genre": "custom", "require_sound": True},
    {"prompt": "Fast paced space battle with boss shields and lasers", "genre": "space_shooter", "require_sound": True},
    {"prompt": "Neon paddle battle with speed multipliers and coin sounds", "genre": "pong", "require_sound": True},
    {"prompt": "Retro dungeon crawler dodging magma hazard orbs", "genre": "custom", "require_sound": True},
    {"prompt": "High speed precision rocket obstacle course", "genre": "flappy", "require_sound": True},
    {"prompt": "Rainbow brick breaker with laser powerups and sound fx", "genre": "breakout", "require_sound": True},
    {"prompt": "Glowing synthwave snake in an infinite grid arena", "genre": "snake", "require_sound": True},
]


class AutomatedRLTrainer:
    """
    Manages automated trial-and-error training sessions based on language files.
    """
    def __init__(self, agent: CodeLanRLAgent = rl_agent, kb: LanguageKnowledgeBase = knowledge_base):
        self.agent = agent
        self.kb = kb
        self.evaluator = CodeLanEvaluator(kb)
        self.generator = CodeLanGameGenerator(agent)
        self.is_training = False

    def stop_training(self):
        """Signals the training loop to stop."""
        self.is_training = False

    def train_step(
        self,
        challenge: Optional[Dict[str, Any]] = None,
        force_mutation: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a single trial episode:
        1. Selects or takes a challenge prompt.
        2. Synthesizes game code using RL policy decisions.
        3. Optionally tests exploratory perturbations (mutations) to learn boundary rules.
        4. Evaluates against AST compiler and language constraints.
        5. Updates multi-dimensional Q-table and policy weights.
        6. Returns rich diagnostics.
        """
        if not challenge:
            challenge = random.choice(TRAINING_CHALLENGES)

        prompt = challenge["prompt"]
        genre = challenge.get("genre", "custom")

        # Synthesize code (guided by current RL policy)
        code, intent = self.generator.generate_game(prompt)

        # Decide whether to test deliberate syntax perturbations during exploration
        # to teach the agent strict language discipline
        decisions = {
            "syntax_action": "valid_codelan_let",
            "features": intent.decisions
        }

        code_trial = code
        is_mutation_tested = False
        mutation_desc = ""

        # Deliberate mutation test during exploration:
        # e.g., foreign keywords from Python / JS / Java to verify punishment learning
        should_mutate = (force_mutation is not None) or (
            random.random() < 0.12 and self.agent.epsilon > 0.08
        )

        if should_mutate:
            is_mutation_tested = True
            mut_type = force_mutation or random.choice(["var", "func", "console", "def", "missing_draw"])
            if mut_type == "var":
                code_trial = code.replace("let ", "var ", 1)
                decisions["syntax_action"] = "foreign_var"
                mutation_desc = "Exploratory test: Foreign 'var' keyword substituted"
            elif mut_type == "func":
                code_trial = code.replace("fn ", "function ", 1)
                decisions["syntax_action"] = "foreign_func"
                mutation_desc = "Exploratory test: Foreign 'function' keyword substituted"
            elif mut_type == "console":
                code_trial = "console.log('debug')\n" + code
                decisions["syntax_action"] = "foreign_console"
                mutation_desc = "Exploratory test: Foreign 'console.log' injected"
            elif mut_type == "def":
                code_trial = code.replace("fn ", "def ", 1)
                decisions["syntax_action"] = "foreign_def"
                mutation_desc = "Exploratory test: Foreign 'def' keyword substituted"
            elif mut_type == "missing_draw":
                # Remove draw block
                idx = code.find("draw {")
                if idx != -1:
                    code_trial = code[:idx]
                    decisions["syntax_action"] = "missing_draw"
                    mutation_desc = "Exploratory test: 'draw' lifecycle removed"

        # Evaluate against language spec and compiler AST
        report = self.evaluator.evaluate(code_trial, intent_spec=challenge)

        # Multi-dimensional reinforcement learning update
        self.agent.update_from_trial(genre, decisions, report)

        step_record = {
            "episode": self.agent.total_episodes,
            "prompt": prompt,
            "genre": genre,
            "reward": round(report.total_reward, 2),
            "is_valid_syntax": report.is_valid_syntax,
            "syntax_error": report.syntax_error,
            "matched_builtins": report.matched_builtins,
            "rewards_breakdown": report.rewards_breakdown,
            "punishments_breakdown": report.punishments_breakdown,
            "decisions": decisions,
            "is_mutation_tested": is_mutation_tested,
            "mutation_desc": mutation_desc,
            "code_snippet": "\n".join(code_trial.strip().splitlines()[:16])
        }

        self.agent.history.append(step_record)
        return step_record

    def train_on_file(
        self,
        filepath: str,
        episodes: int = 25,
        delay_seconds: float = 0.04,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Ingests a language file and executes trial-and-error episodes.
        """
        self.is_training = True
        success_load = self.kb.load_file(filepath)
        if not success_load:
            self.is_training = False
            return {
                "success": False,
                "error": f"Failed to load file '{filepath}'. Please check the file path."
            }

        total_reward_session = 0.0
        session_history = []
        syntax_passed_count = 0

        for ep in range(1, episodes + 1):
            if not self.is_training:
                break

            step_record = self.train_step()
            session_history.append(step_record)

            total_reward_session += step_record["reward"]
            if step_record["is_valid_syntax"]:
                syntax_passed_count += 1

            if progress_callback:
                progress_callback({
                    "current_episode": ep,
                    "total_episodes": episodes,
                    "global_episode": step_record["episode"],
                    "latest_reward": step_record["reward"],
                    "is_valid_syntax": step_record["is_valid_syntax"],
                    "genre": step_record["genre"],
                    "prompt": step_record["prompt"],
                    "rewards_count": len(step_record["rewards_breakdown"]),
                    "punishments_count": len(step_record["punishments_breakdown"]),
                    "session_avg_reward": round(total_reward_session / ep, 2),
                    "accuracy": round((syntax_passed_count / ep) * 100.0, 1),
                    "step_record": step_record
                })

            if delay_seconds > 0:
                time.sleep(delay_seconds)

        self.agent.save()
        self.is_training = False

        avg_reward = (total_reward_session / len(session_history)) if session_history else 0.0
        accuracy = (syntax_passed_count / len(session_history) * 100.0) if session_history else 0.0

        return {
            "success": True,
            "file": os.path.basename(filepath),
            "episodes_trained": len(session_history),
            "total_reward_session": round(total_reward_session, 2),
            "avg_reward": round(avg_reward, 2),
            "accuracy_percent": round(accuracy, 1),
            "kb_builtins_known": len(self.kb.builtins),
            "session_history": session_history[-10:]
        }


# Global automated trainer singleton
trainer = AutomatedRLTrainer()
