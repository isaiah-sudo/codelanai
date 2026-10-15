"""
CodeLan AI Studio & Reinforcement Learning (Trial-and-Error) Web Application.
Provides interactive game generation, compiler syntax verification, live browser play,
desktop game launching, and file-based RL trial-and-error training with human feedback.
"""

import sys
import os
import re
import json
import time
import uuid
import socket
import webbrowser
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Ensure UTF-8 stdout encoding on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Local AI & RL components
from knowledge_base import knowledge_base
from rl_engine import rl_agent, CodeLanEvaluator
from game_generator import game_generator
from automated_trainer import trainer

# CodeLan runtime and web exporter
from codelan.lexer import Lexer, LexerError
from codelan.parser import Parser, ParserError
from codelan.web_exporter import export_to_html

# Global state for temporary generated games
GAMES_CACHE = {}
DEFAULT_GAME_ID = "current_game"


def transpile_codelan_to_html(code: str, title: str = "CodeLan Game") -> str:
    """Parses CodeLan code and returns self-contained HTML5 canvas game string."""
    try:
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens, filename="game.clan")
        program = parser.parse()
        return export_to_html(program, title=title)
    except Exception as e:
        # Fallback error page
        return f"""<!DOCTYPE html>
<html>
<head><title>Syntax Error</title><style>body{{background:#0f172a;color:#f43f5e;font-family:monospace;padding:30px;}}</style></head>
<body><h2>❌ CodeLan Syntax Error</h2><pre>{e}</pre></body>
</html>"""


