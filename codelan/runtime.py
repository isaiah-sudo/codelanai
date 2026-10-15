"""
Desktop Game Runtime for CodeLan using Tkinter.
Provides smooth 60 FPS rendering, keyboard & mouse input polling, and event dispatch.
"""

import time
import tkinter as tk
from typing import Optional
from .interpreter import Interpreter

# Mapping Tkinter keysyms to friendly CodeLan key strings
KEY_MAP = {
    "left": "left",
    "right": "right",
    "up": "up",
    "down": "down",
    "space": "space",
    "return": "enter",
    "enter": "enter",
    "escape": "escape",
    "backspace": "backspace",
    "tab": "tab",
    "shift_l": "shift",
    "shift_r": "shift",
    "control_l": "ctrl",
    "control_r": "ctrl",
}

class DesktopGameRunner:
    def __init__(self, interpreter: Interpreter):
        self.interpreter = interpreter
        self.root: Optional[tk.Tk] = None
        self.canvas: Optional[tk.Canvas] = None
        self.is_running = False
        self.last_time = time.perf_counter()

    def run(self):
        # Execute setup hook first so window dimensions and title can be configured
        self.interpreter.execute_setup()

        # If neither update nor draw exists, program was a simple script
        has_game_loop = ("update" in self.interpreter.hooks or "draw" in self.interpreter.hooks)
        if not has_game_loop:
            # Script has already executed top-to-bottom
            return

        self.root = tk.Tk()
        self.root.title(self.interpreter.window_title)
        self.root.geometry(f"{self.interpreter.window_width}x{self.interpreter.window_height}")
        self.root.resizable(False, False)

        # Background color
        self.root.configure(bg=self.interpreter.bg_color)

        # Canvas with double buffering
        self.canvas = tk.Canvas(
            self.root,
            width=self.interpreter.window_width,
            height=self.interpreter.window_height,
            bg=self.interpreter.bg_color,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind inputs
        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.is_running = True
        self.last_time = time.perf_counter()

        # Start game loop
        self._loop()
        self.root.mainloop()

    def _on_close(self):
        self.is_running = False
        if self.root:
            self.root.destroy()

    def _normalize_key(self, event) -> str:
        sym = event.keysym.lower()
        if sym in KEY_MAP:
            return KEY_MAP[sym]
        if event.char and event.char.isalnum():
            return event.char.lower()
        return sym

    def _on_key_press(self, event):
        key = self._normalize_key(event)
        if key not in self.interpreter.keys_held:
            self.interpreter.keys_pressed.add(key)
            self.interpreter.handle_event("key_down", key)
        self.interpreter.keys_held.add(key)

    def _on_key_release(self, event):
        key = self._normalize_key(event)
        self.interpreter.keys_held.discard(key)
        self.interpreter.handle_event("key_up", key)

    def _on_mouse_move(self, event):
        self.interpreter.mouse_x = event.x
        self.interpreter.mouse_y = event.y

    def _on_mouse_down(self, event):
        self.interpreter.mouse_x = event.x
        self.interpreter.mouse_y = event.y
        self.interpreter.mouse_down = True
        self.interpreter.mouse_clicked = True
        self.interpreter.handle_event("mouse_down", "left")

    def _on_mouse_up(self, event):
        self.interpreter.mouse_x = event.x
        self.interpreter.mouse_y = event.y
        self.interpreter.mouse_down = False
        self.interpreter.handle_event("mouse_up", "left")

    def _loop(self):
        if not self.is_running or not self.root:
            return

        now = time.perf_counter()
        dt = now - self.last_time
        self.last_time = now

        self.interpreter.delta_time = min(dt, 0.1)  # clamp to avoid huge delta on freeze
        self.interpreter.frame_count += 1

        # Execute game update logic
        try:
            self.interpreter.execute_update()
        except Exception as e:
            print(f"[CodeLan Error in update]: {e}")
            self._on_close()
            return

        # Execute game render logic
        try:
            draw_cmds = self.interpreter.execute_draw()
        except Exception as e:
            print(f"[CodeLan Error in draw]: {e}")
            self._on_close()
            return

        # Render draw commands to canvas
        self._render(draw_cmds)

        # Reset single-frame inputs
        self.interpreter.keys_pressed.clear()
        self.interpreter.mouse_clicked = False

        # Calculate time to next frame
        elapsed = time.perf_counter() - now
        target_delay = 1.0 / self.interpreter.target_fps
        sleep_ms = max(1, int((target_delay - elapsed) * 1000))

        if self.is_running:
            self.root.after(sleep_ms, self._loop)

    def _render(self, draw_cmds):
        if not self.canvas:
            return

        self.canvas.delete("all")
        w = self.interpreter.window_width
        h = self.interpreter.window_height

        for cmd in draw_cmds:
            ctype = cmd.get("type")

            if ctype == "clear":
                color = cmd.get("color", self.interpreter.bg_color)
                self.canvas.create_rectangle(0, 0, w, h, fill=color, outline="")

            elif ctype == "rect":
                x = cmd["x"]
                y = cmd["y"]
                width = cmd["w"]
                height = cmd["h"]
                fill = cmd.get("fill", "") or ""
                outline = cmd.get("outline", "") or ""
                stroke_w = cmd.get("width", 1)
                self.canvas.create_rectangle(
                    x, y, x + width, y + height,
                    fill=fill,
                    outline=outline,
                    width=stroke_w
                )

            elif ctype == "circle":
                x = cmd["x"]
                y = cmd["y"]
                r = cmd["r"]
                fill = cmd.get("fill", "") or ""
                outline = cmd.get("outline", "") or ""
                stroke_w = cmd.get("width", 1)
                self.canvas.create_oval(
                    x - r, y - r, x + r, y + r,
                    fill=fill,
                    outline=outline,
                    width=stroke_w
                )

            elif ctype == "oval":
                x = cmd["x"]
                y = cmd["y"]
                width = cmd["w"]
                height = cmd["h"]
                fill = cmd.get("fill", "") or ""
                outline = cmd.get("outline", "") or ""
                stroke_w = cmd.get("width", 1)
                self.canvas.create_oval(
                    x, y, x + width, y + height,
                    fill=fill,
                    outline=outline,
                    width=stroke_w
                )

            elif ctype == "line":
                self.canvas.create_line(
                    cmd["x1"], cmd["y1"], cmd["x2"], cmd["y2"],
                    fill=cmd.get("color", "#ffffff"),
                    width=cmd.get("width", 1)
                )

            elif ctype == "triangle":
                fill = cmd.get("fill", "") or ""
                outline = cmd.get("outline", "") or ""
                self.canvas.create_polygon(
                    cmd["x1"], cmd["y1"],
                    cmd["x2"], cmd["y2"],
                    cmd["x3"], cmd["y3"],
                    fill=fill,
                    outline=outline
                )

            elif ctype == "text":
                align = cmd.get("align", "left")
                anchor = tk.W
                if align == "center":
                    anchor = tk.CENTER
                elif align == "right":
                    anchor = tk.E

                size = cmd.get("size", 16)
                font_name = cmd.get("font", "Arial")
                self.canvas.create_text(
                    cmd["x"], cmd["y"],
                    text=cmd["text"],
                    fill=cmd.get("color", "#ffffff"),
                    anchor=anchor,
                    font=(font_name, size, "bold" if size >= 18 else "normal")
                )

            elif ctype == "grid":
                step = cmd.get("step", 40)
                grid_color = cmd.get("color", "#252538")
                for gx in range(0, w, step):
                    self.canvas.create_line(gx, 0, gx, h, fill=grid_color, width=1)
                for gy in range(0, h, step):
                    self.canvas.create_line(0, gy, w, gy, fill=grid_color, width=1)
