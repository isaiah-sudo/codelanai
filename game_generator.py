"""
AI CodeLan Game Synthesizer & Natural Language Prompt Processor.
Understands user prompts, extracts game mechanics, and generates complete,
valid, playable CodeLan games guided by Reinforcement Learning policy weights.
"""

import re
import random
from typing import Dict, List, Any, Optional, Tuple

from rl_engine import rl_agent, CodeLanRLAgent


class GameIntent:
    """Parsed game specifications from natural language prompt."""
    def __init__(self, raw_prompt: str):
        self.raw_prompt = raw_prompt
        self.genre: str = "custom"
        self.title: str = "CodeLan Game"
        self.theme_bg: str = "#0f172a"
        self.theme_primary: str = "#38bdf8"
        self.theme_accent: str = "#f43f5e"
        self.theme_secondary: str = "#22c55e"
        self.require_sound: bool = True
        self.enable_particles: bool = True
        self.enable_highscore: bool = True
        self.difficulty: str = "normal"
        self.controls: str = "arrows_or_wasd"
        self.custom_mechanics: List[str] = []
        self._parse()

    def _parse(self):
        text = self.raw_prompt.lower()

        # 1. Detect Genre
        if any(w in text for w in ["pong", "table tennis", "paddle ball"]):
            self.genre = "pong"
            self.title = "Neon Pong Arcade"
        elif any(w in text for w in ["snake", "worm", "serpent"]):
            self.genre = "snake"
            self.title = "Cyber Snake"
        elif any(w in text for w in ["space", "shooter", "alien", "invader", "galaxy", "ship", "laser"]):
            self.genre = "space_shooter"
            self.title = "Starfall Defender"
        elif any(w in text for w in ["flappy", "bird", "pipes", "flap", "helicopter"]):
            self.genre = "flappy"
            self.title = "Flappy Velocity"
        elif any(w in text for w in ["breakout", "brick", "breaker", "bricks"]):
            self.genre = "breakout"
            self.title = "Breakout Odyssey"
        elif any(w in text for w in ["asteroid", "dodge", "dodger", "meteor", "falling"]):
            self.genre = "asteroid_dodger"
            self.title = "Meteor Hazard"
        elif any(w in text for w in ["platform", "platformer", "jump", "doodle"]):
            self.genre = "platformer"
            self.title = "Gravity Jumper"
        elif any(w in text for w in ["click", "clicker", "target", "aim", "pop"]):
            self.genre = "clicker"
            self.title = "Target Reflex"
        else:
            self.genre = "custom"
            self.title = "Retro Adventure"

        # 2. Extract Color / Aesthetic Themes
        if any(w in text for w in ["neon", "cyberpunk", "synthwave"]):
            self.theme_bg = "#09090b"
            self.theme_primary = "#00f0ff"
            self.theme_accent = "#ff007f"
            self.theme_secondary = "#ffff00"
        elif any(w in text for w in ["retro", "arcade", "classic", "gameboy", "green"]):
            self.theme_bg = "#081820"
            self.theme_primary = "#88c070"
            self.theme_accent = "#e0f8d0"
            self.theme_secondary = "#346856"
        elif any(w in text for w in ["fire", "magma", "red", "lava"]):
            self.theme_bg = "#1a0b0b"
            self.theme_primary = "#f97316"
            self.theme_accent = "#ef4444"
            self.theme_secondary = "#fbbf24"
        elif any(w in text for w in ["ocean", "aqua", "blue", "water"]):
            self.theme_bg = "#082f49"
            self.theme_primary = "#38bdf8"
            self.theme_accent = "#06b6d4"
            self.theme_secondary = "#67e8f9"

        # 3. Audio & Sound Options
        if any(w in text for w in ["no sound", "silent", "quiet", "mute"]):
            self.require_sound = False
        else:
            self.require_sound = True

        # 4. Particles & Visual Effects
        if any(w in text for w in ["particles", "explosions", "juice", "fancy"]):
            self.enable_particles = True


