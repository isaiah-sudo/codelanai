"""
Web Exporter and Transpiler for CodeLan.
Compiles CodeLan source into a standalone, playable HTML5 canvas game.
"""

import json
from typing import Any
from .ast_nodes import (
    ASTNode, NumberLiteral, StringLiteral, BooleanLiteral, NullLiteral,
    Identifier, ListLiteral, DictLiteral, BinaryOp, UnaryOp, Assignment,
    FunctionCall, MemberAccess, IndexAccess, ExpressionStatement,
    VarDeclaration, BlockStatement, IfStatement, WhileStatement,
    ForInStatement, ForCStyleStatement, RepeatStatement, FunctionDeclaration,
    ReturnStatement, BreakStatement, ContinueStatement, GameHook,
    EventHandler, Program
)

JS_BUILTINS = """
// --- CodeLan Web Audio Synthesizer ---
let _audioCtx = null;
function _getAudioContext() {
    if (!_audioCtx) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) _audioCtx = new AudioCtx();
    }
    if (_audioCtx && _audioCtx.state === 'suspended') {
        _audioCtx.resume();
    }
    return _audioCtx;
}

function sound(name) {
    const ctx = _getAudioContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    name = String(name).toLowerCase().trim();

    if (name === "laser" || name === "shoot") {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sawtooth";
        osc.frequency.setValueAtTime(880, now);
        osc.frequency.exponentialRampToValueAtTime(110, now + 0.15);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.15);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.15);
    } else if (name === "jump") {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "square";
        osc.frequency.setValueAtTime(150, now);
        osc.frequency.exponentialRampToValueAtTime(600, now + 0.18);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.18);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.18);
    } else if (name === "coin" || name === "pickup") {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(987.77, now);
        osc.frequency.setValueAtTime(1318.51, now + 0.08);
        gain.gain.setValueAtTime(0.25, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.25);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now);
        osc.stop(now + 0.25);
    } else if (name === "hit" || name === "explosion" || name === "boom") {
        const bufferSize = ctx.sampleRate * 0.25;
        const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (bufferSize * 0.3));
        }
        const noise = ctx.createBufferSource();
        noise.buffer = buffer;
        const gain = ctx.createGain();
        gain.gain.setValueAtTime(0.3, now);
        noise.connect(gain);
        gain.connect(ctx.destination);
        noise.start(now);
    } else if (name === "powerup") {
        [330, 392, 523, 659].forEach((freq, idx) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = "triangle";
            osc.frequency.setValueAtTime(freq, now + idx * 0.07);
            gain.gain.setValueAtTime(0.2, now + idx * 0.07);
            gain.gain.linearRampToValueAtTime(0.01, now + (idx + 1) * 0.07);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now + idx * 0.07);
            osc.stop(now + (idx + 1) * 0.07);
        });
    } else if (name === "gameover") {
        [440, 370, 311, 220].forEach((freq, idx) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = "sawtooth";
            osc.frequency.setValueAtTime(freq, now + idx * 0.12);
            gain.gain.setValueAtTime(0.25, now + idx * 0.12);
            gain.gain.linearRampToValueAtTime(0.01, now + (idx + 1) * 0.12);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now + idx * 0.12);
            osc.stop(now + (idx + 1) * 0.12);
        });
    } else {
        beep(440, 50);
    }
}

function beep(freq = 440, durationMs = 100) {
    const ctx = _getAudioContext();
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0.2, now);
    gain.gain.linearRampToValueAtTime(0.01, now + durationMs / 1000);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + durationMs / 1000);
}

// --- Math & Built-in Utilities ---
const pi = Math.PI;
function random(a = 0, b = 1) {
    if (Number.isInteger(a) && Number.isInteger(b)) {
        const min = Math.min(a, b);
        const max = Math.max(a, b);
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }
    return Math.random() * (b - a) + a;
}
const rand = random;
function random_choice(arr) {
    if (!arr || arr.length === 0) return null;
    return arr[Math.floor(Math.random() * arr.length)];
}
function clamp(val, minVal, maxVal) {
    return Math.max(minVal, Math.min(maxVal, val));
}
function sin(deg) { return Math.sin(deg * Math.PI / 180); }
function cos(deg) { return Math.cos(deg * Math.PI / 180); }
function atan2(dy, dx) { return Math.atan2(dy, dx) * 180 / Math.PI; }
function lerp(a, b, t) { return a + (b - a) * t; }
function map_range(v, i1, i2, o1, o2) {
    if (i2 === i1) return o1;
    return o1 + ((v - i1) / (i2 - i1)) * (o2 - o1);
}
function rgb(r, g, b) {
    const toHex = (n) => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, '0');
    return '#' + toHex(r) + toHex(g) + toHex(b);
}
function distance(x1, y1, x2, y2) { return Math.hypot(x2 - x1, y2 - y1); }
function collide_rect(x1, y1, w1, h1, x2, y2, w2, h2) {
    return x1 < x2 + w2 && x1 + w1 > x2 && y1 < y2 + h2 && y1 + h1 > y2;
}
function collide_circle(x1, y1, r1, x2, y2, r2) {
    const dx = x1 - x2, dy = y1 - y2;
    return (dx * dx + dy * dy) <= ((r1 + r2) * (r1 + r2));
}
function collide_point_rect(px, py, rx, ry, rw, rh) {
    return px >= rx && px <= rx + rw && py >= ry && py <= ry + rh;
}
function collide_point_circle(px, py, cx, cy, r) {
    const dx = px - cx, dy = py - cy;
    return (dx * dx + dy * dy) <= (r * r);
}
function len(item) { return item ? item.length : 0; }
const length = len;
function push(arr, item) { arr.push(item); return arr.length; }
const append = push;
function pop(arr, idx = -1) { return idx === -1 ? arr.pop() : arr.splice(idx, 1)[0]; }
function remove(arr, item) {
    const idx = arr.indexOf(item);
    if (idx !== -1) { arr.splice(idx, 1); return true; }
    return false;
}
function contains(coll, item) {
    if (!coll) return false;
    if (Array.isArray(coll) || typeof coll === 'string') return coll.includes(item);
    return item in coll;
}
function keys(obj) { return Object.keys(obj); }
function values(obj) { return Object.values(obj); }
function range(start, end, step = 1) {
    if (end === undefined) { end = start; start = 0; }
    const res = [];
    for (let i = start; i < end; i += step) res.push(i);
    return res;
}
function print(...args) { console.log(...args); }

// Global Game Variables
let width = 800;
let height = 600;
let screen_width = 800;
let screen_height = 600;
let delta = 1 / 60;
let frame = 0;
let mouse_x = 0;
let mouse_y = 0;
let mouse_down_state = false;
let mouse_clicked_state = false;
let _current_fill = '#ffffff';
let _current_stroke = null;
let _current_stroke_width = 1;
let _camera_x = 0;
let _camera_y = 0;
const _keys_held = new Set();
const _keys_pressed = new Set();

function window_setup(title = "CodeLan Game", w = 800, h = 600) {
    document.title = title;
    width = w;
    height = h;
    screen_width = w;
    screen_height = h;
    const canvas = document.getElementById('gameCanvas');
    if (canvas) {
        canvas.width = w;
        canvas.height = h;
    }
}
const window_clan = window_setup;

function fps(target) {} // Managed by requestAnimationFrame

function clear(color = "#181824") {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = color;
    ctx.fillRect(0, 0, width, height);
}

function color(fill = "#ffffff", stroke = null, strokeWidth = 1) {
    _current_fill = fill;
    _current_stroke = stroke;
    _current_stroke_width = strokeWidth;
}
const fill = color;

function rect(x, y, w, h, f = null, stroke = null, strokeWidth = null) {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const fillStyle = f || _current_fill;
    const strokeStyle = stroke || _current_stroke;
    const sw = strokeWidth || _current_stroke_width;

    ctx.save();
    ctx.translate(_camera_x, _camera_y);
    if (fillStyle) {
        ctx.fillStyle = fillStyle;
        ctx.fillRect(x, y, w, h);
    }
    if (strokeStyle) {
        ctx.strokeStyle = strokeStyle;
        ctx.lineWidth = sw;
        ctx.strokeRect(x, y, w, h);
    }
    ctx.restore();
}

function circle(x, y, r, f = null, stroke = null, strokeWidth = null) {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const fillStyle = f || _current_fill;
    const strokeStyle = stroke || _current_stroke;
    const sw = strokeWidth || _current_stroke_width;

    ctx.save();
    ctx.translate(_camera_x, _camera_y);
    ctx.beginPath();
    ctx.arc(x, y, Math.max(0, r), 0, Math.PI * 2);
    if (fillStyle) {
        ctx.fillStyle = fillStyle;
        ctx.fill();
    }
    if (strokeStyle) {
        ctx.strokeStyle = strokeStyle;
        ctx.lineWidth = sw;
        ctx.stroke();
    }
    ctx.restore();
}

function oval(x, y, w, h, f = null, stroke = null, strokeWidth = null) {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const fillStyle = f || _current_fill;
    const strokeStyle = stroke || _current_stroke;
    const sw = strokeWidth || _current_stroke_width;

    ctx.save();
    ctx.translate(_camera_x, _camera_y);
    ctx.beginPath();
    ctx.ellipse(x + w / 2, y + h / 2, Math.abs(w / 2), Math.abs(h / 2), 0, 0, Math.PI * 2);
    if (fillStyle) {
        ctx.fillStyle = fillStyle;
        ctx.fill();
    }
    if (strokeStyle) {
        ctx.strokeStyle = strokeStyle;
        ctx.lineWidth = sw;
        ctx.stroke();
    }
    ctx.restore();
}

function line(x1, y1, x2, y2, c = null, strokeWidth = 1) {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    ctx.save();
    ctx.translate(_camera_x, _camera_y);
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.strokeStyle = c || _current_fill || '#ffffff';
    ctx.lineWidth = strokeWidth;
    ctx.stroke();
    ctx.restore();
}

function triangle(x1, y1, x2, y2, x3, y3, f = null, stroke = null) {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    ctx.save();
    ctx.translate(_camera_x, _camera_y);
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.lineTo(x3, y3);
    ctx.closePath();
    if (f || _current_fill) {
        ctx.fillStyle = f || _current_fill;
        ctx.fill();
    }
    if (stroke || _current_stroke) {
        ctx.strokeStyle = stroke || _current_stroke;
        ctx.stroke();
    }
    ctx.restore();
}

function text(str, x, y, size = 16, c = null, align = "left", font = "Arial") {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    ctx.save();
    ctx.translate(_camera_x, _camera_y);
    ctx.fillStyle = c || _current_fill || '#ffffff';
    ctx.font = `${size >= 18 ? 'bold ' : ''}${size}px ${font}`;
    ctx.textAlign = align;
    ctx.textBaseline = 'middle';
    ctx.fillText(String(str), x, y);
    ctx.restore();
}

function text_centered(str, x, y, size = 16, c = null) {
    text(str, x, y, size, c, "center");
}

function grid(step = 40, col = "#252538") {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    ctx.save();
    ctx.strokeStyle = col;
    ctx.lineWidth = 1;
    for (let x = 0; x < width; x += step) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
    }
    for (let y = 0; y < height; y += step) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
    }
    ctx.restore();
}

function camera(cx = 0, cy = 0) {
    _camera_x = -cx;
    _camera_y = -cy;
}

function key(k) { return _keys_held.has(String(k).toLowerCase()); }
function key_down(k) { return _keys_pressed.has(String(k).toLowerCase()); }
function mouse_down() { return mouse_down_state; }
function mouse_clicked() { return mouse_clicked_state; }
"""

