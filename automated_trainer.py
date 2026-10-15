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

    def train_on_file(
        self,
        filepath: str,
        episodes: int = 25,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Ingests a file about the language and runs trial-and-error episodes.
        """
        self.is_training = True
        success_load = self.kb.load_file(filepath)
        if not success_load:
            self.is_training = False
            return {
                "success": False,
                "error": f"Failed to load file '{filepath}'. Please check the file path."
            }

        # Training challenge prompts to exercise the AI across genres and syntax
        training_challenges = [
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
        ]

        total_reward_session = 0.0
        session_history = []
        syntax_passed_count = 0

        for ep in range(1, episodes + 1):
            if not self.is_training:
                break

            challenge = random.choice(training_challenges)
            
            # --- Trial: Synthesize code ---
            code, intent = self.generator.generate_game(challenge["prompt"])

            # Introduce occasional exploratory perturbations during trial
            # to verify reward/punishment sensitivity
            if random.random() < 0.05 and self.agent.epsilon > 0.1:
                # Deliberate mutation test
                code_trial = code.replace("let ", "var ")  # Introduces a punished flaw
            else:
                code_trial = code

            # --- Evaluation against the language file and compiler ---
            report = self.evaluator.evaluate(code_trial, intent_spec=challenge)

            # --- Reinforcement Learning Update ---
            # Update Q-table state for this genre & structure
            state_key = f"genre_{intent.genre}"
            action_key = "standard_lifecycle" if report.is_valid_syntax else "syntax_flaw"
            self.agent.update_step(state_key, action_key, report.total_reward)

            total_reward_session += report.total_reward
            if report.is_valid_syntax:
                syntax_passed_count += 1

            # Log step
            step_record = {
                "episode": ep,
                "prompt": challenge["prompt"],
                "genre": intent.genre,
                "reward": report.total_reward,
                "is_valid_syntax": report.is_valid_syntax,
                "matched_builtins": report.matched_builtins,
                "rewards_breakdown": report.rewards_breakdown,
                "punishments_breakdown": report.punishments_breakdown,
                "syntax_error": report.syntax_error
            }
            session_history.append(step_record)
            self.agent.history.append(step_record)

            # Fire callback if provided
            if progress_callback:
                progress_callback({
                    "current_episode": ep,
                    "total_episodes": episodes,
                    "latest_reward": round(report.total_reward, 2),
                    "is_valid_syntax": report.is_valid_syntax,
                    "genre": intent.genre,
                    "rewards_count": len(report.rewards_breakdown),
                    "punishments_count": len(report.punishments_breakdown),
                    "session_avg_reward": round(total_reward_session / ep, 2),
                    "accuracy": round((syntax_passed_count / ep) * 100.0, 1)
                })

            time.sleep(0.04)  # Small pause for interactive training perception

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
