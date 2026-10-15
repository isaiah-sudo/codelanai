"""
CodeLan AI Studio - Native Desktop Application Window (PyQt6).
Provides real-time interactive game synthesis, live RL trial-and-error training visualizer,
Q-table / policy inspector, native 60 FPS desktop game launcher, and human-in-the-loop feedback.
"""

import os
import sys
import time
import json
import random
import subprocess
import webbrowser
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QPlainTextEdit, QTabWidget,
    QProgressBar, QSlider, QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QCheckBox, QComboBox, QFileDialog,
    QMessageBox, QFrame, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QRectF, QPointF
from PyQt6.QtGui import (
    QColor, QFont, QPainter, QPen, QBrush, QLinearGradient,
    QSyntaxHighlighter, QTextCharFormat, QIcon, QKeySequence
)

# Project imports
from knowledge_base import knowledge_base
from rl_engine import rl_agent, CodeLanEvaluator
from game_generator import game_generator
from automated_trainer import trainer
from app import transpile_codelan_to_html


# =====================================================================
# CODELAN SYNTAX HIGHLIGHTER
# =====================================================================
class CodeLanSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for CodeLan game code in the code editor."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []

        # Keywords (pink/magenta)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#ff007f"))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keywords = [
            r"\blet\b", r"\bfn\b", r"\breturn\b", r"\bif\b", r"\belse\b",
            r"\bwhile\b", r"\bfor\b", r"\bin\b", r"\brepeat\b", r"\bsetup\b",
            r"\bupdate\b", r"\bdraw\b", r"\bon\b", r"\btrue\b", r"\bfalse\b",
            r"\bnull\b", r"\band\b", r"\bor\b", r"\bnot\b"
        ]
        for kw in keywords:
            self.rules.append((kw, keyword_format))

        # Built-in functions (neon cyan)
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#00f0ff"))
        builtin_format.setFontWeight(QFont.Weight.DemiBold)
        builtins = [
            r"\bwindow\b", r"\bfps\b", r"\bclear\b", r"\bcolor\b", r"\brect\b",
            r"\bcircle\b", r"\boval\b", r"\bline\b", r"\btriangle\b", r"\btext\b",
            r"\btext_centered\b", r"\bgrid\b", r"\bcamera\b", r"\bkey\b",
            r"\bkey_down\b", r"\bmouse_down\b", r"\bmouse_clicked\b",
            r"\bsound\b", r"\bbeep\b", r"\bcollide_rect\b", r"\bcollide_circle\b",
            r"\bcollide_point_rect\b", r"\bcollide_point_circle\b", r"\bdistance\b",
            r"\brandom\b", r"\brand\b", r"\brandom_choice\b", r"\bclamp\b",
            r"\bmin\b", r"\bmax\b", r"\babs\b", r"\bfloor\b", r"\bceil\b",
            r"\bround\b", r"\bpush\b", r"\bpop\b", r"\blen\b"
        ]
        for b in builtins:
            self.rules.append((b, builtin_format))

        # Strings (green)
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#4ade80"))
        self.rules.append((r'"[^"\\]*(\\.[^"\\]*)*"', string_format))
        self.rules.append((r"'[^'\\]*(\\.[^'\\]*)*'", string_format))

        # Numbers (yellow)
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#facc15"))
        self.rules.append((r"\b\d+(\.\d+)?\b", number_format))

        # Comments (slate grey italic)
        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#64748b"))
        self.comment_format.setFontItalic(True)
        self.rules.append((r"//[^\n]*", self.comment_format))

    def highlightBlock(self, text: str):
        import re
        for pattern, fmt in self.rules:
            for match in re.finditer(pattern, text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)


