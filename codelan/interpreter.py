"""
Interpreter and runtime evaluation for CodeLan.
"""

import math
import random
import time
from typing import Any, Dict, List, Optional, Callable
from .ast_nodes import (
    ASTNode, NumberLiteral, StringLiteral, BooleanLiteral, NullLiteral,
    Identifier, ListLiteral, DictLiteral, BinaryOp, UnaryOp, Assignment,
    FunctionCall, MemberAccess, IndexAccess, ExpressionStatement,
    VarDeclaration, BlockStatement, IfStatement, WhileStatement,
    ForInStatement, ForCStyleStatement, RepeatStatement, FunctionDeclaration,
    ReturnStatement, BreakStatement, ContinueStatement, GameHook,
    EventHandler, Program
)
from .environment import Environment
from .sound import play_sound, play_beep

class ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value

class BreakSignal(Exception):
    pass

class ContinueSignal(Exception):
    pass

class CodeLanRuntimeError(Exception):
    def __init__(self, message: str, node: Optional[ASTNode] = None):
        loc = f" at line {node.line}:{node.column}" if node and getattr(node, 'line', 0) else ""
        super().__init__(f"Runtime Error{loc}: {message}")
        self.node = node

class CodeLanFunction:
    def __init__(self, name: str, params: List[str], body: BlockStatement, closure: Environment):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure

    def call(self, interpreter: 'Interpreter', args: List[Any]) -> Any:
        env = Environment(parent=self.closure)
        for i, param in enumerate(self.params):
            val = args[i] if i < len(args) else None
            env.define(param, val)
        try:
            interpreter.execute_block(self.body.statements, env)
        except ReturnSignal as ret:
            return ret.value
        return None