class ASTToJSCompiler:
    def __init__(self):
        self.indent_level = 0
        self.hooks = {}
        self.event_handlers = []

    def indent(self) -> str:
        return "    " * self.indent_level

    def compile(self, program: Program) -> str:
        body_lines = []
        for stmt in program.statements:
            if isinstance(stmt, GameHook):
                self.hooks[stmt.hook_type] = stmt.body
            elif isinstance(stmt, EventHandler):
                self.event_handlers.append(stmt)
            else:
                body_lines.append(self.compile_stmt(stmt))

        setup_code = ""
        if "setup" in self.hooks:
            setup_code = f"function _setup() {{\n{self.compile_block_body(self.hooks['setup'])}\n}}\n"

        update_code = ""
        if "update" in self.hooks:
            update_code = f"function _update() {{\n{self.compile_block_body(self.hooks['update'])}\n}}\n"

        draw_code = ""
        if "draw" in self.hooks:
            draw_code = f"function _draw() {{\n{self.compile_block_body(self.hooks['draw'])}\n}}\n"

        events_code = []
        for eh in self.event_handlers:
            p = eh.param or ""
            events_code.append(f"function _on_{eh.event_type}({p}) {{\n{self.compile_block_body(eh.body)}\n}}")

        top_level = "\n".join(body_lines)
        events_joined = "\n".join(events_code)

        return f"""
// --- User CodeLan Compiled Code ---
{top_level}

{setup_code}
{update_code}
{draw_code}
{events_joined}
"""

    def compile_block_body(self, block: BlockStatement) -> str:
        self.indent_level += 1
        lines = [f"{self.indent()}{self.compile_stmt(s)}" for s in block.statements]
        self.indent_level -= 1
        return "\n".join(lines)

    def compile_stmt(self, node: ASTNode) -> str:
        if isinstance(node, ExpressionStatement):
            return f"{self.compile_expr(node.expression)};"
        elif isinstance(node, VarDeclaration):
            val = self.compile_expr(node.initializer) if node.initializer else "null"
            return f"let {node.name} = {val};"
        elif isinstance(node, BlockStatement):
            return f"{{\n{self.compile_block_body(node)}\n{self.indent()}}}"
        elif isinstance(node, IfStatement):
            cond = self.compile_expr(node.condition)
            then_code = self.compile_stmt(node.then_branch)
            else_code = f" else {self.compile_stmt(node.else_branch)}" if node.else_branch else ""
            return f"if ({cond}) {then_code}{else_code}"
        elif isinstance(node, WhileStatement):
            cond = self.compile_expr(node.condition)
            body = self.compile_stmt(node.body)
            return f"while ({cond}) {body}"
        elif isinstance(node, ForInStatement):
            it = self.compile_expr(node.iterable)
            body = self.compile_stmt(node.body)
            return f"for (let {node.variable} of {it}) {body}"
        elif isinstance(node, ForCStyleStatement):
            init = self.compile_stmt(node.init).rstrip(";") if node.init else ""
            cond = self.compile_expr(node.condition) if node.condition else "true"
            up = self.compile_expr(node.update) if node.update else ""
            body = self.compile_stmt(node.body)
            return f"for ({init}; {cond}; {up}) {body}"
        elif isinstance(node, RepeatStatement):
            cnt = self.compile_expr(node.count)
            body = self.compile_stmt(node.body)
            return f"for (let _rep = 0; _rep < ({cnt}); _rep++) {body}"
        elif isinstance(node, FunctionDeclaration):
            params = ", ".join(node.parameters)
            body = self.compile_block_body(node.body)
            return f"function {node.name}({params}) {{\n{body}\n{self.indent()}}}"
        elif isinstance(node, ReturnStatement):
            val = f" {self.compile_expr(node.value)}" if node.value else ""
            return f"return{val};"
        elif isinstance(node, BreakStatement):
            return "break;"
        elif isinstance(node, ContinueStatement):
            return "continue;"
        return ""

    def compile_expr(self, node: ASTNode) -> str:
        if isinstance(node, NumberLiteral):
            return str(node.value)
        elif isinstance(node, StringLiteral):
            # Check for interpolation
            val = node.value
            if "{" in val and "}" in val:
                # template string
                import re
                escaped = val.replace("`", "\\`")
                template = re.sub(r"\{([a-zA-Z0-9_\.]+)\}", r"${\1}", escaped)
                return f"`{template}`"
            return json.dumps(val)
        elif isinstance(node, BooleanLiteral):
            return "true" if node.value else "false"
        elif isinstance(node, NullLiteral):
            return "null"
        elif isinstance(node, Identifier):
            if node.name == "window":
                return "window_clan"
            return node.name
        elif isinstance(node, ListLiteral):
            elements = ", ".join([self.compile_expr(e) for e in node.elements])
            return f"[{elements}]"
        elif isinstance(node, DictLiteral):
            pairs = ", ".join([f'"{k}": {self.compile_expr(v)}' for k, v in node.pairs])
            return f"{{{pairs}}}"
        elif isinstance(node, MemberAccess):
            obj = self.compile_expr(node.object)
            return f"{obj}.{node.member}"
        elif isinstance(node, IndexAccess):
            obj = self.compile_expr(node.object)
            idx = self.compile_expr(node.index)
            return f"{obj}[{idx}]"
        elif isinstance(node, Assignment):
            target = self.compile_expr(node.target)
            val = self.compile_expr(node.value)
            return f"{target} {node.op} {val}"
        elif isinstance(node, BinaryOp):
            left = self.compile_expr(node.left)
            right = self.compile_expr(node.right)
            op = node.op
            if op in ("and", "&&"): op = "&&"
            elif op in ("or", "||"): op = "||"
            elif op == "==": op = "==="
            elif op == "!=": op = "!=="
            return f"({left} {op} {right})"
        elif isinstance(node, UnaryOp):
            op = "!" if node.op in ("not", "!") else node.op
            return f"{op}({self.compile_expr(node.operand)})"
        elif isinstance(node, FunctionCall):
            callee = self.compile_expr(node.callee)
            args = ", ".join([self.compile_expr(a) for a in node.arguments])
            return f"{callee}({args})"
        return "null"