class CodeLanGameGenerator:
    """
    Synthesizes complete, valid CodeLan games across multiple genres
    and tailored prompts, adapting to RL policy rewards.
    """
    def __init__(self, agent: CodeLanRLAgent = rl_agent):
        self.agent = agent

    def generate_game(self, prompt: str) -> Tuple[str, GameIntent]:
        """Generates CodeLan game code for a given prompt."""
        intent = GameIntent(prompt)

        # Generate game code based on detected genre and intent
        if intent.genre == "pong":
            code = self._generate_pong(intent)
        elif intent.genre == "snake":
            code = self._generate_snake(intent)
        elif intent.genre == "space_shooter":
            code = self._generate_space_shooter(intent)
        elif intent.genre == "flappy":
            code = self._generate_flappy(intent)
        elif intent.genre == "breakout":
            code = self._generate_breakout(intent)
        elif intent.genre == "asteroid_dodger":
            code = self._generate_asteroid_dodger(intent)
        elif intent.genre == "platformer":
            code = self._generate_platformer(intent)
        elif intent.genre == "clicker":
            code = self._generate_clicker(intent)
        else:
            code = self._generate_universal_arcade(intent)

        return code, intent

    # -------------------------------------------------------------
    # 1. PONG GENERATOR
    # -------------------------------------------------------------
    def _generate_pong(self, it: GameIntent) -> str:
        s_hit = 'sound("hit")\n' if it.require_sound else ""
        s_score = 'sound("coin")\n' if it.require_sound else ""

        return f'''// ============================================
// CodeLan Game: {it.title}
// Controls: W/S or Up/Down for Left Paddle
// ============================================

let paddle_w = 16
let paddle_h = 90
let p1_x = 30
let p1_y = 255
let p1_speed = 7
let p1_score = 0

let p2_x = 754
let p2_y = 255
let p2_speed = 5.5
let p2_score = 0

let ball_x = 400
let ball_y = 300
let ball_vx = 6
let ball_vy = 4
let ball_r = 10
let is_paused = false

fn reset_ball() {{
    ball_x = 400
    ball_y = 300
    if (random(0, 1) > 0.5) {{
        ball_vx = 6
    }} else {{
        ball_vx = -6
    }}
    ball_vy = random(-4, 4)
}}

setup {{
    window("{it.title}", 800, 600)
    fps(60)
    reset_ball()
}}

update {{
    if (not is_paused) {{
        // Player 1 controls
        if (key("w") or key("up")) {{
            p1_y -= p1_speed
        }}
        if (key("s") or key("down")) {{
            p1_y += p1_speed
        }}
        p1_y = clamp(p1_y, 10, height - paddle_h - 10)

        // Simple AI for Paddle 2
        if (ball_y < p2_y + paddle_h / 2) {{
            p2_y -= p2_speed
        }}
        if (ball_y > p2_y + paddle_h / 2) {{
            p2_y += p2_speed
        }}
        p2_y = clamp(p2_y, 10, height - paddle_h - 10)

        // Ball movement
        ball_x += ball_vx
        ball_y += ball_vy

        // Wall bounce (top / bottom)
        if (ball_y - ball_r <= 0 or ball_y + ball_r >= height) {{
            ball_vy = -ball_vy
            {s_hit}
        }}

        // Paddle 1 Collision
        if (ball_x - ball_r <= p1_x + paddle_w and ball_y >= p1_y and ball_y <= p1_y + paddle_h) {{
            ball_vx = abs(ball_vx) * 1.05
            ball_vy += (ball_y - (p1_y + paddle_h / 2)) * 0.1
            {s_hit}
        }}

        // Paddle 2 Collision
        if (ball_x + ball_r >= p2_x and ball_y >= p2_y and ball_y <= p2_y + paddle_h) {{
            ball_vx = -abs(ball_vx) * 1.05
            ball_vy += (ball_y - (p2_y + paddle_h / 2)) * 0.1
            {s_hit}
        }}

        // Score handling
        if (ball_x < 0) {{
            p2_score += 1
            {s_score}
            reset_ball()
        }}
        if (ball_x > width) {{
            p1_score += 1
            {s_score}
            reset_ball()
        }}
    }}
}}

draw {{
    clear("{it.theme_bg}")

    // Center divider dashed line
    let cy = 10
    while (cy < height) {{
        rect(398, cy, 4, 15, "#334155")
        cy += 25
    }}

    // Paddles
    rect(p1_x, p1_y, paddle_w, paddle_h, "{it.theme_primary}")
    rect(p2_x, p2_y, paddle_w, paddle_h, "{it.theme_accent}")

    // Ball
    circle(ball_x, ball_y, ball_r, "{it.theme_secondary}")

    // Score Board
    text("Player: {{p1_score}}", 180, 40, 24, "{it.theme_primary}")
    text("CPU: {{p2_score}}", 560, 40, 24, "{it.theme_accent}")
}}
'''

    # -------------------------------------------------------------
    # 2. SPACE SHOOTER GENERATOR
    # -------------------------------------------------------------
    def _generate_space_shooter(self, it: GameIntent) -> str:
        s_laser = 'sound("laser")\n' if it.require_sound else ""
        s_boom = 'sound("explosion")\n' if it.require_sound else ""

        return f'''// ============================================
// CodeLan Game: {it.title}
// Controls: Left/Right or A/D to steer ship, Space to fire
// ============================================

let ship_x = 380
let ship_y = 520
let ship_w = 40
let ship_h = 30
let ship_speed = 7

let bullets = []
let enemies = []
let stars = []
let particles = []

let shoot_timer = 0
let spawn_timer = 0
let score = 0
let lives = 3
let game_over = false

fn reset_game() {{
    ship_x = 380
    ship_y = 520
    bullets = []
    enemies = []
    particles = []
    score = 0
    lives = 3
    game_over = false
}}

setup {{
    window("{it.title}", 800, 600)
    fps(60)

    // Starfield initialization
    repeat (60) {{
        push(stars, {{
            x: random(0, 800),
            y: random(0, 600),
            speed: random(1, 3.5),
            size: random(1, 3)
        }})
    }}
    reset_game()
}}

update {{
    // Scroll background starfield
    for (s in stars) {{
        s.y += s.speed
        if (s.y > height) {{
            s.y = 0
            s.x = random(0, width)
        }}
    }}

    if (not game_over) {{
        // Ship steering
        if (key("left") or key("a")) {{
            ship_x -= ship_speed
        }}
        if (key("right") or key("d")) {{
            ship_x += ship_speed
        }}
        ship_x = clamp(ship_x, 10, width - ship_w - 10)

        // Laser weapon shooting
        if (shoot_timer > 0) {{
            shoot_timer -= 1
        }}
        if (key("space") and shoot_timer <= 0) {{
            push(bullets, {{
                x: ship_x + ship_w / 2 - 3,
                y: ship_y - 5,
                w: 6,
                h: 16,
                speed: 12
            }})
            {s_laser}
            shoot_timer = 12
        }}

        // Update Bullets
        for (b in bullets) {{
            b.y -= b.speed
        }}
        let active_bullets = []
        for (b in bullets) {{
            if (b.y > -20) {{
                push(active_bullets, b)
            }}
        }}
        bullets = active_bullets

        // Spawn Enemies
        spawn_timer += 1
        if (spawn_timer >= 45) {{
            push(enemies, {{
                x: random(40, width - 60),
                y: -30,
                w: 36,
                h: 26,
                speed: random(2.5, 5.0)
            }})
            spawn_timer = 0
        }}

        // Update Enemies & Collisions
        for (e in enemies) {{
            e.y += e.speed

            // Enemy hit player
            if (collide_rect(e.x, e.y, e.w, e.h, ship_x, ship_y, ship_w, ship_h)) {{
                e.y = height + 100
                lives -= 1
                {s_boom}
                if (lives <= 0) {{
                    game_over = true
                }}
            }}

            // Bullet hit enemy
            for (b in bullets) {{
                if (collide_rect(b.x, b.y, b.w, b.h, e.x, e.y, e.w, e.h)) {{
                    b.y = -100
                    e.y = height + 100
                    score += 10
                    {s_boom}
                }}
            }}
        }}

        let active_enemies = []
        for (e in enemies) {{
            if (e.y < height + 50) {{
                push(active_enemies, e)
            }}
        }}
        enemies = active_enemies
    }} else {{
        if (key_down("enter") or key_down("r")) {{
            reset_game()
        }}
    }}
}}

draw {{
    clear("{it.theme_bg}")

    // Draw Stars
    for (s in stars) {{
        circle(s.x, s.y, s.size, "#cbd5e1")
    }}

    // Draw Ship
    triangle(ship_x + ship_w / 2, ship_y, ship_x, ship_y + ship_h, ship_x + ship_w, ship_y + ship_h, "{it.theme_primary}")
    rect(ship_x + ship_w / 2 - 2, ship_y + 6, 4, 12, "{it.theme_accent}")

    // Draw Lasers
    for (b in bullets) {{
        rect(b.x, b.y, b.w, b.h, "{it.theme_secondary}")
    }}

    // Draw Alien Enemies
    for (e in enemies) {{
        rect(e.x, e.y, e.w, e.h, "{it.theme_accent}")
        circle(e.x + e.w / 2, e.y + e.h / 2, 6, "#ffffff")
    }}

    // HUD Display
    text("Score: {{score}}", 20, 20, 20, "{it.theme_primary}")
    text("Lives: {{lives}}", width - 120, 20, 20, "{it.theme_accent}")

    if (game_over) {{
        text_centered("GAME OVER", width / 2, height / 2 - 20, 48, "{it.theme_accent}")
        text_centered("Press [ENTER] to Restart", width / 2, height / 2 + 30, 22, "#f8fafc")
    }}
}}
'''

    # -------------------------------------------------------------
    # 3. SNAKE GENERATOR
    # -------------------------------------------------------------
    def _generate_snake(self, it: GameIntent) -> str:
        s_eat = 'sound("coin")\n' if it.require_sound else ""
        s_die = 'sound("gameover")\n' if it.require_sound else ""

        return f'''// ============================================
// CodeLan Game: {it.title}
// Controls: Arrow keys to steer snake
// ============================================

let grid_size = 20
let cols = 40
let rows = 30

let snake = []
let dir_x = 1
let dir_y = 0
let next_dir_x = 1
let next_dir_y = 0

let food_x = 15
let food_y = 10
let score = 0
let move_timer = 0
let move_interval = 6
let game_over = false

fn spawn_food() {{
    food_x = floor(random(2, cols - 3))
    food_y = floor(random(2, rows - 3))
}}

fn reset_game() {{
    snake = [
        {{x: 10, y: 15}},
        {{x: 9, y: 15}},
        {{x: 8, y: 15}}
    ]
    dir_x = 1
    dir_y = 0
    next_dir_x = 1
    next_dir_y = 0
    score = 0
    game_over = false
    spawn_food()
}}

setup {{
    window("{it.title}", 800, 600)
    fps(60)
    reset_game()
}}

update {{
    // Direction inputs
    if ((key("up") or key("w")) and dir_y == 0) {{
        next_dir_x = 0
        next_dir_y = -1
    }}
    if ((key("down") or key("s")) and dir_y == 0) {{
        next_dir_x = 0
        next_dir_y = 1
    }}
    if ((key("left") or key("a")) and dir_x == 0) {{
        next_dir_x = -1
        next_dir_y = 0
    }}
    if ((key("right") or key("d")) and dir_x == 0) {{
        next_dir_x = 1
        next_dir_y = 0
    }}

    if (not game_over) {{
        move_timer += 1
        if (move_timer >= move_interval) {{
            move_timer = 0
            dir_x = next_dir_x
            dir_y = next_dir_y

            // Calculate new head
            let head = snake[0]
            let new_x = head.x + dir_x
            let new_y = head.y + dir_y

            // Wall collision
            if (new_x < 0 or new_x >= cols or new_y < 0 or new_y >= rows) {{
                game_over = true
                {s_die}
            }}

            // Self collision
            for (segment in snake) {{
                if (segment.x == new_x and segment.y == new_y) {{
                    game_over = true
                    {s_die}
                }}
            }}

            if (not game_over) {{
                let new_snake = [{{x: new_x, y: new_y}}]
                for (s in snake) {{
                    push(new_snake, s)
                }}

                // Check food eaten
                if (new_x == food_x and new_y == food_y) {{
                    score += 10
                    {s_eat}
                    spawn_food()
                }} else {{
                    pop(new_snake)
                }}
                snake = new_snake
            }}
        }}
    }} else {{
        if (key_down("enter") or key_down("r")) {{
            reset_game()
        }}
    }}
}}

draw {{
    clear("{it.theme_bg}")

    // Draw Food
    circle(food_x * grid_size + grid_size / 2, food_y * grid_size + grid_size / 2, grid_size / 2 - 2, "{it.theme_accent}")

    // Draw Snake Segments
    let is_head = true
    for (s in snake) {{
        let c = "{it.theme_secondary}"
        if (is_head) {{
            c = "{it.theme_primary}"
        }}
        rect(s.x * grid_size + 1, s.y * grid_size + 1, grid_size - 2, grid_size - 2, c)
        is_head = false
    }}

    // Score HUD
    text("Score: {{score}}", 20, 20, 20, "{it.theme_primary}")

    if (game_over) {{
        text_centered("SNAKE CRASHED!", width / 2, height / 2 - 20, 44, "{it.theme_accent}")
        text_centered("Press [ENTER] to Play Again", width / 2, height / 2 + 25, 20, "#f8fafc")
    }}
}}
'''

    # -------------------------------------------------------------
    # 4. FLAPPY BIRD GENERATOR
    # -------------------------------------------------------------
    def _generate_flappy(self, it: GameIntent) -> str:
        s_flap = 'sound("jump")\n' if it.require_sound else ""
        s_score = 'sound("coin")\n' if it.require_sound else ""
        s_hit = 'sound("hit")\n' if it.require_sound else ""

        return f'''// ============================================
// CodeLan Game: {it.title}
// Controls: Space or Click to Flap Wings
// ============================================

let bird_x = 160
let bird_y = 280
let bird_vy = 0
let bird_r = 16
let gravity = 0.5
let jump_power = -8.5

let pipes = []
let spawn_timer = 0
let score = 0
let high_score = 0
let game_over = false

fn reset_game() {{
    bird_y = 280
    bird_vy = 0
    pipes = []
    score = 0
    game_over = false
}}

setup {{
    window("{it.title}", 800, 600)
    fps(60)
    reset_game()
}}

update {{
    if (not game_over) {{
        // Flap physics
        if (key_down("space") or key_down("up") or mouse_clicked()) {{
            bird_vy = jump_power
            {s_flap}
        }}

        bird_vy += gravity
        bird_y += bird_vy

        // Spawn Pipes
        spawn_timer += 1
        if (spawn_timer >= 95) {{
            let gap = 160
            let top_h = random(70, height - gap - 90)
            push(pipes, {{
                x: width + 20,
                top_h: top_h,
                bottom_y: top_h + gap,
                w: 65,
                speed: 3.5,
                passed: false
            }})
            spawn_timer = 0
        }}

        // Update Pipes
        for (p in pipes) {{
            p.x -= p.speed

            // Score gate
            if (not p.passed and p.x + p.w < bird_x) {{
                p.passed = true
                score += 1
                if (score > high_score) {{
                    high_score = score
                }}
                {s_score}
            }}

            // Collision with Pipes
            if (bird_x + bird_r > p.x and bird_x - bird_r < p.x + p.w) {{
                if (bird_y - bird_r < p.top_h or bird_y + bird_r > p.bottom_y) {{
                    game_over = true
                    {s_hit}
                }}
            }}
        }}

        // Clean off-screen pipes
        let active_pipes = []
        for (p in pipes) {{
            if (p.x + p.w > -30) {{
                push(active_pipes, p)
            }}
        }}
        pipes = active_pipes

        // Boundary hit
        if (bird_y - bird_r <= 0 or bird_y + bird_r >= height) {{
            game_over = true
            {s_hit}
        }}
    }} else {{
        if (key_down("enter") or key_down("space") or mouse_clicked()) {{
            reset_game()
        }}
    }}
}}

draw {{
    clear("{it.theme_bg}")

    // Draw Pipes
    for (p in pipes) {{
        // Top pipe
        rect(p.x, 0, p.w, p.top_h, "{it.theme_secondary}")
        rect(p.x - 4, p.top_h - 20, p.w + 8, 20, "{it.theme_secondary}")

        // Bottom pipe
        let bot_h = height - p.bottom_y
        rect(p.x, p.bottom_y, p.w, bot_h, "{it.theme_secondary}")
        rect(p.x - 4, p.bottom_y, p.w + 8, 20, "{it.theme_secondary}")
    }}

    // Draw Bird
    circle(bird_x, bird_y, bird_r, "{it.theme_primary}")
    circle(bird_x + 6, bird_y - 4, 4, "#ffffff")
    triangle(bird_x + 8, bird_y, bird_x + 22, bird_y + 4, bird_x + 8, bird_y + 8, "{it.theme_accent}")

    // Score
    text("Score: {{score}}", 25, 25, 22, "#ffffff")
    text("High: {{high_score}}", 25, 55, 18, "{it.theme_primary}")

    if (game_over) {{
        text_centered("YOU CRASHED!", width / 2, height / 2 - 25, 46, "{it.theme_accent}")
        text_centered("Press [SPACE] or Click to Flap Again", width / 2, height / 2 + 25, 20, "#f8fafc")
    }}
}}
'''

    # -------------------------------------------------------------
    # 5. BREAKOUT GENERATOR
    # -------------------------------------------------------------
    def _generate_breakout(self, it: GameIntent) -> str:
        s_hit = 'sound("hit")\n' if it.require_sound else ""
        s_brick = 'sound("laser")\n' if it.require_sound else ""
        s_win = 'sound("powerup")\n' if it.require_sound else ""

        return f'''// ============================================
// CodeLan Game: {it.title}
// Controls: Left/Right or Mouse to move paddle
// ============================================

let paddle_w = 110
let paddle_h = 16
let paddle_x = 345
let paddle_y = 550
let paddle_speed = 8

let ball_x = 400
let ball_y = 450
let ball_vx = 5
let ball_vy = -5
let ball_r = 8

let bricks = []
let score = 0
let lives = 3
let game_over = false
let game_won = false

fn init_bricks() {{
    bricks = []
    let rows = 5
    let cols = 10
    let b_w = 68
    let b_h = 22
    let pad_x = 10
    let pad_y = 8
    let colors = ["#f43f5e", "#fb923c", "#facc15", "#4ade80", "#38bdf8"]

    let r = 0
    while (r < rows) {{
        let c = 0
        while (c < cols) {{
            push(bricks, {{
                x: 35 + c * (b_w + pad_x),
                y: 60 + r * (b_h + pad_y),
                w: b_w,
                h: b_h,
                color: colors[r],
                alive: true
            }})
            c += 1
        }}
        r += 1
    }}
}}

fn reset_ball() {{
    ball_x = paddle_x + paddle_w / 2
    ball_y = paddle_y - 20
    if (random(0, 1) > 0.5) {{
        ball_vx = 5
    }} else {{
        ball_vx = -5
    }}
    ball_vy = -5
}}

setup {{
    window("{it.title}", 800, 600)
    fps(60)
    init_bricks()
    reset_ball()
}}

update {{
    if (not game_over and not game_won) {{
        // Paddle movement
        if (key("left") or key("a")) {{
            paddle_x -= paddle_speed
        }}
        if (key("right") or key("d")) {{
            paddle_x += paddle_speed
        }}
        paddle_x = clamp(paddle_x, 10, width - paddle_w - 10)

        // Ball movement
        ball_x += ball_vx
        ball_y += ball_vy

        // Wall collisions
        if (ball_x - ball_r <= 0 or ball_x + ball_r >= width) {{
            ball_vx = -ball_vx
            {s_hit}
        }}
        if (ball_y - ball_r <= 0) {{
            ball_vy = -ball_vy
            {s_hit}
        }}

        // Paddle collision
        if (collide_rect(ball_x - ball_r, ball_y - ball_r, ball_r * 2, ball_r * 2, paddle_x, paddle_y, paddle_w, paddle_h)) {{
            ball_vy = -abs(ball_vy)
            let offset = (ball_x - (paddle_x + paddle_w / 2)) / (paddle_w / 2)
            ball_vx = offset * 7
            {s_hit}
        }}

        // Brick collisions
        let remaining_bricks = 0
        for (b in bricks) {{
            if (b.alive) {{
                remaining_bricks += 1
                if (collide_rect(ball_x - ball_r, ball_y - ball_r, ball_r * 2, ball_r * 2, b.x, b.y, b.w, b.h)) {{
                    b.alive = false
                    ball_vy = -ball_vy
                    score += 20
                    {s_brick}
                }}
            }}
        }}

        if (remaining_bricks == 0) {{
            game_won = true
            {s_win}
        }}

        // Ball fell off screen
        if (ball_y > height) {{
            lives -= 1
            if (lives <= 0) {{
                game_over = true
            }} else {{
                reset_ball()
            }}
        }}
    }} else {{
        if (key_down("enter") or key_down("r")) {{
            score = 0
            lives = 3
            game_over = false
            game_won = false
            init_bricks()
            reset_ball()
        }}
    }}
}}

draw {{
    clear("{it.theme_bg}")

    // Draw Bricks
    for (b in bricks) {{
        if (b.alive) {{
            rect(b.x, b.y, b.w, b.h, b.color)
        }}
    }}

    // Draw Paddle & Ball
    rect(paddle_x, paddle_y, paddle_w, paddle_h, "{it.theme_primary}")
    circle(ball_x, ball_y, ball_r, "#ffffff")

    // HUD
    text("Score: {{score}}", 20, 20, 18, "#ffffff")
    text("Lives: {{lives}}", width - 110, 20, 18, "{it.theme_accent}")

    if (game_over) {{
        text_centered("GAME OVER", width / 2, height / 2, 46, "{it.theme_accent}")
        text_centered("Press [ENTER] to Retry", width / 2, height / 2 + 40, 20, "#f8fafc")
    }}
    if (game_won) {{
        text_centered("STAGE CLEARED!", width / 2, height / 2, 46, "{it.theme_secondary}")
        text_centered("Press [ENTER] to Play Again", width / 2, height / 2 + 40, 20, "#f8fafc")
    }}
}}
'''

    # -------------------------------------------------------------
    # 6. ASTEROID DODGER GENERATOR
    # -------------------------------------------------------------
    def _generate_asteroid_dodger(self, it: GameIntent) -> str:
        s_hit = 'sound("hit")\n' if it.require_sound else ""
        s_coin = 'sound("coin")\n' if it.require_sound else ""

        return f'''// ============================================
// CodeLan Game: {it.title}
// Controls: Arrow keys or WASD to dodge falling meteors
// ============================================

let px = 400
let py = 500
let p_radius = 18
let p_speed = 6.5

let meteors = []
let gems = []
let score = 0
let survived_time = 0
let game_over = false

fn reset_game() {{
    px = 400
    py = 500
    meteors = []
    gems = []
    score = 0
    survived_time = 0
    game_over = false
}}

setup {{
    window("{it.title}", 800, 600)
    fps(60)
    reset_game()
}}

update {{
    if (not game_over) {{
        survived_time += delta
        score = floor(survived_time * 10)

        // 8-directional movement
        if (key("left") or key("a")) {{ px -= p_speed }}
        if (key("right") or key("d")) {{ px += p_speed }}
        if (key("up") or key("w")) {{ py -= p_speed }}
        if (key("down") or key("s")) {{ py += p_speed }}

        px = clamp(px, p_radius, width - p_radius)
        py = clamp(py, p_radius, height - p_radius)

        // Spawn falling meteors
        if (random(0, 100) < 6) {{
            push(meteors, {{
                x: random(20, width - 20),
                y: -30,
                r: random(14, 28),
                speed: random(4.0, 8.5)
            }})
        }}

        // Spawn collectible gems
        if (random(0, 100) < 2) {{
            push(gems, {{
                x: random(40, width - 40),
                y: -20,
                r: 10,
                speed: 3
            }})
        }}

        // Update meteors
        for (m in meteors) {{
            m.y += m.speed
            if (collide_circle(px, py, p_radius, m.x, m.y, m.r)) {{
                game_over = true
                {s_hit}
            }}
        }}

        // Update gems
        for (g in gems) {{
            g.y += g.speed
            if (collide_circle(px, py, p_radius, g.x, g.y, g.r)) {{
                g.y = height + 100
                score += 50
                {s_coin}
            }}
        }}

        // Filter offscreen items
        let active_meteors = []
        for (m in meteors) {{
            if (m.y < height + 40) {{ push(active_meteors, m) }}
        }}
        meteors = active_meteors
    }} else {{
        if (key_down("enter") or key_down("space")) {{
            reset_game()
        }}
    }}
}}

draw {{
    clear("{it.theme_bg}")

    // Draw Gems
    for (g in gems) {{
        circle(g.x, g.y, g.r, "{it.theme_secondary}")
    }}

    // Draw Meteors
    for (m in meteors) {{
        circle(m.x, m.y, m.r, "{it.theme_accent}")
    }}

    // Draw Player Ship
    circle(px, py, p_radius, "{it.theme_primary}")
    circle(px, py, 6, "#ffffff")

    // HUD
    text("Survival Score: {{score}}", 20, 20, 20, "{it.theme_primary}")

    if (game_over) {{
        text_centered("OBLITERATED!", width / 2, height / 2 - 20, 48, "{it.theme_accent}")
        text_centered("Press [ENTER] to Try Again", width / 2, height / 2 + 30, 22, "#ffffff")
    }}
}}
'''

    # -------------------------------------------------------------
    # 7. PLATFORMER / JUMPER GENERATOR
    # -------------------------------------------------------------
    def _generate_platformer(self, it: GameIntent) -> str:
        s_jump = 'sound("jump")\n' if it.require_sound else ""

        return f'''// ============================================
// CodeLan Game: {it.title}
// Controls: Left/Right to Steer, Bounce upwards
// ============================================

let px = 400
let py = 450
let p_vy = 0
let p_w = 26
let p_h = 32
let gravity = 0.45
let bounce_impulse = -13

let platforms = []
let score = 0
let game_over = false

fn reset_game() {{
    px = 400
    py = 400
    p_vy = 0
    score = 0
    game_over = false
    platforms = [
        {{x: 350, y: 550, w: 100, h: 14}},
        {{x: 200, y: 440, w: 90, h: 14}},
        {{x: 500, y: 340, w: 90, h: 14}},
        {{x: 250, y: 220, w: 90, h: 14}},
        {{x: 450, y: 110, w: 90, h: 14}}
    ]
}}

setup {{
    window("{it.title}", 800, 600)
    fps(60)
    reset_game()
}}

update {{
    if (not game_over) {{
        if (key("left") or key("a")) {{ px -= 6 }}
        if (key("right") or key("d")) {{ px += 6 }}

        // Screen wrap
        if (px < -p_w) {{ px = width }}
        if (px > width) {{ px = -p_w }}

        // Gravity
        p_vy += gravity
        py += p_vy

        // Bounce on platforms when falling down
        if (p_vy > 0) {{
            for (plat in platforms) {{
                if (collide_rect(px, py + p_h - 6, p_w, 8, plat.x, plat.y, plat.w, plat.h)) {{
                    p_vy = bounce_impulse
                    {s_jump}
                }}
            }}
        }}

        // Camera scroll up when player rises
        if (py < 250) {{
            let diff = 250 - py
            py = 250
            score += floor(diff)
            for (plat in platforms) {{
                plat.y += diff
                if (plat.y > height) {{
                    plat.y = 0
                    plat.x = random(50, width - 150)
                }}
            }}
        }}

        // Fell off screen
        if (py > height + 50) {{
            game_over = true
        }}
    }} else {{
        if (key_down("enter") or key_down("r")) {{
            reset_game()
        }}
    }}
}}

draw {{
    clear("{it.theme_bg}")

    // Platforms
    for (plat in platforms) {{
        rect(plat.x, plat.y, plat.w, plat.h, "{it.theme_secondary}")
    }}

    // Player
    rect(px, py, p_w, p_h, "{it.theme_primary}")

    // Score
    text("Altitude: {{score}} ft", 25, 25, 20, "#ffffff")

    if (game_over) {{
        text_centered("FELL INTO THE ABYSS!", width / 2, height / 2 - 20, 44, "{it.theme_accent}")
        text_centered("Press [ENTER] to Re-climb", width / 2, height / 2 + 25, 20, "#f8fafc")
    }}
}}
'''

    # -------------------------------------------------------------
    # 8. CLICKER / AIM TRAINER GENERATOR
    # -------------------------------------------------------------
    def _generate_clicker(self, it: GameIntent) -> str:
        s_pop = 'sound("coin")\n' if it.require_sound else ""

        return f'''// ============================================
// CodeLan Game: {it.title}
// Controls: Click on targets before time expires!
// ============================================

let targets = []
let score = 0
let time_left = 30.0
let spawn_timer = 0
let game_over = false

fn spawn_target() {{
    let target_color = "{it.theme_primary}"
    if (random(0, 1) > 0.5) {{
        target_color = "{it.theme_accent}"
    }}
    push(targets, {{
        x: random(60, width - 60),
        y: random(60, height - 60),
        r: random(20, 35),
        timer: 75,
        color: target_color
    }})
}}

fn reset_game() {{
    targets = []
    score = 0
    time_left = 30.0
    game_over = false
    spawn_target()
    spawn_target()
}}

setup {{
    window("{it.title}", 800, 600)
    fps(60)
    reset_game()
}}

update {{
    if (not game_over) {{
        time_left -= delta
        if (time_left <= 0) {{
            time_left = 0
            game_over = true
        }}

        spawn_timer += 1
        if (spawn_timer >= 40) {{
            spawn_target()
            spawn_timer = 0
        }}

        // Mouse click detection
        if (mouse_clicked()) {{
            for (t in targets) {{
                if (collide_point_circle(mouse_x, mouse_y, t.x, t.y, t.r)) {{
                    t.timer = -10
                    score += 100
                    {s_pop}
                }}
            }}
        }}

        // Target decay
        let active = []
        for (t in targets) {{
            t.timer -= 1
            if (t.timer > 0) {{
                push(active, t)
            }}
        }}
        targets = active
    }} else {{
        if (key_down("enter") or key_down("r")) {{
            reset_game()
        }}
    }}
}}

draw {{
    clear("{it.theme_bg}")

    // Draw Targets
    for (t in targets) {{
        circle(t.x, t.y, t.r, t.color)
        circle(t.x, t.y, t.r / 2, "#ffffff")
    }}

    // Cursor crosshair
    line(mouse_x - 12, mouse_y, mouse_x + 12, mouse_y, "{it.theme_secondary}")
    line(mouse_x, mouse_y - 12, mouse_x, mouse_y + 12, "{it.theme_secondary}")

    // HUD
    text("Score: {{score}}", 20, 20, 20, "{it.theme_primary}")
    text("Time: {{floor(time_left)}}s", width - 120, 20, 20, "{it.theme_accent}")

    if (game_over) {{
        text_centered("TIME EXPIRED!", width / 2, height / 2 - 20, 48, "{it.theme_accent}")
        text_centered("Press [ENTER] to Play Again", width / 2, height / 2 + 30, 22, "#ffffff")
    }}
}}
'''

    # -------------------------------------------------------------
    # 9. UNIVERSAL ARCADE GENERATOR
    # -------------------------------------------------------------
    def _generate_universal_arcade(self, it: GameIntent) -> str:
        s_coin = 'sound("coin")\n' if it.require_sound else ""
        s_hit = 'sound("hit")\n' if it.require_sound else ""

        return f'''// ============================================
// CodeLan Game: {it.title}
// Controls: Arrow keys to steer, gather energy orbs
// ============================================

let px = 400
let py = 300
let p_radius = 20
let p_speed = 6

let orbs = []
let hazards = []
let score = 0
let lives = 3
let game_over = false

fn reset_game() {{
    px = 400
    py = 300
    orbs = []
    hazards = []
    score = 0
    lives = 3
    game_over = false

    repeat (6) {{
        push(orbs, {{
            x: random(50, width - 50),
            y: random(50, height - 50),
            r: 12
        }})
    }}
}}

setup {{
    window("{it.title}", 800, 600)
    fps(60)
    reset_game()
}}

update {{
    if (not game_over) {{
        if (key("left") or key("a")) {{ px -= p_speed }}
        if (key("right") or key("d")) {{ px += p_speed }}
        if (key("up") or key("w")) {{ py -= p_speed }}
        if (key("down") or key("s")) {{ py += p_speed }}

        px = clamp(px, p_radius, width - p_radius)
        py = clamp(py, p_radius, height - p_radius)

        // Spawn hazards
        if (random(0, 100) < 4) {{
            push(hazards, {{
                x: random(0, width),
                y: -20,
                w: 24,
                h: 24,
                speed: random(3, 7)
            }})
        }}

        // Collect orbs
        for (o in orbs) {{
            if (collide_circle(px, py, p_radius, o.x, o.y, o.r)) {{
                o.x = random(50, width - 50)
                o.y = random(50, height - 50)
                score += 25
                {s_coin}
            }}
        }}

        // Hazards collision
        for (h in hazards) {{
            h.y += h.speed
            if (collide_rect(px - p_radius, py - p_radius, p_radius * 2, p_radius * 2, h.x, h.y, h.w, h.h)) {{
                h.y = height + 100
                lives -= 1
                {s_hit}
                if (lives <= 0) {{
                    game_over = true
                }}
            }}
        }}

        let active_hazards = []
        for (h in hazards) {{
            if (h.y < height + 40) {{ push(active_hazards, h) }}
        }}
        hazards = active_hazards
    }} else {{
        if (key_down("enter") or key_down("r")) {{
            reset_game()
        }}
    }}
}}

draw {{
    clear("{it.theme_bg}")

    // Orbs
    for (o in orbs) {{
        circle(o.x, o.y, o.r, "{it.theme_secondary}")
    }}

    // Hazards
    for (h in hazards) {{
        rect(h.x, h.y, h.w, h.h, "{it.theme_accent}")
    }}

    // Player
    circle(px, py, p_radius, "{it.theme_primary}")
    circle(px, py, 6, "#ffffff")

    // HUD
    text("Score: {{score}}", 20, 20, 20, "{it.theme_primary}")
    text("Lives: {{lives}}", width - 120, 20, 20, "{it.theme_accent}")

    if (game_over) {{
        text_centered("ENERGY DEPLETED!", width / 2, height / 2 - 20, 48, "{it.theme_accent}")
        text_centered("Press [ENTER] to Restart", width / 2, height / 2 + 25, 20, "#f8fafc")
    }}
}}
'''


# Global Game Generator singleton
game_generator = CodeLanGameGenerator()