# =====================================================================
# REAL-TIME LEARNING CURVE GRAPH (QPAINTER)
# =====================================================================
class LearningCurveWidget(QWidget):
    """
    Renders an animated, anti-aliased graph of episode rewards and
    rolling average rewards dynamically as the AI learns.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.episodes: List[int] = []
        self.rewards: List[float] = []
        self.rolling_avg: List[float] = []
        self.setMinimumHeight(190)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background-color: #0b1120; border: 1px solid #1e293b; border-radius: 8px;")

    def update_data(self, episodes: List[int], rewards: List[float], rolling_avg: List[float]):
        self.episodes = episodes
        self.rewards = rewards
        self.rolling_avg = rolling_avg
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        pad_l, pad_r, pad_t, pad_b = 50, 20, 25, 30

        # Background
        painter.fillRect(0, 0, w, h, QColor("#0b1120"))

        if not self.rewards or len(self.rewards) < 2:
            painter.setPen(QPen(QColor("#64748b")))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter,
                             "Waiting for training episodes to plot learning curve...")
            return

        min_r = min(-40.0, min(self.rewards) - 10.0)
        max_r = max(60.0, max(self.rewards) + 15.0)
        r_range = max(1.0, max_r - min_r)

        plot_w = w - pad_l - pad_r
        plot_h = h - pad_t - pad_b

        def to_screen(idx, r_val):
            x = pad_l + (idx / (len(self.rewards) - 1)) * plot_w
            y = pad_t + plot_h - ((r_val - min_r) / r_range) * plot_h
            return QPointF(x, y)

        # Draw Grid & Axes
        painter.setPen(QPen(QColor("#1e293b"), 1, Qt.PenStyle.DashLine))
        grid_steps = 4
        painter.setFont(QFont("Segoe UI", 8))
        for i in range(grid_steps + 1):
            val = min_r + (i / grid_steps) * r_range
            y = pad_t + plot_h - (i / grid_steps) * plot_h
            painter.drawLine(QPointF(pad_l, y), QPointF(w - pad_r, y))
            painter.setPen(QColor("#64748b"))
            painter.drawText(QRectF(0, y - 8, pad_l - 6, 16), Qt.AlignmentFlag.AlignRight, f"{val:.0f}")
            painter.setPen(QPen(QColor("#1e293b"), 1, Qt.PenStyle.DashLine))

        # Zero reference line
        if min_r <= 0 <= max_r:
            y_zero = pad_t + plot_h - ((0.0 - min_r) / r_range) * plot_h
            painter.setPen(QPen(QColor("#475569"), 1, Qt.PenStyle.SolidLine))
            painter.drawLine(QPointF(pad_l, y_zero), QPointF(w - pad_r, y_zero))

        # Draw Episode Reward Curve (Cyan)
        pen_rew = QPen(QColor("#00f0ff"), 1.8)
        painter.setPen(pen_rew)
        for i in range(len(self.rewards) - 1):
            p1 = to_screen(i, self.rewards[i])
            p2 = to_screen(i + 1, self.rewards[i + 1])
            painter.drawLine(p1, p2)

        # Draw Rolling Average Curve (Yellow glow)
        if self.rolling_avg:
            pen_avg = QPen(QColor("#facc15"), 2.6)
            painter.setPen(pen_avg)
            for i in range(len(self.rolling_avg) - 1):
                p1 = to_screen(i, self.rolling_avg[i])
                p2 = to_screen(i + 1, self.rolling_avg[i + 1])
                painter.drawLine(p1, p2)

        # Draw latest value point
        last_pt = to_screen(len(self.rewards) - 1, self.rewards[-1])
        painter.setBrush(QBrush(QColor("#00f0ff")))
        painter.setPen(QPen(QColor("#ffffff"), 1.5))
        painter.drawEllipse(last_pt, 4.0, 4.0)

        # Header Legend
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        # Cyan label: Trial Reward
        painter.setPen(QColor("#00f0ff"))
        painter.drawText(pad_l, pad_t - 8, f"● Trial Reward ({self.rewards[-1]:+.1f})")
        # Yellow label: Moving Average
        painter.setPen(QColor("#facc15"))
        avg_val = self.rolling_avg[-1] if self.rolling_avg else 0.0
        painter.drawText(pad_l + 160, pad_t - 8, f"● Moving Avg ({avg_val:+.1f})")


# =====================================================================
# BACKGROUND TRAINING THREAD
# =====================================================================
class TrainingWorker(QThread):
    """Background worker that runs trial-and-error training episodes."""
    step_completed = pyqtSignal(dict)
    training_finished = pyqtSignal(dict)

    def __init__(self, episodes: int = 25, delay: float = 0.08, filepath: str = "CODELAN_README.md"):
        super().__init__()
        self.episodes = episodes
        self.delay = delay
        self.filepath = filepath
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):
        trainer.is_training = True
        total_session_rew = 0.0
        passed_count = 0

        # Load file rules if present
        knowledge_base.load_file(self.filepath)

        for ep in range(1, self.episodes + 1):
            if not self.is_running:
                break

            record = trainer.train_step()
            total_session_rew += record["reward"]
            if record["is_valid_syntax"]:
                passed_count += 1

            payload = {
                "current_episode": ep,
                "total_episodes": self.episodes,
                "record": record,
                "session_avg": round(total_session_rew / ep, 2),
                "accuracy": round((passed_count / ep) * 100.0, 1),
                "stats": rl_agent.get_stats(),
                "learning_curve": rl_agent.get_learning_curve()
            }
            self.step_completed.emit(payload)

            if self.delay > 0:
                time.sleep(self.delay)

        trainer.is_training = False
        rl_agent.save()
        self.training_finished.emit({
            "total_episodes": ep if 'ep' in locals() else 0,
            "total_reward": round(total_session_rew, 2),
            "accuracy": round((passed_count / max(1, ep)) * 100.0, 1) if 'ep' in locals() else 0.0
        })


# =====================================================================
# MAIN DESKTOP APPLICATION WINDOW
# =====================================================================
class CodeLanStudioWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎮 CodeLan AI Studio | Reinforcement Learning Desktop Window")
        self.resize(1340, 890)
        self.setMinimumSize(1100, 720)

        self.current_code = ""
        self.current_intent = None
        self.current_game_genre = "custom"
        self.training_worker: Optional[TrainingWorker] = None

        self._setup_styles()
        self._setup_ui()
        self._load_initial_stats()

        # Auto-generate starter game
        QTimer.singleShot(400, self._generate_starter_game)

    def _setup_styles(self):
        """Dark cyberpunk modern stylesheet."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #090d16;
                color: #f1f5f9;
            }
            QWidget {
                color: #f1f5f9;
                font-family: 'Segoe UI', 'Inter', sans-serif;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid #1e293b;
                background: #0f172a;
                border-radius: 8px;
                top: -1px;
            }
            QTabBar::tab {
                background: #131a2a;
                color: #94a3b8;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                border: 1px solid #1e293b;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background: #1e293b;
                color: #00f0ff;
                border-top: 2px solid #00f0ff;
            }
            QTabBar::tab:hover {
                color: #f1f5f9;
                background: #192237;
            }
            QGroupBox {
                border: 1px solid #1e293b;
                border-radius: 8px;
                margin-top: 14px;
                padding-top: 14px;
                font-weight: 600;
                color: #38bdf8;
                background-color: #111827;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                background-color: #090d16;
            }
            QPushButton {
                background-color: #1e293b;
                color: #f1f5f9;
                border: 1px solid #334155;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #00f0ff;
                color: #00f0ff;
            }
            QPushButton:pressed {
                background-color: #0f172a;
            }
            QPushButton#btnNeonPrimary {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #00f0ff);
                color: #090d16;
                border: none;
                font-weight: 700;
                font-size: 13px;
            }
            QPushButton#btnNeonPrimary:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #67e8f9);
            }
            QPushButton#btnReward {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #15803d, stop:1 #22c55e);
                color: #ffffff;
                border: none;
            }
            QPushButton#btnReward:hover {
                background: #16a34a;
            }
            QPushButton#btnPunish {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #be123c, stop:1 #f43f5e);
                color: #ffffff;
                border: none;
            }
            QPushButton#btnPunish:hover {
                background: #e11d48;
            }
            QPlainTextEdit, QTextEdit {
                background-color: #0b1120;
                color: #f1f5f9;
                border: 1px solid #1e293b;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', 'Fira Code', monospace;
                font-size: 13px;
            }
            QTableWidget {
                background-color: #0b1120;
                color: #f1f5f9;
                gridline-color: #1e293b;
                border: 1px solid #1e293b;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #131a2a;
                color: #94a3b8;
                padding: 6px;
                border: 1px solid #1e293b;
                font-weight: 600;
            }
            QProgressBar {
                border: 1px solid #1e293b;
                border-radius: 5px;
                background-color: #0b1120;
                text-align: center;
                color: #ffffff;
                font-weight: 600;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f0ff, stop:1 #a855f7);
                border-radius: 4px;
            }
            QScrollBar:vertical {
                border: none;
                background: #0b1120;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #243048;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #38bdf8;
            }
        """)

    def _setup_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)

        # -------------------------------------------------------------
        # TOP HEADER & METRICS RIBBON
        # -------------------------------------------------------------
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #111827; border: 1px solid #1e293b; border-radius: 10px; padding: 6px 14px;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(6, 4, 6, 4)

        # Title Brand
        title_box = QVBoxLayout()
        title_lbl = QLabel("🎮 CODELAN AI STUDIO")
        title_lbl.setStyleSheet("font-size: 19px; font-weight: 900; color: #00f0ff; letter-spacing: 1px;")
        sub_lbl = QLabel("Reinforcement Learning Engine & Trial-and-Error Code Synthesizer")
        sub_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Metrics Badges
        def make_badge(title_text: str, default_val: str, color: str = "#00f0ff"):
            box = QFrame()
            box.setStyleSheet(f"background-color: #0b1120; border: 1px solid #1e293b; border-radius: 6px; padding: 4px 10px;")
            l = QVBoxLayout(box)
            l.setContentsMargins(2, 2, 2, 2)
            l.setSpacing(1)
            t = QLabel(title_text)
            t.setStyleSheet("font-size: 10px; color: #64748b; font-weight: 600; text-transform: uppercase;")
            v = QLabel(default_val)
            v.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {color};")
            l.addWidget(t, alignment=Qt.AlignmentFlag.AlignCenter)
            l.addWidget(v, alignment=Qt.AlignmentFlag.AlignCenter)
            return box, v

        self.badge_episodes, self.lbl_episodes = make_badge("Episodes", "0", "#00f0ff")
        self.badge_reward, self.lbl_reward = make_badge("Lifetime Reward", "+0.0", "#22c55e")
        self.badge_avg, self.lbl_avg = make_badge("Avg Reward", "0.0", "#eab308")
        self.badge_acc, self.lbl_acc = make_badge("AST Pass Rate", "100%", "#a855f7")
        self.badge_eps, self.lbl_eps = make_badge("Epsilon (Explore)", "20.0%", "#ff007f")

        header_layout.addWidget(self.badge_episodes)
        header_layout.addWidget(self.badge_reward)
        header_layout.addWidget(self.badge_avg)
        header_layout.addWidget(self.badge_acc)
        header_layout.addWidget(self.badge_eps)

        main_layout.addWidget(header_frame)

        # -------------------------------------------------------------
        # MAIN TABBED CONTAINER
        # -------------------------------------------------------------
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: Game Studio & Synthesizer
        self.tab_studio = QWidget()
        self._build_studio_tab()
        self.tabs.addTab(self.tab_studio, "🎮 AI Game Studio")

        # Tab 2: Live RL Visualizer (Watch it Learn!)
        self.tab_visualizer = QWidget()
        self._build_visualizer_tab()
        self.tabs.addTab(self.tab_visualizer, "🧠 Live RL Learning Visualizer")

        # Tab 3: Language Knowledge Base
        self.tab_knowledge = QWidget()
        self._build_knowledge_tab()
        self.tabs.addTab(self.tab_knowledge, "📚 Language Knowledge Base")

        # Tab 4: History & Logs
        self.tab_history = QWidget()
        self._build_history_tab()
        self.tabs.addTab(self.tab_history, "📜 RL History & Human Feedback")

    # =================================================================
    # TAB 1: AI GAME STUDIO & GENERATOR
    # =================================================================
    def _build_studio_tab(self):
        layout = QHBoxLayout(self.tab_studio)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # --- Left Panel: Prompt & Controls ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # Prompt Input
        prompt_group = QGroupBox("NATURAL LANGUAGE GAME SPECIFICATION")
        pg_layout = QVBoxLayout(prompt_group)

        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setPlaceholderText("Describe your game idea in plain English...\nE.g.: 'Make a retro space shooter with laser sounds and exploding aliens'")
        self.prompt_edit.setMaximumHeight(85)
        self.prompt_edit.setPlainText("Make a retro space shooter with laser sounds and exploding aliens")
        pg_layout.addWidget(self.prompt_edit)

        # Quick Preset Chips
        chips_lbl = QLabel("Quick Genre Presets:")
        chips_lbl.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600;")
        pg_layout.addWidget(chips_lbl)

        chips_layout1 = QHBoxLayout()
        chips_layout2 = QHBoxLayout()

        presets1 = [
            ("🚀 Space Shooter", "Make a retro space shooter with laser sounds and exploding aliens"),
            ("🏓 Neon Pong", "Create a 2-player neon pong game with bouncing ball and paddle sounds"),
            ("🐍 Cyber Snake", "Make a cyber snake game that eats glowing food pellets"),
            ("🧱 Breakout", "Make a breakout brick breaker with colored bricks and bounce physics")
        ]
        presets2 = [
            ("🐦 Flappy Bird", "Build a flappy bird game with gravity and pipe obstacles"),
            ("🧗 Platformer", "Create a vertical platformer where player bounces higher and higher"),
            ("☄️ Asteroids", "Dodge falling asteroids with arrow keys and collect energy gems"),
            ("🎯 Clicker", "Click on fast disappearing targets for high score")
        ]

        for label, text in presets1:
            btn = QPushButton(label)
            btn.setStyleSheet("font-size: 11px; padding: 4px 8px;")
            btn.clicked.connect(lambda _, t=text: self.prompt_edit.setPlainText(t))
            chips_layout1.addWidget(btn)

        for label, text in presets2:
            btn = QPushButton(label)
            btn.setStyleSheet("font-size: 11px; padding: 4px 8px;")
            btn.clicked.connect(lambda _, t=text: self.prompt_edit.setPlainText(t))
            chips_layout2.addWidget(btn)

        pg_layout.addLayout(chips_layout1)
        pg_layout.addLayout(chips_layout2)
        left_layout.addWidget(prompt_group)

        # RL Feature Policy Controls
        policy_group = QGroupBox("REINFORCEMENT LEARNING POLICY CONTROLS")
        pol_layout = QVBoxLayout(policy_group)

        self.chk_auto_rl = QCheckBox("🤖 AI Autonomous Decisions (Consult RL Policy Q-Values)")
        self.chk_auto_rl.setChecked(True)
        self.chk_auto_rl.setStyleSheet("color: #00f0ff; font-weight: 700;")
        pol_layout.addWidget(self.chk_auto_rl)

        # Feature overrides
        f_row = QHBoxLayout()
        self.chk_audio = QCheckBox("🔊 Sound FX")
        self.chk_audio.setChecked(True)
        self.chk_particles = QCheckBox("✨ Particles")
        self.chk_particles.setChecked(True)
        self.chk_highscore = QCheckBox("🏆 High Score")
        self.chk_highscore.setChecked(True)
        self.chk_shake = QCheckBox("📳 Screen Shake")
        self.chk_shake.setChecked(False)

        f_row.addWidget(self.chk_audio)
        f_row.addWidget(self.chk_particles)
        f_row.addWidget(self.chk_highscore)
        f_row.addWidget(self.chk_shake)
        pol_layout.addLayout(f_row)

        left_layout.addWidget(policy_group)

        # Generate Button
        self.btn_generate = QPushButton("✨ SYNTHESIZE CODELAN GAME (RL GUIDED)")
        self.btn_generate.setObjectName("btnNeonPrimary")
        self.btn_generate.setMinimumHeight(44)
        self.btn_generate.clicked.connect(self._on_synthesize_clicked)
        left_layout.addWidget(self.btn_generate)

        # Human Feedback Panel
        hf_group = QGroupBox("HUMAN-IN-THE-LOOP RL FEEDBACK")
        hf_layout = QVBoxLayout(hf_group)

        hf_info = QLabel("Give immediate positive or negative reinforcement to guide the AI's future games:")
        hf_info.setStyleSheet("color: #94a3b8; font-size: 11px;")
        hf_layout.addWidget(hf_info)

        hf_btn_row = QHBoxLayout()
        self.btn_reward = QPushButton("👍 Reward AI (+15 pts)")
        self.btn_reward.setObjectName("btnReward")
        self.btn_reward.clicked.connect(lambda: self._send_human_feedback(15.0, "Human approved game quality"))

        self.btn_punish = QPushButton("👎 Punish AI (-15 pts)")
        self.btn_punish.setObjectName("btnPunish")
        self.btn_punish.clicked.connect(lambda: self._send_human_feedback(-15.0, "Human disliked game"))

        hf_btn_row.addWidget(self.btn_reward)
        hf_btn_row.addWidget(self.btn_punish)
        hf_layout.addLayout(hf_btn_row)

        self.lbl_feedback_status = QLabel("Awaiting generation...")
        self.lbl_feedback_status.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
        hf_layout.addWidget(self.lbl_feedback_status)

        left_layout.addWidget(hf_group)
        left_layout.addStretch()

        splitter.addWidget(left_widget)

        # --- Right Panel: Code Editor & Execution ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # Code Editor Header & Status Badge
        top_bar = QHBoxLayout()
        code_lbl = QLabel("CODELAN SOURCE CODE (.clan):")
        code_lbl.setStyleSheet("font-weight: 700; color: #38bdf8;")
        top_bar.addWidget(code_lbl)

        top_bar.addStretch()

        self.lbl_syntax_badge = QLabel("✅ AST Valid: Ready")
        self.lbl_syntax_badge.setStyleSheet("background-color: #14532d; color: #4ade80; border: 1px solid #22c55e; border-radius: 4px; padding: 3px 8px; font-weight: 700; font-size: 11px;")
        top_bar.addWidget(self.lbl_syntax_badge)

        right_layout.addLayout(top_bar)

        # Editor
        self.code_editor = QPlainTextEdit()
        self.code_highlighter = CodeLanSyntaxHighlighter(self.code_editor.document())
        self.code_editor.textChanged.connect(self._on_code_edited)
        right_layout.addWidget(self.code_editor)

        # Action Buttons Bar
        btn_bar = QHBoxLayout()

        self.btn_run_desktop = QPushButton("▶ Run Native Desktop Window (60 FPS)")
        self.btn_run_desktop.setObjectName("btnNeonPrimary")
        self.btn_run_desktop.clicked.connect(self._run_desktop_game)

        self.btn_play_web = QPushButton("🌐 Play in Browser")
        self.btn_play_web.clicked.connect(self._play_web_game)

        self.btn_copy_code = QPushButton("📋 Copy Code")
        self.btn_copy_code.clicked.connect(self._copy_code)

        self.btn_save_clan = QPushButton("💾 Save .clan")
        self.btn_save_clan.clicked.connect(self._save_clan_file)

        btn_bar.addWidget(self.btn_run_desktop)
        btn_bar.addWidget(self.btn_play_web)
        btn_bar.addWidget(self.btn_copy_code)
        btn_bar.addWidget(self.btn_save_clan)

        right_layout.addLayout(btn_bar)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 6)

    # =================================================================
    # TAB 2: LIVE RL LEARNING VISUALIZER (WATCH IT LEARN!)
    # =================================================================
    def _build_visualizer_tab(self):
        layout = QVBoxLayout(self.tab_visualizer)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # 1. Training Controls Bar
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet("background-color: #111827; border: 1px solid #1e293b; border-radius: 8px; padding: 8px 12px;")
        ctrl_layout = QHBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(4, 4, 4, 4)
        ctrl_layout.setSpacing(10)

        self.btn_auto_train = QPushButton("▶ Start Auto-Train")
        self.btn_auto_train.setObjectName("btnNeonPrimary")
        self.btn_auto_train.clicked.connect(self._toggle_auto_train)
        ctrl_layout.addWidget(self.btn_auto_train)

        self.btn_step_trial = QPushButton("⏭ Step 1 Trial")
        self.btn_step_trial.clicked.connect(self._step_single_trial)
        ctrl_layout.addWidget(self.btn_step_trial)

        self.btn_train_25 = QPushButton("🚀 Train 25 Episodes")
        self.btn_train_25.clicked.connect(lambda: self._start_batch_training(25))
        ctrl_layout.addWidget(self.btn_train_25)

        self.btn_train_100 = QPushButton("🔥 Train 100 Episodes")
        self.btn_train_100.clicked.connect(lambda: self._start_batch_training(100))
        ctrl_layout.addWidget(self.btn_train_100)

        # Speed slider
        speed_lbl = QLabel("Speed:")
        speed_lbl.setStyleSheet("color: #94a3b8; font-weight: 600;")
        ctrl_layout.addWidget(speed_lbl)

        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_speed.setRange(20, 600)
        self.slider_speed.setValue(80)
        self.slider_speed.setFixedWidth(100)
        ctrl_layout.addWidget(self.slider_speed)

        self.btn_load_file = QPushButton("📂 Train on File...")
        self.btn_load_file.clicked.connect(self._select_training_file)
        ctrl_layout.addWidget(self.btn_load_file)

        self.btn_reset_rl = QPushButton("🔄 Reset Model")
        self.btn_reset_rl.clicked.connect(self._reset_rl_model)
        ctrl_layout.addWidget(self.btn_reset_rl)

        layout.addWidget(ctrl_frame)

        # 2. Real-Time Learning Curve Graph
        curve_group = QGroupBox("REAL-TIME LEARNING CURVE & REWARD TRAJECTORY")
        cg_layout = QVBoxLayout(curve_group)
        self.curve_widget = LearningCurveWidget()
        cg_layout.addWidget(self.curve_widget)
        layout.addWidget(curve_group, stretch=4)

        # 3. Lower Splitter: Live Episode Feed (Left) & Q-Table / Policy Inspector (Right)
        lower_splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(lower_splitter, stretch=5)

        # Left Column: Live Trial Episode Stream
        feed_group = QGroupBox("LIVE TRIAL EPISODE FEED")
        feed_layout = QVBoxLayout(feed_group)

        self.trial_card_text = QTextEdit()
        self.trial_card_text.setReadOnly(True)
        self.trial_card_text.setStyleSheet("background-color: #0b1120; border: 1px solid #1e293b; border-radius: 6px; font-family: monospace; font-size: 12px;")
        feed_layout.addWidget(self.trial_card_text)
        lower_splitter.addWidget(feed_group)

        # Right Column: Live Q-Table & Policy Inspector
        q_group = QGroupBox("LIVE Q-TABLE & POLICY WEIGHTS INSPECTOR")
        q_layout = QVBoxLayout(q_group)

        # Table showing state-action Q-values
        self.q_table_widget = QTableWidget()
        self.q_table_widget.setColumnCount(3)
        self.q_table_widget.setHorizontalHeaderLabels(["State / Context", "Action", "Q-Value"])
        self.q_table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.q_table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.q_table_widget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        q_layout.addWidget(self.q_table_widget)

        lower_splitter.addWidget(q_group)
        lower_splitter.setStretchFactor(0, 5)
        lower_splitter.setStretchFactor(1, 5)

    # =================================================================
    # TAB 3: LANGUAGE KNOWLEDGE BASE
    # =================================================================
    def _build_knowledge_tab(self):
        layout = QVBoxLayout(self.tab_knowledge)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        kb_summary = knowledge_base.get_summary()

        # Top summary card
        top_card = QFrame()
        top_card.setStyleSheet("background-color: #111827; border: 1px solid #1e293b; border-radius: 8px; padding: 10px 14px;")
        tc_layout = QHBoxLayout(top_card)

        info1 = QLabel(f"<b>Specification File:</b> {kb_summary.get('source_file')}")
        info2 = QLabel(f"<b>Discovered Built-ins:</b> {kb_summary.get('total_builtins')}")
        info3 = QLabel(f"<b>Audio Effects:</b> {', '.join(kb_summary.get('audio_effects', []))}")

        tc_layout.addWidget(info1)
        tc_layout.addWidget(info2)
        tc_layout.addWidget(info3)
        layout.addWidget(top_card)

        # Table of Built-in Functions
        builtins_group = QGroupBox("CODELAN STANDARD BUILT-IN FUNCTIONS")
        bg_layout = QVBoxLayout(builtins_group)

        self.kb_table = QTableWidget()
        self.kb_table.setColumnCount(3)
        self.kb_table.setHorizontalHeaderLabels(["Function Name", "Arguments Range", "Description"])
        self.kb_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.kb_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.kb_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # Populate builtins
        sigs = knowledge_base.builtin_signatures
        self.kb_table.setRowCount(len(sigs))
        for row, (fn, info) in enumerate(sorted(sigs.items())):
            item_fn = QTableWidgetItem(f"{fn}()")
            item_fn.setForeground(QColor("#00f0ff"))
            item_fn.setFont(QFont("Consolas", 11, QFont.Weight.Bold))

            min_a = info.get("min_args", 0)
            max_a = info.get("max_args", 0)
            args_str = f"{min_a} - {max_a}" if min_a != max_a else str(min_a)
            item_args = QTableWidgetItem(args_str)

            item_desc = QTableWidgetItem(info.get("desc", ""))

            self.kb_table.setItem(row, 0, item_fn)
            self.kb_table.setItem(row, 1, item_args)
            self.kb_table.setItem(row, 2, item_desc)

        bg_layout.addWidget(self.kb_table)
        layout.addWidget(builtins_group)

        # Forbidden tokens card
        forbid_group = QGroupBox("ANTI-HALLUCINATION RULES & FORBIDDEN TOKENS")
        forbid_layout = QVBoxLayout(forbid_group)
        forbid_text = QLabel(
            "The RL Agent is heavily penalized whenever foreign syntax from Python/JS/Java is used:\n" +
            ", ".join(sorted(knowledge_base.forbidden_hallucinations))
        )
        forbid_text.setStyleSheet("color: #f43f5e; font-family: monospace; font-size: 11px;")
        forbid_text.setWordWrap(True)
        forbid_layout.addWidget(forbid_text)
        layout.addWidget(forbid_group)

    # =================================================================
    # TAB 4: RL HISTORY & HUMAN FEEDBACK
    # =================================================================
    def _build_history_tab(self):
        layout = QVBoxLayout(self.tab_history)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Table of past episodes
        hist_group = QGroupBox("RECENT TRAINING EPISODES")
        hg_layout = QVBoxLayout(hist_group)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["Episode", "Genre", "Reward", "Syntax Status", "Prompt Tested"])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        hg_layout.addWidget(self.history_table)
        layout.addWidget(hist_group)

        # Table of Human feedback
        fb_group = QGroupBox("HUMAN FEEDBACK AUDIT LOG")
        fbg_layout = QVBoxLayout(fb_group)

        self.feedback_table = QTableWidget()
        self.feedback_table.setColumnCount(4)
        self.feedback_table.setHorizontalHeaderLabels(["Timestamp", "Genre", "Reward Points", "Note"])
        self.feedback_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.feedback_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.feedback_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.feedback_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        fbg_layout.addWidget(self.feedback_table)
        layout.addWidget(fb_group)

    # =================================================================
    # LOGIC & EVENTS
    # =================================================================
    def _load_initial_stats(self):
        """Loads and updates top KPI ribbons and learning curve."""
        stats = rl_agent.get_stats()
        self._update_stats_display(stats)
        self._update_q_table_display()
        self._update_history_tables()

        # Update curve
        curve = rl_agent.get_learning_curve()
        self.curve_widget.update_data(curve["episodes"], curve["rewards"], curve["rolling_avg"])

    def _update_stats_display(self, stats: Dict[str, Any]):
        self.lbl_episodes.setText(str(stats.get("total_episodes", 0)))
        rew = stats.get("total_reward_lifetime", 0.0)
        self.lbl_reward.setText(f"{rew:+.1f}")
        self.lbl_avg.setText(f"{stats.get('avg_recent_reward', 0.0):+.1f}")
        self.lbl_acc.setText(f"{stats.get('accuracy_percent', 100.0):.1f}%")
        self.lbl_eps.setText(f"{stats.get('epsilon', 0.2) * 100:.1f}%")

    def _update_q_table_display(self):
        """Refreshes the Q-table inspector."""
        q_dict = rl_agent.q_table
        rows = []
        for state, actions in sorted(q_dict.items()):
            for action, q_val in sorted(actions.items()):
                rows.append((state, action, q_val))

        self.q_table_widget.setRowCount(len(rows))
        for idx, (st, act, val) in enumerate(rows):
            item_st = QTableWidgetItem(st)
            item_act = QTableWidgetItem(act)
            item_val = QTableWidgetItem(f"{val:+.2f}")

            if val > 15.0:
                item_val.setForeground(QColor("#4ade80"))
            elif val < 0.0:
                item_val.setForeground(QColor("#f43f5e"))
            else:
                item_val.setForeground(QColor("#facc15"))

            self.q_table_widget.setItem(idx, 0, item_st)
            self.q_table_widget.setItem(idx, 1, item_act)
            self.q_table_widget.setItem(idx, 2, item_val)

    def _update_history_tables(self):
        """Updates history and feedback tables."""
        # 1. Episodes
        hist = rl_agent.history[-40:]
        self.history_table.setRowCount(len(hist))
        for row, item in enumerate(reversed(hist)):
            self.history_table.setItem(row, 0, QTableWidgetItem(str(item.get("episode", ""))))
            self.history_table.setItem(row, 1, QTableWidgetItem(item.get("genre", "")))

            rew = item.get("reward", 0.0)
            item_rew = QTableWidgetItem(f"{rew:+.1f}")
            item_rew.setForeground(QColor("#4ade80") if rew > 0 else QColor("#f43f5e"))
            self.history_table.setItem(row, 2, item_rew)

            status = "✅ PASS" if item.get("is_valid_syntax") else "❌ FAIL"
            self.history_table.setItem(row, 3, QTableWidgetItem(status))
            self.history_table.setItem(row, 4, QTableWidgetItem(item.get("prompt", "")))

        # 2. Feedback
        fb = rl_agent.human_feedback_log[-30:]
        self.feedback_table.setRowCount(len(fb))
        for row, item in enumerate(reversed(fb)):
            self.feedback_table.setItem(row, 0, QTableWidgetItem(item.get("timestamp", "")[:19]))
            self.feedback_table.setItem(row, 1, QTableWidgetItem(item.get("genre", "")))

            pts = item.get("reward_points", 0.0)
            item_pts = QTableWidgetItem(f"{pts:+.1f}")
            item_pts.setForeground(QColor("#4ade80") if pts > 0 else QColor("#f43f5e"))
            self.feedback_table.setItem(row, 2, item_pts)
            self.feedback_table.setItem(row, 3, QTableWidgetItem(item.get("note", "")))

    def _generate_starter_game(self):
        """Generates starter game on startup."""
        self._on_synthesize_clicked()

    def _on_synthesize_clicked(self):
        """Handles game synthesis from user prompt."""
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            prompt = "Make a retro space shooter with laser sounds and exploding aliens"

        # Feature overrides if user unchecks Auto-RL
        overrides = None
        if not self.chk_auto_rl.isChecked():
            overrides = {
                "sound_effects": self.chk_audio.isChecked(),
                "particles": self.chk_particles.isChecked(),
                "high_score": self.chk_highscore.isChecked(),
                "screenshake": self.chk_shake.isChecked()
            }

        code, intent = game_generator.generate_game(prompt, feature_overrides=overrides)
        self.current_code = code
        self.current_intent = intent
        self.current_game_genre = intent.genre

        # Check code syntax
        evaluator = CodeLanEvaluator(knowledge_base)
        report = evaluator.evaluate(code, intent_spec={"genre": intent.genre, "require_sound": intent.require_sound})

        # Update editor
        self.code_editor.setPlainText(code)

        # Update syntax badge
        if report.is_valid_syntax:
            self.lbl_syntax_badge.setText(f"✅ AST Valid ({len(report.matched_builtins)} builtins, +{report.total_reward:.0f} pts)")
            self.lbl_syntax_badge.setStyleSheet("background-color: #14532d; color: #4ade80; border: 1px solid #22c55e; border-radius: 4px; padding: 3px 8px; font-weight: 700; font-size: 11px;")
        else:
            self.lbl_syntax_badge.setText(f"❌ Syntax Error: {report.syntax_error}")
            self.lbl_syntax_badge.setStyleSheet("background-color: #4c0519; color: #f43f5e; border: 1px solid #e11d48; border-radius: 4px; padding: 3px 8px; font-weight: 700; font-size: 11px;")

        self.lbl_feedback_status.setText(f"Synthesized '{intent.title}' [{intent.genre}]. Ready to run or rate!")

    def _on_code_edited(self):
        """Live updates syntax badge when code is typed into editor."""
        self.current_code = self.code_editor.toPlainText()
        # Fast debounce or live check
        if len(self.current_code) > 20:
            evaluator = CodeLanEvaluator(knowledge_base)
            report = evaluator.evaluate(self.current_code)
            if report.is_valid_syntax:
                self.lbl_syntax_badge.setText(f"✅ AST Valid ({len(report.matched_builtins)} builtins)")
                self.lbl_syntax_badge.setStyleSheet("background-color: #14532d; color: #4ade80; border: 1px solid #22c55e; border-radius: 4px; padding: 3px 8px; font-weight: 700; font-size: 11px;")
            else:
                self.lbl_syntax_badge.setText(f"❌ Syntax Flaw: {report.syntax_error or 'Foreign syntax'}")
                self.lbl_syntax_badge.setStyleSheet("background-color: #4c0519; color: #f43f5e; border: 1px solid #e11d48; border-radius: 4px; padding: 3px 8px; font-weight: 700; font-size: 11px;")

    def _send_human_feedback(self, points: float, note: str):
        """Sends immediate human reinforcement to the RL model."""
        genre = self.current_game_genre or "custom"
        rl_agent.record_human_feedback(genre, points, note)
        stats = rl_agent.get_stats()
        self._update_stats_display(stats)
        self._update_q_table_display()
        self._update_history_tables()

        symbol = "🏆 REWARDED" if points > 0 else "⚡ PENALIZED"
        self.lbl_feedback_status.setText(f"{symbol} AI with {points:+.1f} points for '{genre}'! Model saved.")

    def _run_desktop_game(self):
        """Runs the native 60 FPS desktop game in an actual separate window."""
        code = self.code_editor.toPlainText()
        if not code.strip():
            QMessageBox.warning(self, "No Code", "Please synthesize a game first!")
            return

        temp_file = Path(__file__).resolve().parent / "temp_game.clan"
        temp_file.write_text(code, encoding="utf-8")

        def launch():
            try:
                subprocess.run([sys.executable, "-m", "codelan.cli", "run", str(temp_file)])
            except Exception as ex:
                print(f"Error launching desktop runner: {ex}")

        threading.Thread(target=launch, daemon=True).start()

    def _play_web_game(self):
        """Transpiles to HTML5 canvas and opens in browser."""
        code = self.code_editor.toPlainText()
        if not code.strip():
            return

        title = self.current_intent.title if self.current_intent else "CodeLan Game"
        html_str = transpile_codelan_to_html(code, title=title)
        temp_html = Path(__file__).resolve().parent / "temp_game.html"
        temp_html.write_text(html_str, encoding="utf-8")
        webbrowser.open(str(temp_html.resolve()))

    def _copy_code(self):
        QApplication.clipboard().setText(self.code_editor.toPlainText())
        QMessageBox.information(self, "Copied", "CodeLan code copied to clipboard!")

    def _save_clan_file(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save CodeLan Game", f"{self.current_game_genre}.clan", "CodeLan Files (*.clan);;All Files (*)")
        if filename:
            Path(filename).write_text(self.code_editor.toPlainText(), encoding="utf-8")
            QMessageBox.information(self, "Saved", f"Game saved to {filename}")

    # =================================================================
    # LIVE TRAINING CONTROLS & VISUALIZATION
    # =================================================================
    def _step_single_trial(self):
        """Executes a single trial episode and immediately renders the learning step."""
        rec = trainer.train_step()
        stats = rl_agent.get_stats()
        self._update_stats_display(stats)
        self._update_q_table_display()
        self._update_history_tables()

        # Update curve
        curve = rl_agent.get_learning_curve()
        self.curve_widget.update_data(curve["episodes"], curve["rewards"], curve["rolling_avg"])

        # Render rich trial card
        self._render_trial_card(rec)

    def _toggle_auto_train(self):
        """Starts or pauses continuous live training."""
        if self.training_worker and self.training_worker.isRunning():
            self.training_worker.stop()
            self.training_worker.wait()
            self.btn_auto_train.setText("▶ Resume Auto-Train")
        else:
            self._start_batch_training(episodes=200)
            self.btn_auto_train.setText("⏸ Pause Auto-Train")

    def _start_batch_training(self, episodes: int = 25):
        """Starts training thread with given episode count."""
        if self.training_worker and self.training_worker.isRunning():
            self.training_worker.stop()
            self.training_worker.wait()

        delay = self.slider_speed.value() / 1000.0
        self.training_worker = TrainingWorker(episodes=episodes, delay=delay)
        self.training_worker.step_completed.connect(self._on_training_step)
        self.training_worker.training_finished.connect(self._on_training_finished)
        self.training_worker.start()

    def _on_training_step(self, payload: dict):
        """Called every time an episode finishes in the background."""
        rec = payload["record"]
        stats = payload["stats"]
        curve = payload["learning_curve"]

        # Update top KPIs
        self._update_stats_display(stats)

        # Update Curve
        self.curve_widget.update_data(curve["episodes"], curve["rewards"], curve["rolling_avg"])

        # Render Live Feed Card
        self._render_trial_card(rec)

        # Update Q-table
        self._update_q_table_display()

    def _on_training_finished(self, summary: dict):
        self.btn_auto_train.setText("▶ Start Auto-Train")
        self._update_history_tables()

    def _render_trial_card(self, rec: dict):
        """Displays formatted trial diagnostics in the live episode feed."""
        syntax_badge = "<span style='color: #4ade80; font-weight: bold;'>✅ AST PASS</span>" if rec.get("is_valid_syntax") else "<span style='color: #f43f5e; font-weight: bold;'>❌ AST FAIL</span>"
        rew_color = "#4ade80" if rec.get("reward", 0) > 0 else "#f43f5e"

        mutation_html = ""
        if rec.get("is_mutation_tested"):
            mutation_html = f"<div style='color: #facc15; margin: 4px 0;'>🎲 <b>Exploratory Test:</b> {rec.get('mutation_desc')}</div>"

        rewards_list = "".join(f"<li style='color: #4ade80;'>+{r['points']:.0f} pts: {r['reason']}</li>" for r in rec.get("rewards_breakdown", [])[:6])
        punishments_list = "".join(f"<li style='color: #f43f5e;'>{p['points']:.0f} pts: {p['reason']}</li>" for p in rec.get("punishments_breakdown", [])[:4])

        html = f"""
        <div style='background-color: #0b1120; border-bottom: 1px solid #1e293b; padding: 10px;'>
            <div style='display: flex; justify-content: space-between;'>
                <b style='color: #00f0ff;'>[EPISODE #{rec.get("episode")}] Genre: {rec.get("genre").upper()}</b>
                &nbsp;&nbsp;{syntax_badge}&nbsp;&nbsp;
                <b style='color: {rew_color}; font-size: 14px;'>{rec.get("reward"):+.1f} pts</b>
            </div>
            <div style='color: #94a3b8; font-style: italic; margin-top: 4px;'>"{rec.get('prompt')}"</div>
            {mutation_html}
            <div style='margin-top: 6px;'>
                <ul style='margin: 0; padding-left: 20px;'>
                    {rewards_list}
                    {punishments_list}
                </ul>
            </div>
        </div>
        """
        self.trial_card_text.setHtml(html)

    def _select_training_file(self):
        """Allows user to select any language specification or code file to train from."""
        filename, _ = QFileDialog.getOpenFileName(self, "Select Language File", "", "Markdown & Clan (*.md *.clan *.txt);;All Files (*)")
        if filename:
            self._start_batch_training(episodes=30)

    def _reset_rl_model(self):
        """Resets model to baseline."""
        reply = QMessageBox.question(self, "Reset Model", "Are you sure you want to reset all learned Q-values and policy weights to defaults?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            rl_agent.reset_weights()
            self._load_initial_stats()
            QMessageBox.information(self, "Reset", "RL Model has been reset to initial baseline weights.")


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================
def main():
    # Enable High DPI scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    app.setApplicationName("CodeLan AI Studio")

    window = CodeLanStudioWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