def export_to_html(program: Program, title: str = "CodeLan Game") -> str:
    compiler = ASTToJSCompiler()
    user_js = compiler.compile(program)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            user-select: none;
        }}
        body {{
            background: #0f0f18;
            color: #eee;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            overflow: hidden;
        }}
        #game-container {{
            position: relative;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.7);
            border-radius: 8px;
            overflow: hidden;
            border: 2px solid #2e2e4a;
        }}
        canvas {{
            display: block;
            background: #181824;
            image-rendering: pixelated;
        }}
        .header {{
            margin-bottom: 12px;
            font-size: 14px;
            color: #8888aa;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}
        .badge {{
            background: #5b21b6;
            color: #fff;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
            margin-left: 6px;
        }}
    </style>
</head>
<body>
    <div class="header">
        🎮 <span>{title}</span> <span class="badge">CodeLan</span>
    </div>
    <div id="game-container">
        <canvas id="gameCanvas" width="800" height="600"></canvas>
    </div>

    <script>
{JS_BUILTINS}

{user_js}

// --- Runner and Event Listeners ---
window.addEventListener('DOMContentLoaded', () => {{
    const canvas = document.getElementById('gameCanvas');

    // Key normalizer
    const mapKey = (k) => {{
        k = k.toLowerCase();
        if (k === 'arrowleft') return 'left';
        if (k === 'arrowright') return 'right';
        if (k === 'arrowup') return 'up';
        if (k === 'arrowdown') return 'down';
        if (k === ' ') return 'space';
        return k;
    }};

    window.addEventListener('keydown', (e) => {{
        _getAudioContext();
        const k = mapKey(e.key);
        if (!_keys_held.has(k)) {{
            _keys_pressed.add(k);
            if (typeof _on_key_down === 'function') _on_key_down(k);
        }}
        _keys_held.add(k);
        if (['space', 'left', 'right', 'up', 'down'].includes(k)) {{
            e.preventDefault();
        }}
    }});

    window.addEventListener('keyup', (e) => {{
        const k = mapKey(e.key);
        _keys_held.delete(k);
        if (typeof _on_key_up === 'function') _on_key_up(k);
    }});

    canvas.addEventListener('mousemove', (e) => {{
        const rect = canvas.getBoundingClientRect();
        mouse_x = e.clientX - rect.left;
        mouse_y = e.clientY - rect.top;
    }});

    canvas.addEventListener('mousedown', (e) => {{
        _getAudioContext();
        const rect = canvas.getBoundingClientRect();
        mouse_x = e.clientX - rect.left;
        mouse_y = e.clientY - rect.top;
        mouse_down_state = true;
        mouse_clicked_state = true;
        if (typeof _on_mouse_down === 'function') _on_mouse_down('left');
    }});

    window.addEventListener('mouseup', (e) => {{
        mouse_down_state = false;
        if (typeof _on_mouse_up === 'function') _on_mouse_up('left');
    }});

    // Initialize setup
    if (typeof _setup === 'function') {{
        _setup();
    }}

    let lastTime = performance.now();
    function gameLoop(now) {{
        delta = Math.min((now - lastTime) / 1000, 0.1);
        lastTime = now;
        frame++;

        if (typeof _update === 'function') {{
            _update();
        }}
        if (typeof _draw === 'function') {{
            _draw();
        }}

        _keys_pressed.clear();
        mouse_clicked_state = false;
        requestAnimationFrame(gameLoop);
    }}

    requestAnimationFrame(gameLoop);
}});
    </script>
</body>
</html>
"""
    return html
