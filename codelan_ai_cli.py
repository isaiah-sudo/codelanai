"""
CodeLan AI Command-Line Interface.
Train with Reinforcement Learning on language files, generate games from prompts,
check syntax, and inspect learned model weights.
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from knowledge_base import knowledge_base
from rl_engine import rl_agent, CodeLanEvaluator
from game_generator import game_generator
from automated_trainer import trainer
from app import main as run_web_app


def cmd_train(args):
    filepath = args.file
    episodes = args.episodes
    print(f"\n🧠 [RL TRAINER] Starting Trial-and-Error Training...")
    print(f"📖 Language File: {filepath}")
    print(f"🔄 Episodes: {episodes}\n")

    def progress(p):
        status = "✓" if p["is_valid_syntax"] else "✕"
        print(f"Episode {p['current_episode']:2d}/{p['total_episodes']:2d} [{p['genre']}] {status} Reward: {p['latest_reward']:+5.1f} | Avg: {p['session_avg_reward']:+5.1f} | Acc: {p['accuracy']}%%")

    res = trainer.train_on_file(filepath=filepath, episodes=episodes, progress_callback=progress)
    if res.get("success"):
        print(f"\n✨ Training Complete!")
        print(f"   - Total Episodes: {res['episodes_trained']}")
        print(f"   - Total Reward: {res['total_reward_session']:+.1f}")
        print(f"   - Average Reward: {res['avg_reward']:+.1f}")
        print(f"   - Compiler Accuracy: {res['accuracy_percent']}%")
        print(f"   - Discovered Builtins: {res['kb_builtins_known']}")
    else:
        print(f"\n❌ Training Error: {res.get('error')}")


def cmd_generate(args):
    prompt = args.prompt
    print(f"\n🎨 [AI GENERATOR] Synthesizing game from prompt: '{prompt}'...")
    code, intent = game_generator.generate_game(prompt)

    evaluator = CodeLanEvaluator(knowledge_base)
    report = evaluator.evaluate(code, intent_spec={"genre": intent.genre, "require_sound": intent.require_sound})

    out_file = args.output or f"{intent.genre}.clan"
    Path(out_file).write_text(code, encoding="utf-8")

    print(f"✨ Game synthesized: {intent.title} (Genre: {intent.genre})")
    print(f"💾 Saved code to: {out_file}")
    print(f"📊 Syntax Passed: {'YES' if report.is_valid_syntax else 'NO'}")
    print(f"🏆 Total RL Reward: {report.total_reward:+.1f} points")
    print(f"   - Verified Built-ins: {', '.join(report.matched_builtins)}")

    if args.play:
        print(f"\n▶ Launching game in desktop runner...")
        import subprocess
        subprocess.run([sys.executable, "-m", "codelan.cli", "run", out_file])


def cmd_stats(args):
    stats = rl_agent.get_stats()
    print("\n=======================================================")
    print("📊 CODELAN AI REINFORCEMENT LEARNING STATS")
    print("=======================================================")
    print(f"Total Lifetime Episodes:   {stats['total_episodes']}")
    print(f"Lifetime Reward Accumulated: {stats['total_reward_lifetime']:+.1f}")
    print(f"Recent Average Reward:     {stats['avg_recent_reward']:+.1f}")
    print(f"Compilation Accuracy Rate: {stats['accuracy_percent']}%")
    print(f"Exploration Rate (Epsilon):{stats['epsilon']}")
    print(f"Learned Q-States:          {stats['total_q_states']}")
    print(f"Human Feedback Logs:       {stats['human_feedback_count']}")
    print("\nGenre Policy Weights:")
    for g, w in stats['genre_weights'].items():
        print(f"  • {g:18s}: {w:.1f}")
    print("=======================================================\n")


def cmd_reward(args):
    genre = args.genre
    points = args.points
    note = args.note or ""
    rl_agent.record_human_feedback(genre, points, note)
    action = "Rewarded" if points > 0 else "Punished"
    print(f"\n{action} AI for genre '{genre}' with {points:+.1f} points! (Note: {note})")
    print(f"New weight for '{genre}': {rl_agent.genre_weights.get(genre, 0.0):.1f}")


def main():
    parser = argparse.ArgumentParser(description="CodeLan AI: Reinforcement Learning Game Maker")
    subparsers = parser.add_subparsers(dest="command")

    # Serve (Web UI)
    subparsers.add_parser("serve", help="Launch the interactive web studio dashboard")

    # Train
    train_p = subparsers.add_parser("train", help="Train with Trial and Error using a language file")
    train_p.add_argument("--file", "-f", default="CODELAN_README.md", help="Path to language documentation or rules file")
    train_p.add_argument("--episodes", "-e", type=int, default=25, help="Number of trial-and-error episodes")

    # Generate
    gen_p = subparsers.add_parser("generate", help="Synthesize a CodeLan game from natural language prompt")
    gen_p.add_argument("prompt", help="Game description prompt")
    gen_p.add_argument("--output", "-o", help="Output .clan file path")
    gen_p.add_argument("--play", "-p", action="store_true", help="Launch and play immediately after generating")

    # Stats
    subparsers.add_parser("stats", help="Inspect learned Q-values and training metrics")

    # Reward / Punish
    rew_p = subparsers.add_parser("feedback", help="Provide human reinforcement reward or punishment")
    rew_p.add_argument("--genre", "-g", required=True, help="Genre name (e.g. space_shooter, pong, snake)")
    rew_p.add_argument("--points", "-p", type=float, required=True, help="Points (+10 for reward, -10 for punishment)")
    rew_p.add_argument("--note", "-n", default="", help="Optional feedback note")

    args = parser.parse_args()

    if args.command == "train":
        cmd_train(args)
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "feedback":
        cmd_reward(args)
    else:
        # Default action: launch web studio
        run_web_app()


if __name__ == "__main__":
    main()
