# 🎮 CodeLan AI Studio & Reinforcement Learning Game Maker

An autonomous AI engine specialized in the **CodeLan** programming language (`.clan`). It recognizes game concepts described in natural language, synthesizes complete, runnable games, verifies them against the CodeLan compiler, and continuously learns using **Reinforcement Learning (Trial and Error)**.

---

## 🌟 Key Features

- 🧠 **Reinforcement Learning (Trial & Error Engine)**:
  - Learns from any language specification file (such as `CODELAN_README.md`, syntax docs, or rule files).
  - Rewards (+) valid syntax, lifecycle compliance (`setup`, `update`, `draw`), proper function signatures, and game mechanics.
  - Punishes (-) compiler syntax errors, missing game loops, and foreign hallucinations (like Python `def`, JS `function`, `var`, `console.log`).
- 🎮 **Generates a Wide Variety of Games**:
  - **Space Defender / Arcade Shooters**: Scrolling starfields, lasers, alien fleets, particle bursts, and sounds.
  - **Pong / Table Tennis**: Bouncing ball volleys, paddle physics, AI opponents, and scoring.
  - **Cyber Snake**: Grid navigation, apple pickups, body growth, and wall collision.
  - **Flappy Bird**: Gravity physics, flap impulses, moving pipe obstacles, and high scores.
  - **Breakout / Brick Breaker**: Multi-colored destructible brick grids, ball reflections, and combo sound triggers.
  - **Asteroid Dodger**: 8-way dodging, falling hazards, and collectible energy gems.
  - **Platformer / Jumper**: Moving bounce pads and vertical camera climbing.
  - **Target Clicker / Reflex**: Fast disappearing targets clicked with the mouse.
  - **Custom Game Prompts**: Type any custom game idea in natural language.
- 🕹️ **Instant Playable Browser Preview**:
  - Automatically transpiles generated games to standalone HTML5 canvas games with retro 8-bit Web Audio.
- 🖥️ **Native 60 FPS Desktop Runner**:
  - Launch native 60 FPS desktop games with one click.
- 🐶 **Human-in-the-Loop RL (RLHF)**:
  - Reward (+10, +5) or punish (-10, -5) the AI directly from the web interface or CLI.

---

## 🚀 Quick Start

### Option 1: Double-Click Launcher (Windows)
Double-click **`launch.bat`** to start the web application and automatically open your default browser at `http://localhost:5050`.

### Option 2: Run via Terminal
```bash
python app.py
```
Then visit **`http://localhost:5050`** in your browser.

### Option 3: Run Standalone Executable
```bash
dist\codelan_ai\codelan_ai.exe
```

---

## 🧠 Reinforcement Learning (Trial and Error)

### How It Works
The engine uses **Method 3: Reinforcement Learning (Trial and Error)**:
> *This method teaches an AI through a system of rewards and punishments, similar to training a dog or playing a video game.*

1. **Ingest Language File**:
   - Provide a file containing documentation or rules (e.g. `CODELAN_README.md`).
   - The AI extracts all valid built-in functions, lifecycle requirements, audio effect names, and forbidden tokens.
2. **Trial-and-Error Episodes**:
   - The AI proposes code solutions for varied game challenges.
   - The **CodeLan Evaluator Environment** runs the code through the official `Lexer` and `Parser`.
3. **Reward & Punishment Breakdown**:
   - **Syntax Passed**: `+25.0` points.
   - **Syntax Error (Compiler Failed)**: `-30.0` points.
   - **Lifecycle Hooks (`setup`, `update`, `draw`)**: `+10.0` points each.
   - **Valid Built-in Usage**: `+3.0` points per valid built-in function from the language file.
   - **Audio Effects**: `+5.0` points for valid 8-bit sounds (`laser`, `jump`, `hit`, `coin`, `explosion`, etc.).
   - **Hallucinations**: `-20.0` points for using forbidden keywords (`def`, `function`, `var`, `class`, `import`).
4. **Policy & Q-Value Updates**:
   - Updates Q-values and feature weights using:
     $$Q(s, a) \leftarrow Q(s, a) + \alpha \big( R - Q(s, a) \big)$$
   - High-reward patterns are strengthened; penalized errors are avoided in future generations.

---

## 💻 CLI Usage

The `codelan_ai_cli.py` tool lets you train and generate directly from your command line:

### 1. Train on Language Documentation
```bash
python codelan_ai_cli.py train --file CODELAN_README.md --episodes 25
```

### 2. Synthesize a Game from Natural Language
```bash
python codelan_ai_cli.py generate "Neon space shooter with laser sounds" --output myshooter.clan
```

### 3. Generate and Immediately Play in Desktop Window
```bash
python codelan_ai_cli.py generate "Breakout with 5 rows of bricks" --play
```

### 4. Provide Human Reinforcement (Reward or Punish)
```bash
# Reward the AI for great space games
python codelan_ai_cli.py feedback --genre space_shooter --points 10 --note "Awesome lasers"

# Punish the AI for a mistake
python codelan_ai_cli.py feedback --genre pong --points -10 --note "Ball got stuck in paddle"
```

### 5. Inspect Model Stats & Q-Values
```bash
python codelan_ai_cli.py stats
```

---

## 📁 Project Structure

```
codelanai/
├── app.py                 # Interactive Web Studio (HTTP Server & UI)
├── launch.bat             # 1-Click Windows Launcher
├── codelan_ai_cli.py      # CLI tool (train, generate, stats, feedback)
├── main.py                # Unified entry point for executable
├── knowledge_base.py      # Extracts language rules & builtins from files
├── rl_engine.py           # Reinforcement Learning evaluator, Q-table & agent
├── game_generator.py      # Multi-genre CodeLan game synthesizer
├── automated_trainer.py   # Automated trial-and-error training loop
├── codelan_rl_model.json  # Saved Q-values, weights, and reward history
├── CODELAN_README.md      # Language documentation reference
├── codelan/               # Core CodeLan compiler (lexer, parser, interpreter, runtime)
└── examples/              # Sample CodeLan games (.clan)
```

---

## 📄 License
MIT License.