# =====================================================================
# HTTP REQUEST HANDLER
# =====================================================================
class CodeLanAIHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _send_html(self, html_str, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(html_str.encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. Main Application Dashboard
        if path == "/" or path == "/index.html":
            self._send_html(self.get_main_ui_html())
            return

        # 2. Play game endpoint (renders iframe canvas)
        if path.startswith("/play/"):
            game_id = path.replace("/play/", "").strip()
            if game_id in GAMES_CACHE:
                self._send_html(GAMES_CACHE[game_id]["html"])
            else:
                self._send_html("<h3>Game not found or expired. Generate a game first!</h3>", 404)
            return

        # 3. API: Stats & Model Status
        if path == "/api/stats":
            stats = rl_agent.get_stats()
            self._send_json({"success": True, "stats": stats})
            return

        # 3b. API: Real-Time Learning Curve
        if path == "/api/curve":
            curve = rl_agent.get_learning_curve()
            self._send_json({"success": True, "curve": curve})
            return

        # 4. API: Knowledge Base Summary
        if path == "/api/knowledge":
            summary = knowledge_base.get_summary()
            self._send_json({"success": True, "knowledge": summary})
            return

        # 5. API: Pre-built Demo Games
        if path == "/api/demos":
            examples_dir = Path(__file__).resolve().parent / "examples"
            demos = []
            if examples_dir.exists():
                for p in examples_dir.glob("*.clan"):
                    demos.append({
                        "name": p.stem.replace("_", " ").title(),
                        "filename": p.name,
                        "code": p.read_text(encoding="utf-8", errors="replace")
                    })
            self._send_json({"success": True, "demos": demos})
            return

        self.send_error(404, "Page Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8", errors="replace") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        # 1. API: Generate Game from Prompt
        if path == "/api/generate":
            prompt = payload.get("prompt", "Create an arcade game").strip()
            code, intent = game_generator.generate_game(prompt)

            # Evaluate against compiler and language file rules
            evaluator = CodeLanEvaluator(knowledge_base)
            report = evaluator.evaluate(code, intent_spec={"genre": intent.genre, "require_sound": intent.require_sound})

            # Record automated RL learning step
            decisions = {
                "syntax_action": "valid_codelan_let" if report.is_valid_syntax else "syntax_flaw",
                "features": getattr(intent, "decisions", {})
            }
            rl_agent.update_from_trial(intent.genre, decisions, report)

            # Transpile to HTML for live playable canvas
            html_content = transpile_codelan_to_html(code, title=intent.title)
            game_id = str(uuid.uuid4())[:8]
            GAMES_CACHE[game_id] = {"code": code, "html": html_content, "title": intent.title}
            GAMES_CACHE[DEFAULT_GAME_ID] = GAMES_CACHE[game_id]

            self._send_json({
                "success": True,
                "game_id": game_id,
                "code": code,
                "intent": {
                    "genre": intent.genre,
                    "title": intent.title,
                    "require_sound": intent.require_sound
                },
                "report": report.to_dict(),
                "play_url": f"/play/{game_id}"
            })
            return

        # 2. API: Syntax Validation Check
        if path == "/api/check_syntax":
            code = payload.get("code", "")
            evaluator = CodeLanEvaluator(knowledge_base)
            report = evaluator.evaluate(code)
            self._send_json({
                "success": True,
                "report": report.to_dict()
            })
            return

        # 3. API: Transpile / Preview Code
        if path == "/api/transpile":
            code = payload.get("code", "")
            title = payload.get("title", "CodeLan Game")
            html_content = transpile_codelan_to_html(code, title=title)
            game_id = str(uuid.uuid4())[:8]
            GAMES_CACHE[game_id] = {"code": code, "html": html_content, "title": title}
            GAMES_CACHE[DEFAULT_GAME_ID] = GAMES_CACHE[game_id]
            self._send_json({
                "success": True,
                "game_id": game_id,
                "play_url": f"/play/{game_id}"
            })
            return

        # 4. API: Run Native 60 FPS Desktop Game
        if path == "/api/run_desktop":
            code = payload.get("code", "")
            temp_file = Path(__file__).resolve().parent / "temp_game.clan"
            temp_file.write_text(code, encoding="utf-8")

            # Launch python codelan runner as separate process
            def launch_runner():
                runner_script = Path(__file__).resolve().parent / "codelan" / "cli.py"
                try:
                    subprocess.run([sys.executable, "-m", "codelan.cli", "run", str(temp_file)])
                except Exception as ex:
                    print(f"Error launching desktop runner: {ex}")

            threading.Thread(target=launch_runner, daemon=True).start()
            self._send_json({"success": True, "message": "Launching native desktop window at 60 FPS..."})
            return

        # 5. API: Human Reinforcement Learning Feedback (Reward / Punish)
        if path == "/api/reward":
            genre = payload.get("genre", "custom")
            reward_points = float(payload.get("points", 10.0))
            note = payload.get("note", "")

            rl_agent.record_human_feedback(genre, reward_points, note)
            self._send_json({
                "success": True,
                "message": f"{'🏆 Rewarded' if reward_points > 0 else '⚡ Punished'} AI with {reward_points:+.1f} points!",
                "stats": rl_agent.get_stats()
            })
            return

        # 6. API: Train on Language File (Trial and Error Learning Loop)
        if path == "/api/train_file":
            filepath = payload.get("filepath", "CODELAN_README.md").strip()
            episodes = int(payload.get("episodes", 25))

            # Resolve filepath
            if not os.path.exists(filepath):
                local_path = os.path.join(os.path.dirname(__file__), filepath)
                if os.path.exists(local_path):
                    filepath = local_path

            result = trainer.train_on_file(filepath=filepath, episodes=episodes)
            result["stats"] = rl_agent.get_stats()
            self._send_json(result)
            return

        self.send_error(404, "API Endpoint Not Found")

    def get_main_ui_html(self) -> str:
        """Returns the full HTML, CSS, and JS single-page web app."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🎮 CodeLan AI Studio | Reinforcement Learning Game Engine</title>
  <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Orbitron:wght@600;800;900&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #090d16;
      --bg-card: #131a2a;
      --bg-card-hover: #1c263d;
      --border-color: #243048;
      --neon-cyan: #00f0ff;
      --neon-pink: #ff007f;
      --neon-purple: #a855f7;
      --neon-green: #22c55e;
      --neon-yellow: #eab308;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg-dark);
      color: var(--text-main);
      font-family: 'Inter', sans-serif;
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* Glow Header */
    header {
      background: rgba(19, 26, 42, 0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border-color);
      padding: 14px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand h1 {
      font-family: 'Orbitron', sans-serif;
      font-size: 1.45rem;
      font-weight: 800;
      background: linear-gradient(135deg, var(--neon-cyan), var(--neon-purple), var(--neon-pink));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: 0.5px;
    }
    .brand .badge {
      font-size: 0.72rem;
      background: rgba(0, 240, 255, 0.12);
      color: var(--neon-cyan);
      border: 1px solid rgba(0, 240, 255, 0.3);
      padding: 3px 8px;
      border-radius: 12px;
      font-weight: 600;
    }

    /* Top Stats Pills */
    .header-stats {
      display: flex;
      gap: 16px;
      align-items: center;
    }
    .stat-pill {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      padding: 6px 14px;
      border-radius: 8px;
      font-size: 0.82rem;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .stat-pill .val {
      font-weight: 700;
      color: var(--neon-cyan);
      font-family: 'Fira Code', monospace;
    }
    .stat-pill .lbl {
      font-size: 0.68rem;
      color: var(--text-muted);
    }

    /* Navigation Tabs */
    .tabs {
      display: flex;
      gap: 8px;
      padding: 14px 28px 0;
      border-bottom: 1px solid var(--border-color);
      background: #0d121f;
    }
    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 10px 20px;
      font-size: 0.95rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      border-bottom: 2px solid transparent;
      transition: all 0.2s ease;
    }
    .tab-btn:hover { color: var(--text-main); }
    .tab-btn.active {
      color: var(--neon-cyan);
      border-bottom: 2px solid var(--neon-cyan);
    }

    /* Tab Contents */
    .tab-content {
      display: none;
      padding: 24px 28px;
    }
    .tab-content.active { display: block; }

    /* Generator Grid */
    .generator-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      height: calc(100vh - 170px);
    }

    .panel {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    }
    .panel-header {
      padding: 12px 18px;
      background: rgba(15, 23, 42, 0.7);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .panel-header h2 {
      font-size: 1.05rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .panel-body {
      padding: 18px;
      flex: 1;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    /* Prompt Box */
    .prompt-box {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .prompt-input-row {
      display: flex;
      gap: 10px;
    }
    .prompt-input {
      flex: 1;
      background: #090d16;
      border: 1px solid var(--border-color);
      color: var(--text-main);
      padding: 12px 16px;
      border-radius: 8px;
      font-size: 0.95rem;
      outline: none;
      transition: border 0.2s;
    }
    .prompt-input:focus { border-color: var(--neon-cyan); }
    .btn-generate {
      background: linear-gradient(135deg, var(--neon-cyan), #0284c7);
      color: #000;
      border: none;
      padding: 0 24px;
      border-radius: 8px;
      font-weight: 700;
      font-size: 0.95rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: transform 0.15s, box-shadow 0.2s;
    }
    .btn-generate:hover {
      transform: translateY(-1px);
      box-shadow: 0 0 15px rgba(0, 240, 255, 0.4);
    }

    /* Quick Preset Chips */
    .preset-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .chip {
      background: rgba(30, 41, 59, 0.7);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: var(--text-muted);
      padding: 5px 11px;
      border-radius: 16px;
      font-size: 0.78rem;
      cursor: pointer;
      transition: all 0.15s;
    }
    .chip:hover {
      background: var(--bg-card-hover);
      color: var(--neon-cyan);
      border-color: rgba(0, 240, 255, 0.3);
    }

    /* Code Editor Area */
    .editor-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      background: #060911;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      overflow: hidden;
      min-height: 260px;
    }
    .editor-toolbar {
      background: #0c111d;
      padding: 8px 12px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.8rem;
      color: var(--text-muted);
    }
    .code-area {
      flex: 1;
      width: 100%;
      background: transparent;
      color: #38bdf8;
      border: none;
      padding: 12px;
      font-family: 'Fira Code', monospace;
      font-size: 0.86rem;
      line-height: 1.5;
      resize: none;
      outline: none;
      white-space: pre;
    }

    /* Game Preview Area */
    .preview-canvas-box {
      flex: 1;
      background: #000;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      overflow: hidden;
      position: relative;
      min-height: 380px;
      display: flex;
      flex-direction: column;
    }
    .preview-canvas-box iframe {
      width: 100%;
      height: 100%;
      border: none;
      flex: 1;
    }

    /* RL Human Feedback Panel */
    .rl-feedback-box {
      background: rgba(15, 23, 42, 0.9);
      border: 1px solid var(--border-color);
      border-radius: 10px;
      padding: 14px 18px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .feedback-title {
      font-size: 0.88rem;
      font-weight: 700;
      color: var(--neon-yellow);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .feedback-buttons {
      display: flex;
      gap: 8px;
    }
    .btn-reward {
      flex: 1;
      background: rgba(34, 197, 94, 0.15);
      border: 1px solid var(--neon-green);
      color: var(--neon-green);
      padding: 8px 12px;
      border-radius: 6px;
      font-weight: 700;
      font-size: 0.82rem;
      cursor: pointer;
      transition: all 0.15s;
    }
    .btn-reward:hover {
      background: var(--neon-green);
      color: #000;
      box-shadow: 0 0 12px rgba(34, 197, 94, 0.4);
    }
    .btn-punish {
      flex: 1;
      background: rgba(244, 63, 94, 0.15);
      border: 1px solid var(--neon-pink);
      color: var(--neon-pink);
      padding: 8px 12px;
      border-radius: 6px;
      font-weight: 700;
      font-size: 0.82rem;
      cursor: pointer;
      transition: all 0.15s;
    }
    .btn-punish:hover {
      background: var(--neon-pink);
      color: #fff;
      box-shadow: 0 0 12px rgba(244, 63, 94, 0.4);
    }

    /* Evaluation Diagnostics Card */
    .eval-card {
      background: #0c121e;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 12px 14px;
      font-size: 0.8rem;
    }
    .eval-card .eval-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 6px;
      font-weight: 700;
    }
    .tag-passed { color: var(--neon-green); }
    .tag-failed { color: var(--neon-pink); }

    /* Training View */
    .training-view {
      max-width: 1000px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .train-hero {
      background: linear-gradient(135deg, rgba(168, 85, 247, 0.15), rgba(0, 240, 255, 0.15));
      border: 1px solid rgba(168, 85, 247, 0.3);
      padding: 24px;
      border-radius: 12px;
    }
    .train-hero h2 {
      font-family: 'Orbitron', sans-serif;
      font-size: 1.3rem;
      color: #fff;
      margin-bottom: 8px;
    }
    .train-hero p {
      color: var(--text-muted);
      font-size: 0.92rem;
      line-height: 1.6;
    }

    .train-controls {
      display: grid;
      grid-template-columns: 2fr 1fr 1fr;
      gap: 12px;
      align-items: center;
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      padding: 18px;
      border-radius: 10px;
    }
    .train-input-group label {
      display: block;
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-bottom: 6px;
    }
    .train-input {
      width: 100%;
      background: #090d16;
      border: 1px solid var(--border-color);
      color: #fff;
      padding: 10px 14px;
      border-radius: 6px;
      font-size: 0.9rem;
    }
    .btn-train {
      background: linear-gradient(135deg, var(--neon-purple), var(--neon-pink));
      color: #fff;
      border: none;
      padding: 12px 18px;
      border-radius: 8px;
      font-weight: 700;
      cursor: pointer;
      font-size: 0.95rem;
      height: 44px;
      margin-top: 18px;
      transition: all 0.2s;
    }
    .btn-train:hover {
      box-shadow: 0 0 18px rgba(168, 85, 247, 0.5);
    }

    /* Training Console */
    .train-console {
      background: #060911;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 16px;
      font-family: 'Fira Code', monospace;
      font-size: 0.84rem;
      height: 280px;
      overflow-y: auto;
      color: #38bdf8;
    }
    .log-line { margin-bottom: 4px; }
    .log-reward { color: var(--neon-green); font-weight: 600; }
    .log-punish { color: var(--neon-pink); font-weight: 600; }

    /* Action buttons */
    .btn-action {
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: var(--text-main);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }
    .btn-action:hover {
      background: var(--bg-card-hover);
      border-color: var(--neon-cyan);
      color: var(--neon-cyan);
    }
  </style>
</head>
<body>

  <!-- Header -->
  <header>
    <div class="brand">
      <span style="font-size: 1.8rem;">🎮</span>
      <div>
        <h1>CODELAN AI STUDIO</h1>
      </div>
      <span class="badge">Reinforcement Learning v2.4</span>
    </div>

    <div class="header-stats">
      <div class="stat-pill">
        <span class="val" id="stat-episodes">--</span>
        <span class="lbl">TOTAL EPISODES</span>
      </div>
      <div class="stat-pill">
        <span class="val" id="stat-reward" style="color: var(--neon-green);">--</span>
        <span class="lbl">LIFETIME REWARD</span>
      </div>
      <div class="stat-pill">
        <span class="val" id="stat-accuracy" style="color: var(--neon-purple);">--</span>
        <span class="lbl">SYNTAX ACCURACY</span>
      </div>
      <div class="stat-pill">
        <span class="val" id="stat-qstates">--</span>
        <span class="lbl">Q-TABLE STATES</span>
      </div>
    </div>
  </header>

  <!-- Navigation Tabs -->
  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('creator')">🕹️ AI Game Creator</button>
    <button class="tab-btn" onclick="switchTab('training')">🧠 Reinforcement Learning Studio</button>
    <button class="tab-btn" onclick="switchTab('knowledge')">📚 Language Knowledge & Rules</button>
  </div>

  <!-- ======================================================== -->
  <!-- TAB 1: AI GAME CREATOR -->
  <!-- ======================================================== -->
  <div id="tab-creator" class="tab-content active">
    <div class="generator-grid">

      <!-- Left Panel: Prompt & Code Editor -->
      <div class="panel">
        <div class="panel-header">
          <h2>💬 Tell AI What Game To Build</h2>
          <span id="syntax-badge" class="badge" style="background: rgba(34,197,94,0.15); color: var(--neon-green); border: 1px solid var(--neon-green);">
            ✓ Valid CodeLan
          </span>
        </div>
        <div class="panel-body">

          <!-- Prompt Box -->
          <div class="prompt-box">
            <div class="prompt-input-row">
              <input type="text" id="prompt-input" class="prompt-input" placeholder="e.g. Space shooter with laser sounds and meteor explosions" value="Space shooter with laser sounds and meteor explosions">
              <button class="btn-generate" onclick="generateGame()">
                <span>⚡ Generate</span>
              </button>
            </div>

            <!-- Quick Presets -->
            <div class="preset-chips">
              <span class="chip" onclick="setPrompt('Retro neon space shooter with laser sounds and exploding alien ships')">🚀 Space Shooter</span>
              <span class="chip" onclick="setPrompt('2-Player neon ping pong with bouncy ball and score sounds')">🏓 Neon Pong</span>
              <span class="chip" onclick="setPrompt('Cyber snake game with glowing food and speed increase')">🐍 Cyber Snake</span>
              <span class="chip" onclick="setPrompt('Flappy bird with green pipe obstacles and flapping sound')">🐦 Flappy Bird</span>
              <span class="chip" onclick="setPrompt('Breakout brick breaker with 5 rainbow brick rows and paddle bounce')">🧱 Breakout</span>
              <span class="chip" onclick="setPrompt('Dodge falling meteor hazards and collect energy gems')">☄️ Asteroid Dodge</span>
              <span class="chip" onclick="setPrompt('Bouncing platformer climbing into the sky')">🦘 Platformer</span>
              <span class="chip" onclick="setPrompt('Fast target clicker reflex test with timer')">🎯 Aim Clicker</span>
            </div>
          </div>

          <!-- Code Editor -->
          <div class="editor-container">
            <div class="editor-toolbar">
              <span>CodeLan (.clan) Source</span>
              <div style="display: flex; gap: 8px;">
                <button class="btn-action" onclick="checkSyntax()">🔍 Check Syntax</button>
                <button class="btn-action" onclick="updatePreview()">🔄 Update Play Canvas</button>
                <button class="btn-action" onclick="runDesktop()">🖥️ 60 FPS Desktop</button>
                <button class="btn-action" onclick="downloadCode()">💾 Download .clan</button>
              </div>
            </div>
            <textarea id="code-editor" class="code-area" spellcheck="false"></textarea>
          </div>

          <!-- Evaluation Diagnostics Box -->
          <div id="eval-box" class="eval-card">
            <div class="eval-header">
              <span>Compiler Evaluation & RL Reward</span>
              <span id="eval-reward-score" style="color: var(--neon-cyan);">+0.0 Points</span>
            </div>
            <div id="eval-details" style="color: var(--text-muted); line-height: 1.4;">
              Ready. Generate a game or test syntax to see the reward/penalty breakdown.
            </div>
          </div>

        </div>
      </div>

      <!-- Right Panel: Playable Canvas & Human RL Feedback -->
      <div class="panel">
        <div class="panel-header">
          <h2>▶ Live Playable Game Canvas (HTML5 + 8-Bit Audio)</h2>
          <button class="btn-action" onclick="reloadPreview()">🔄 Restart Game</button>
        </div>
        <div class="panel-body">

          <!-- Playable IFrame -->
          <div class="preview-canvas-box">
            <iframe id="game-frame" src="about:blank"></iframe>
          </div>

          <!-- Human Feedback (Reward / Punish) -->
          <div class="rl-feedback-box">
            <div class="feedback-title">
              <span>🐶 Reinforcement Learning Feedback (Teach the AI)</span>
              <span style="font-size: 0.76rem; color: var(--text-muted);">Reward right behavior or punish mistakes</span>
            </div>
            <div class="feedback-buttons">
              <button class="btn-reward" onclick="sendReward(10, 'Great game mechanics and syntax!')">🏆 Reward +10 (Great!)</button>
              <button class="btn-reward" onclick="sendReward(5, 'Good code')">⭐ Reward +5</button>
              <button class="btn-punish" onclick="sendReward(-5, 'Minor flaw')">⚠️ Punish -5</button>
              <button class="btn-punish" onclick="sendReward(-10, 'Broken or missing features!')">❌ Punish -10 (Bad!)</button>
            </div>
            <div id="feedback-status" style="font-size: 0.78rem; color: var(--text-muted); min-height: 16px;"></div>
          </div>

        </div>
      </div>

    </div>
  </div>

  <!-- ======================================================== -->
  <!-- TAB 2: REINFORCEMENT LEARNING STUDIO -->
  <!-- ======================================================== -->
  <div id="tab-training" class="tab-content">
    <div class="training-view">

      <div class="train-hero">
        <h2>3. Reinforcement Learning (Trial and Error) Studio</h2>
        <p>
          This method teaches an AI through a system of rewards and punishments, similar to training a dog or playing a video game.
          Give it a file about the language (e.g. <code>CODELAN_README.md</code>, tutorials, or syntax rules), and as it trials different game programs,
          if it sees stuff right it is <strong>rewarded</strong> (+), and if it sees stuff wrong it is <strong>punished</strong> (-).
        </p>
      </div>

      <!-- Training File & Episode Inputs -->
      <div class="train-controls">
        <div class="train-input-group">
          <label>Language File Path (Documentation, Rules, or Grammar)</label>
          <input type="text" id="train-filepath" class="train-input" value="CODELAN_README.md">
        </div>
        <div class="train-input-group">
          <label>Trial-and-Error Episodes</label>
          <input type="number" id="train-episodes" class="train-input" value="25" min="5" max="200">
        </div>
        <button class="btn-train" onclick="startFileTraining()">
          🚀 Run RL Training
        </button>
      </div>

      <!-- Training Progress Bar -->
      <div style="background: var(--bg-card); border: 1px solid var(--border-color); padding: 14px; border-radius: 8px;">
        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 8px;">
          <span id="train-status-label">Ready to train</span>
          <span id="train-percent" style="font-weight: 700; color: var(--neon-cyan);">0%</span>
        </div>
        <div style="background: #090d16; border-radius: 6px; height: 12px; overflow: hidden; border: 1px solid var(--border-color);">
          <div id="train-progress-bar" style="background: linear-gradient(90deg, var(--neon-cyan), var(--neon-purple)); width: 0%; height: 100%; transition: width 0.2s;"></div>
        </div>
      </div>

      <!-- Live Trial Console -->
      <div class="train-console" id="train-console">
        <div class="log-line">// Reinforcement Learning Trial-and-Error Console Ready...</div>
        <div class="log-line">// Ingesting language file will calibrate AST compiler rewards and feature weights.</div>
      </div>

    </div>
  </div>

  <!-- ======================================================== -->
  <!-- TAB 3: LANGUAGE KNOWLEDGE & RULES -->
  <!-- ======================================================== -->
  <div id="tab-knowledge" class="tab-content">
    <div class="training-view">
      <div class="panel">
        <div class="panel-header">
          <h2>📚 CodeLan Knowledge Extracted from Language File</h2>
        </div>
        <div class="panel-body">
          <div id="knowledge-summary" style="font-size: 0.9rem; line-height: 1.6; color: var(--text-muted);">
            Loading language knowledge base...
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- JavaScript Frontend Logic -->
  <script>
    let currentGenre = "custom";
    let currentGameId = "";

    function switchTab(name) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      event.target.classList.add('active');
      document.getElementById('tab-' + name).classList.add('active');
      if (name === 'knowledge') loadKnowledge();
    }

    function setPrompt(text) {
      document.getElementById('prompt-input').value = text;
      generateGame();
    }

    async function loadStats() {
      try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        if (data.success) {
          const s = data.stats;
          document.getElementById('stat-episodes').innerText = s.total_episodes;
          document.getElementById('stat-reward').innerText = s.total_reward_lifetime.toFixed(1);
          document.getElementById('stat-accuracy').innerText = s.accuracy_percent + '%';
          document.getElementById('stat-qstates').innerText = s.total_q_states;
        }
      } catch (err) {
        console.error("Error loading stats:", err);
      }
    }

    async function generateGame() {
      const prompt = document.getElementById('prompt-input').value.trim();
      if (!prompt) return;

      document.getElementById('syntax-badge').innerHTML = '⏳ Synthesizing...';
      document.getElementById('eval-reward-score').innerText = '...';

      try {
        const res = await fetch('/api/generate', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({prompt: prompt})
        });
        const data = await res.json();
        if (data.success) {
          document.getElementById('code-editor').value = data.code;
          currentGenre = data.intent.genre;
          currentGameId = data.game_id;
          document.getElementById('game-frame').src = data.play_url;

          // Diagnostics
          renderEvalReport(data.report);
          loadStats();
        }
      } catch (err) {
        alert("Error generating game: " + err);
      }
    }

    function renderEvalReport(rep) {
      const badge = document.getElementById('syntax-badge');
      if (rep.is_valid_syntax) {
        badge.innerHTML = '✓ Valid CodeLan (AST Clean)';
        badge.style.color = 'var(--neon-green)';
        badge.style.borderColor = 'var(--neon-green)';
        badge.style.background = 'rgba(34,197,94,0.15)';
      } else {
        badge.innerHTML = '✕ Syntax Issue Detected';
        badge.style.color = 'var(--neon-pink)';
        badge.style.borderColor = 'var(--neon-pink)';
        badge.style.background = 'rgba(244,63,94,0.15)';
      }

      document.getElementById('eval-reward-score').innerText = (rep.total_reward >= 0 ? '+' : '') + rep.total_reward + ' Points';

      let html = '<div style="margin-bottom: 4px;"><strong>Verified Built-ins:</strong> ' + (rep.matched_builtins.join(', ') || 'None') + '</div>';
      html += '<div style="margin-bottom: 4px;"><strong>Lifecycle Hooks:</strong> ' + rep.matched_lifecycle.join(', ') + '</div>';
      if (rep.rewards && rep.rewards.length) {
        html += '<div style="color: var(--neon-green); margin-top: 4px;"><strong>Rewards:</strong> ' + rep.rewards.map(r => r.reason + ' (+' + r.points + ')').join(' | ') + '</div>';
      }
      if (rep.punishments && rep.punishments.length) {
        html += '<div style="color: var(--neon-pink); margin-top: 4px;"><strong>Punishments:</strong> ' + rep.punishments.map(p => p.reason + ' (' + p.points + ')').join(' | ') + '</div>';
      }
      document.getElementById('eval-details').innerHTML = html;
    }

    async function checkSyntax() {
      const code = document.getElementById('code-editor').value;
      const res = await fetch('/api/check_syntax', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({code: code})
      });
      const data = await res.json();
      if (data.success) {
        renderEvalReport(data.report);
      }
    }

    async function updatePreview() {
      const code = document.getElementById('code-editor').value;
      const res = await fetch('/api/transpile', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({code: code, title: 'CodeLan Play'})
      });
      const data = await res.json();
      if (data.success) {
        document.getElementById('game-frame').src = data.play_url + '?t=' + Date.now();
      }
    }

    function reloadPreview() {
      const frame = document.getElementById('game-frame');
      frame.src = frame.src;
    }

    async function runDesktop() {
      const code = document.getElementById('code-editor').value;
      const res = await fetch('/api/run_desktop', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({code: code})
      });
      const data = await res.json();
      alert(data.message || "Launched desktop window!");
    }

    async function sendReward(points, note) {
      const res = await fetch('/api/reward', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({genre: currentGenre, points: points, note: note})
      });
      const data = await res.json();
      if (data.success) {
        const status = document.getElementById('feedback-status');
        status.innerText = data.message + ' Policy weights updated.';
        status.style.color = points > 0 ? 'var(--neon-green)' : 'var(--neon-pink)';
        loadStats();
      }
    }

    function downloadCode() {
      const code = document.getElementById('code-editor').value;
      const blob = new Blob([code], {type: 'text/plain'});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = (currentGenre || 'game') + '.clan';
      a.click();
    }

    // RL Training Loop
    async function startFileTraining() {
      const filepath = document.getElementById('train-filepath').value.trim();
      const episodes = parseInt(document.getElementById('train-episodes').value) || 25;
      const consoleBox = document.getElementById('train-console');

      consoleBox.innerHTML += '<div class="log-line">// Starting Reinforcement Learning Trial-and-Error on: ' + filepath + ' (' + episodes + ' episodes)</div>';
      document.getElementById('train-status-label').innerText = 'Training in progress...';
      document.getElementById('train-progress-bar').style.width = '20%';

      try {
        const res = await fetch('/api/train_file', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({filepath: filepath, episodes: episodes})
        });
        const data = await res.json();

        if (data.success) {
          document.getElementById('train-progress-bar').style.width = '100%';
          document.getElementById('train-percent').innerText = '100%';
          document.getElementById('train-status-label').innerText = 'Training Complete!';

          consoleBox.innerHTML += '<div class="log-line log-reward">✓ Finished ' + data.episodes_trained + ' trials from ' + data.file + '</div>';
          consoleBox.innerHTML += '<div class="log-line">Total Session Reward: ' + data.total_reward_session + ' | Accuracy: ' + data.accuracy_percent + '%</div>';

          if (data.session_history) {
            data.session_history.forEach(h => {
              const cls = h.reward >= 0 ? 'log-reward' : 'log-punish';
              consoleBox.innerHTML += '<div class="log-line ' + cls + '">Ep ' + h.episode + ' [' + h.genre + '] ' + (h.reward >= 0 ? '+' : '') + h.reward.toFixed(1) + ' pts (Builtins: ' + h.matched_builtins.length + ')</div>';
            });
          }
          consoleBox.scrollTop = consoleBox.scrollHeight;
          loadStats();
        } else {
          consoleBox.innerHTML += '<div class="log-line log-punish">❌ Training failed: ' + data.error + '</div>';
        }
      } catch (err) {
        consoleBox.innerHTML += '<div class="log-line log-punish">❌ Network error: ' + err + '</div>';
      }
    }

    async function loadKnowledge() {
      const res = await fetch('/api/knowledge');
      const data = await res.json();
      if (data.success) {
        const k = data.knowledge;
        let html = '<div style="margin-bottom: 12px;"><strong>Source File:</strong> ' + k.source_file + ' (' + k.file_size + ' bytes)</div>';
        html += '<div style="margin-bottom: 12px;"><strong>Discovered Built-in Functions (' + k.total_builtins + '):</strong><br><div style="font-family: monospace; color: var(--neon-cyan); margin-top: 4px;">' + k.builtins.join(', ') + '</div></div>';
        html += '<div style="margin-bottom: 12px;"><strong>Standard Lifecycle Blocks:</strong><br><div style="font-family: monospace; color: var(--neon-green); margin-top: 4px;">' + k.lifecycle_hooks.join(', ') + '</div></div>';
        html += '<div style="margin-bottom: 12px;"><strong>Procedural 8-bit Audio Names:</strong><br><div style="font-family: monospace; color: var(--neon-yellow); margin-top: 4px;">' + k.audio_effects.join(', ') + '</div></div>';
        html += '<div style="margin-bottom: 12px;"><strong>Forbidden / Penalized Hallucinations:</strong><br><div style="font-family: monospace; color: var(--neon-pink); margin-top: 4px;">' + k.forbidden_hallucinations.join(', ') + '</div></div>';
        document.getElementById('knowledge-summary').innerHTML = html;
      }
    }

    // Auto load on page load
    window.onload = function() {
      loadStats();
      generateGame();
    };
  </script>
</body>
</html>
"""


def find_free_port(start_port=5050):
    for p in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", p)) != 0:
                return p
    return start_port


def main():
    port = find_free_port(5050)
    server = HTTPServer(("localhost", port), CodeLanAIHandler)
    url = f"http://localhost:{port}"

    print(f"\n=======================================================")
    print(f"🚀 CODELAN AI STUDIO IS RUNNING")
    print(f"👉 Local Web URL: {url}")
    print(f"=======================================================\n")

    # Open browser automatically
    def open_browser():
        time.sleep(1.0)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down CodeLan AI Studio.")
        server.server_close()


if __name__ == "__main__":
    main()