class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        self.hooks: Dict[str, BlockStatement] = {}
        self.event_handlers: List[EventHandler] = []
        self.draw_commands: List[Dict[str, Any]] = []

        # Game Window and state configurations
        self.window_title = "CodeLan Game"
        self.window_width = 800
        self.window_height = 600
        self.target_fps = 60
        self.bg_color = "#181824"
        self.current_fill = "#ffffff"
        self.current_stroke = None
        self.current_stroke_width = 1
        self.camera_x = 0
        self.camera_y = 0

        # Input state
        self.keys_held = set()
        self.keys_pressed = set()
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_down = False
        self.mouse_clicked = False

        # Timing
        self.start_time = time.time()
        self.frame_count = 0
        self.delta_time = 1.0 / 60.0

        self.setup_builtins()

    def setup_builtins(self):
        # Window & Config
        def _window(title="CodeLan Game", width=800, height=600):
            self.window_title = str(title)
            self.window_width = int(width)
            self.window_height = int(height)
            self.global_env.define("width", self.window_width)
            self.global_env.define("height", self.window_height)
            self.global_env.define("screen_width", self.window_width)
            self.global_env.define("screen_height", self.window_height)
            return None

        def _fps(val=60):
            self.target_fps = max(1, min(240, int(val)))
            return None

        # Graphics built-ins
        def _clear(color=None):
            c = color if color is not None else self.bg_color
            self.draw_commands.append({"type": "clear", "color": c})
            return None

        def _color(fill="#ffffff", stroke=None, stroke_width=1):
            self.current_fill = fill
            self.current_stroke = stroke
            self.current_stroke_width = stroke_width
            return None

        def _rect(x, y, w, h, fill=None, outline=None, stroke_width=None):
            f = fill if fill is not None else self.current_fill
            o = outline if outline is not None else self.current_stroke
            sw = stroke_width if stroke_width is not None else self.current_stroke_width
            self.draw_commands.append({
                "type": "rect",
                "x": x + self.camera_x,
                "y": y + self.camera_y,
                "w": w,
                "h": h,
                "fill": f,
                "outline": o,
                "width": sw
            })
            return None

        def _circle(x, y, radius, fill=None, outline=None, stroke_width=None):
            f = fill if fill is not None else self.current_fill
            o = outline if outline is not None else self.current_stroke
            sw = stroke_width if stroke_width is not None else self.current_stroke_width
            self.draw_commands.append({
                "type": "circle",
                "x": x + self.camera_x,
                "y": y + self.camera_y,
                "r": radius,
                "fill": f,
                "outline": o,
                "width": sw
            })
            return None

        def _oval(x, y, w, h, fill=None, outline=None, stroke_width=None):
            f = fill if fill is not None else self.current_fill
            o = outline if outline is not None else self.current_stroke
            sw = stroke_width if stroke_width is not None else self.current_stroke_width
            self.draw_commands.append({
                "type": "oval",
                "x": x + self.camera_x,
                "y": y + self.camera_y,
                "w": w,
                "h": h,
                "fill": f,
                "outline": o,
                "width": sw
            })
            return None

        def _line(x1, y1, x2, y2, color=None, width=1):
            c = color if color is not None else self.current_fill
            self.draw_commands.append({
                "type": "line",
                "x1": x1 + self.camera_x,
                "y1": y1 + self.camera_y,
                "x2": x2 + self.camera_x,
                "y2": y2 + self.camera_y,
                "color": c,
                "width": width
            })
            return None

        def _triangle(x1, y1, x2, y2, x3, y3, fill=None, outline=None):
            f = fill if fill is not None else self.current_fill
            o = outline if outline is not None else self.current_stroke
            self.draw_commands.append({
                "type": "triangle",
                "x1": x1 + self.camera_x,
                "y1": y1 + self.camera_y,
                "x2": x2 + self.camera_x,
                "y2": y2 + self.camera_y,
                "x3": x3 + self.camera_x,
                "y3": y3 + self.camera_y,
                "fill": f,
                "outline": o
            })
            return None

        def _text(string, x, y, size=16, color=None, align="left", font="Arial"):
            c = color if color is not None else self.current_fill
            self.draw_commands.append({
                "type": "text",
                "text": str(string),
                "x": x + self.camera_x,
                "y": y + self.camera_y,
                "size": int(size),
                "color": c,
                "align": align,
                "font": font
            })
            return None

        def _text_centered(string, x, y, size=16, color=None):
            return _text(string, x, y, size, color, align="center")

        def _grid(step=40, color="#2a2a3c"):
            self.draw_commands.append({
                "type": "grid",
                "step": int(step),
                "color": color
            })
            return None

        def _camera(cx=0, cy=0):
            self.camera_x = -float(cx)
            self.camera_y = -float(cy)
            return None

        # Input helpers
        def _key(name):
            k = str(name).lower()
            return k in self.keys_held

        def _key_down(name):
            k = str(name).lower()
            return k in self.keys_pressed

        def _mouse_down_fn(btn="left"):
            return self.mouse_down

        def _mouse_clicked_fn(btn="left"):
            return self.mouse_clicked

        # Sound & Audio
        def _sound(name):
            play_sound(str(name))
            return None

        def _beep(freq=440, duration_ms=100):
            play_beep(int(freq), int(duration_ms))
            return None

        # Collisions
        def _collide_rect(x1, y1, w1, h1, x2, y2, w2, h2):
            return (
                x1 < x2 + w2 and
                x1 + w1 > x2 and
                y1 < y2 + h2 and
                y1 + h1 > y2
            )

        def _collide_circle(x1, y1, r1, x2, y2, r2):
            dx = x1 - x2
            dy = y1 - y2
            return (dx * dx + dy * dy) <= ((r1 + r2) * (r1 + r2))

        def _collide_point_rect(px, py, rx, ry, rw, rh):
            return rx <= px <= rx + rw and ry <= py <= ry + rh

        def _collide_point_circle(px, py, cx, cy, r):
            dx = px - cx
            dy = py - cy
            return (dx * dx + dy * dy) <= (r * r)

        def _distance(x1, y1, x2, y2):
            return math.hypot(x2 - x1, y2 - y1)

        # Math helpers
        def _random(a=0, b=1):
            if isinstance(a, int) and isinstance(b, int):
                return random.randint(min(a, b), max(a, b))
            return random.uniform(float(a), float(b))

        def _random_choice(seq):
            if not seq:
                return None
            return random.choice(seq)

        def _clamp(val, low, high):
            return max(low, min(high, val))

        def _sin_deg(deg):
            return math.sin(math.radians(deg))

        def _cos_deg(deg):
            return math.cos(math.radians(deg))

        def _atan2_deg(dy, dx):
            return math.degrees(math.atan2(dy, dx))

        def _lerp(a, b, t):
            return a + (b - a) * t

        def _map_range(val, in_min, in_max, out_min, out_max):
            if in_max == in_min:
                return out_min
            return out_min + ((val - in_min) / (in_max - in_min)) * (out_max - out_min)

        def _rgb(r, g, b):
            return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

        # Collections & Built-ins
        def _push(lst, item):
            if isinstance(lst, list):
                lst.append(item)
                return len(lst)
            raise CodeLanRuntimeError("First argument to push must be a list")

        def _pop(lst, index=-1):
            if isinstance(lst, list):
                return lst.pop(index)
            raise CodeLanRuntimeError("First argument to pop must be a list")

        def _remove(lst, item):
            if isinstance(lst, list):
                if item in lst:
                    lst.remove(item)
                    return True
                return False
            raise CodeLanRuntimeError("First argument to remove must be a list")

        def _contains(collection, item):
            if isinstance(collection, (list, str, dict)):
                return item in collection
            return False

        def _keys(d):
            if isinstance(d, dict):
                return list(d.keys())
            return []

        def _values(d):
            if isinstance(d, dict):
                return list(d.values())
            return []

        def _range_fn(*args):
            return list(range(*args))

        # Register built-ins in global environment
        builtins = {
            # Window & config
            "window": _window,
            "fps": _fps,
            "width": self.window_width,
            "height": self.window_height,
            "screen_width": self.window_width,
            "screen_height": self.window_height,
            # Graphics
            "clear": _clear,
            "color": _color,
            "fill": _color,
            "rect": _rect,
            "circle": _circle,
            "oval": _oval,
            "line": _line,
            "triangle": _triangle,
            "text": _text,
            "text_centered": _text_centered,
            "grid": _grid,
            "camera": _camera,
            # Input
            "key": _key,
            "key_down": _key_down,
            "mouse_down": _mouse_down_fn,
            "mouse_clicked": _mouse_clicked_fn,
            "mouse_x": 0,
            "mouse_y": 0,
            # Audio
            "sound": _sound,
            "beep": _beep,
            # Collisions & Physics
            "collide_rect": _collide_rect,
            "collide_circle": _collide_circle,
            "collide_point_rect": _collide_point_rect,
            "collide_point_circle": _collide_point_circle,
            "distance": _distance,
            # Math
            "random": _random,
            "rand": _random,
            "random_choice": _random_choice,
            "clamp": _clamp,
            "min": min,
            "max": max,
            "abs": abs,
            "floor": math.floor,
            "ceil": math.ceil,
            "round": round,
            "sin": _sin_deg,
            "cos": _cos_deg,
            "atan2": _atan2_deg,
            "lerp": _lerp,
            "map_range": _map_range,
            "rgb": _rgb,
            "pi": math.pi,
            # Collections & Conversions
            "len": len,
            "length": len,
            "push": _push,
            "append": _push,
            "pop": _pop,
            "remove": _remove,
            "contains": _contains,
            "keys": _keys,
            "values": _values,
            "range": _range_fn,
            "str": str,
            "int": lambda x: int(float(x)),
            "float": float,
            "bool": bool,
            "time": lambda: time.time() - self.start_time,
            "delta": 1.0 / 60.0,
            "frame": 0,
            "print": print,
        }

        for name, fn in builtins.items():
            self.global_env.define(name, fn)

    def update_globals_before_frame(self):
        """Updates frame-dependent globals (mouse, delta, frame, dimensions)."""
        self.global_env.assign("mouse_x", self.mouse_x)
        self.global_env.assign("mouse_y", self.mouse_y)
        self.global_env.assign("delta", self.delta_time)
        self.global_env.assign("frame", self.frame_count)
        self.global_env.assign("width", self.window_width)
        self.global_env.assign("height", self.window_height)

    def run_program(self, program: Program):
        for stmt in program.statements:
            if isinstance(stmt, GameHook):
                self.hooks[stmt.hook_type] = stmt.body
            elif isinstance(stmt, EventHandler):
                self.event_handlers.append(stmt)
            else:
                self.execute(stmt, self.global_env)

    def execute_setup(self):
        if "setup" in self.hooks:
            self.execute_block(self.hooks["setup"].statements, self.global_env)

    def execute_update(self):
        self.update_globals_before_frame()
        if "update" in self.hooks:
            self.execute_block(self.hooks["update"].statements, self.global_env)

    def execute_draw(self) -> List[Dict[str, Any]]:
        self.draw_commands.clear()
        self.update_globals_before_frame()
        if "draw" in self.hooks:
            self.execute_block(self.hooks["draw"].statements, self.global_env)
        return self.draw_commands

    def handle_event(self, event_name: str, arg: Any = None):
        for handler in self.event_handlers:
            if handler.event_type.lower() == event_name.lower():
                env = Environment(parent=self.global_env)
                if handler.param is not None:
                    env.define(handler.param, arg)
                self.execute_block(handler.body.statements, env)

    def execute_block(self, statements: List[ASTNode], env: Environment):
        for stmt in statements:
            self.execute(stmt, env)

    def execute(self, node: ASTNode, env: Environment) -> Any:
        if isinstance(node, ExpressionStatement):
            return self.evaluate(node.expression, env)

        elif isinstance(node, VarDeclaration):
            val = self.evaluate(node.initializer, env) if node.initializer is not None else None
            env.define(node.name, val)
            return val

        elif isinstance(node, BlockStatement):
            block_env = Environment(parent=env)
            return self.execute_block(node.statements, block_env)

        elif isinstance(node, IfStatement):
            cond = self.evaluate(node.condition, env)
            if self.is_truthy(cond):
                return self.execute(node.then_branch, env)
            elif node.else_branch is not None:
                return self.execute(node.else_branch, env)
            return None

        elif isinstance(node, WhileStatement):
            while self.is_truthy(self.evaluate(node.condition, env)):
                try:
                    self.execute(node.body, env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return None

        elif isinstance(node, ForInStatement):
            iterable = self.evaluate(node.iterable, env)
            if not hasattr(iterable, '__iter__'):
                raise CodeLanRuntimeError(f"Target of for-in is not iterable: {repr(iterable)}", node)
            for item in iterable:
                loop_env = Environment(parent=env)
                loop_env.define(node.variable, item)
                try:
                    self.execute(node.body, loop_env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return None

        elif isinstance(node, ForCStyleStatement):
            loop_env = Environment(parent=env)
            if node.init:
                self.execute(node.init, loop_env)
            while True:
                if node.condition:
                    cond = self.evaluate(node.condition, loop_env)
                    if not self.is_truthy(cond):
                        break
                try:
                    self.execute(node.body, loop_env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    pass
                if node.update:
                    self.evaluate(node.update, loop_env)
            return None

        elif isinstance(node, RepeatStatement):
            count = int(self.evaluate(node.count, env))
            for _ in range(count):
                try:
                    self.execute(node.body, env)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return None

        elif isinstance(node, FunctionDeclaration):
            fn = CodeLanFunction(node.name, node.parameters, node.body, env)
            env.define(node.name, fn)
            return fn

        elif isinstance(node, ReturnStatement):
            val = self.evaluate(node.value, env) if node.value is not None else None
            raise ReturnSignal(val)

        elif isinstance(node, BreakStatement):
            raise BreakSignal()

        elif isinstance(node, ContinueStatement):
            raise ContinueSignal()

        elif isinstance(node, GameHook):
            self.hooks[node.hook_type] = node.body
            return None

        elif isinstance(node, EventHandler):
            self.event_handlers.append(node)
            return None

        else:
            raise CodeLanRuntimeError(f"Unknown statement node: {type(node).__name__}", node)

    def evaluate(self, node: ASTNode, env: Environment) -> Any:
        if isinstance(node, NumberLiteral):
            return node.value

        elif isinstance(node, StringLiteral):
            return self.interpolate_string(node.value, env)

        elif isinstance(node, BooleanLiteral):
            return node.value

        elif isinstance(node, NullLiteral):
            return None

        elif isinstance(node, Identifier):
            try:
                return env.get(node.name)
            except NameError:
                raise CodeLanRuntimeError(f"Undefined variable '{node.name}'", node)

        elif isinstance(node, ListLiteral):
            return [self.evaluate(elem, env) for elem in node.elements]

        elif isinstance(node, DictLiteral):
            d = {}
            for k, v in node.pairs:
                d[k] = self.evaluate(v, env)
            return d

        elif isinstance(node, MemberAccess):
            obj = self.evaluate(node.object, env)
            if isinstance(obj, dict):
                return obj.get(node.member, None)
            if hasattr(obj, node.member):
                return getattr(obj, node.member)
            return None

        elif isinstance(node, IndexAccess):
            obj = self.evaluate(node.object, env)
            idx = self.evaluate(node.index, env)
            try:
                if isinstance(obj, (list, str)):
                    return obj[int(idx)]
                if isinstance(obj, dict):
                    return obj.get(idx, None)
            except IndexError:
                return None
            raise CodeLanRuntimeError(f"Cannot index into {type(obj).__name__}", node)

        elif isinstance(node, Assignment):
            val = self.evaluate(node.value, env)

            if isinstance(node.target, Identifier):
                name = node.target.name
                if node.op == "=":
                    env.assign(name, val)
                else:
                    curr = env.get(name)
                    new_val = self.apply_compound_op(node.op, curr, val, node)
                    env.assign(name, new_val)
                    val = new_val
                return val

            elif isinstance(node.target, MemberAccess):
                obj = self.evaluate(node.target.object, env)
                if isinstance(obj, dict):
                    prop = node.target.member
                    if node.op == "=":
                        obj[prop] = val
                    else:
                        curr = obj.get(prop, 0)
                        val = self.apply_compound_op(node.op, curr, val, node)
                        obj[prop] = val
                    return val
                raise CodeLanRuntimeError("Cannot set property on non-dictionary", node)

            elif isinstance(node.target, IndexAccess):
                obj = self.evaluate(node.target.object, env)
                idx = self.evaluate(node.target.index, env)
                if isinstance(obj, list):
                    i = int(idx)
                    if node.op == "=":
                        obj[i] = val
                    else:
                        val = self.apply_compound_op(node.op, obj[i], val, node)
                        obj[i] = val
                    return val
                elif isinstance(obj, dict):
                    if node.op == "=":
                        obj[idx] = val
                    else:
                        val = self.apply_compound_op(node.op, obj.get(idx, 0), val, node)
                        obj[idx] = val
                    return val
                raise CodeLanRuntimeError("Cannot index assign to target", node)

            raise CodeLanRuntimeError(f"Invalid assignment target {type(node.target).__name__}", node)

        elif isinstance(node, BinaryOp):
            left = self.evaluate(node.left, env)
            op = node.op

            # Short-circuit logical operators
            if op in ("and", "&&"):
                return left if not self.is_truthy(left) else self.evaluate(node.right, env)
            if op in ("or", "||"):
                return left if self.is_truthy(left) else self.evaluate(node.right, env)

            right = self.evaluate(node.right, env)

            try:
                if op == "+":
                    if isinstance(left, str) or isinstance(right, str):
                        return str(left) + str(right)
                    if isinstance(left, list) and isinstance(right, list):
                        return left + right
                    return left + right
                elif op == "-":
                    return left - right
                elif op == "*":
                    if isinstance(left, str) and isinstance(right, int):
                        return left * right
                    return left * right
                elif op == "/":
                    if right == 0:
                        raise CodeLanRuntimeError("Division by zero", node)
                    return left / right
                elif op == "%":
                    return left % right
                elif op == "==":
                    return left == right
                elif op == "!=":
                    return left != right
                elif op == "<":
                    return left < right
                elif op == "<=":
                    return left <= right
                elif op == ">":
                    return left > right
                elif op == ">=":
                    return left >= right
            except TypeError as te:
                raise CodeLanRuntimeError(f"Type error in '{op}': {te}", node)

            raise CodeLanRuntimeError(f"Unknown operator: {op}", node)

        elif isinstance(node, UnaryOp):
            operand = self.evaluate(node.operand, env)
            if node.op == "-":
                return -operand
            elif node.op in ("not", "!"):
                return not self.is_truthy(operand)
            raise CodeLanRuntimeError(f"Unknown unary operator: {node.op}", node)

        elif isinstance(node, FunctionCall):
            callee = self.evaluate(node.callee, env)
            args = [self.evaluate(arg, env) for arg in node.arguments]

            if isinstance(callee, CodeLanFunction):
                return callee.call(self, args)
            elif callable(callee):
                try:
                    return callee(*args)
                except TypeError as te:
                    raise CodeLanRuntimeError(f"Function call error: {te}", node)
            else:
                raise CodeLanRuntimeError(f"'{callee}' is not callable", node)

        raise CodeLanRuntimeError(f"Unknown expression node: {type(node).__name__}", node)

    def apply_compound_op(self, op: str, curr: Any, val: Any, node: ASTNode) -> Any:
        if op == "+=":
            if isinstance(curr, str) or isinstance(val, str):
                return str(curr) + str(val)
            return curr + val
        elif op == "-=":
            return curr - val
        elif op == "*=":
            return curr * val
        elif op == "/=":
            if val == 0:
                raise CodeLanRuntimeError("Division by zero", node)
            return curr / val
        raise CodeLanRuntimeError(f"Unknown assignment operator {op}", node)

    def is_truthy(self, val: Any) -> bool:
        if val is None or val is False or val == 0 or val == "":
            return False
        return True

    def interpolate_string(self, text: str, env: Environment) -> str:
        """Supports embedded {variable} inside strings like 'Score: {score}'."""
        if "{" not in text:
            return text
        result = []
        i = 0
        n = len(text)
        while i < n:
            if text[i] == "{" and (i == 0 or text[i - 1] != "\\"):
                j = text.find("}", i + 1)
                if j != -1:
                    var_expr = text[i + 1:j].strip()
                    try:
                        # Simple identifier or property lookup
                        if "." in var_expr:
                            parts = var_expr.split(".")
                            obj = env.get(parts[0])
                            for p in parts[1:]:
                                if isinstance(obj, dict):
                                    obj = obj.get(p)
                                else:
                                    obj = getattr(obj, p, None)
                            result.append(str(obj))
                        else:
                            val = env.get(var_expr)
                            result.append(str(val))
                    except Exception:
                        result.append("{" + var_expr + "}")
                    i = j + 1
                    continue
            result.append(text[i])
            i += 1
        return "".join(result)
