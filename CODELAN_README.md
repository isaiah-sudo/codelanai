# 🎮 CodeLan

**CodeLan** is a clean, simple, and expressive programming language designed specifically to make 2D game development fast, easy, and fun.

- ⚡ **Zero Setup & Instant Play**: Runs desktop games at 60 FPS natively with zero external dependencies (pure Python standard library).
- 🌐 **Export to Web**: Turn any `.clan` game into a standalone, single-file HTML5 canvas game with one command.
- 🔊 **Built-in Retro Audio**: Built-in 8-bit sound synthesizer for lasers, jumps, explosions, coins, and hits.
- 🎯 **Beginner Friendly**: Clear, readable syntax with forgiving formatting, optional semicolons, string interpolation, and built-in collision detection.

---

## 🚀 Quick Start

### 1. Run a Built-In Game Demo
CodeLan comes with 5 complete, ready-to-play arcade games:

```bash
# Play classic Pong
python codelan.py demo pong

# Play Snake
python codelan.py demo snake

# Play Space Defender
python codelan.py demo space

# Play Flappy Bird
python codelan.py demo flappy

# Play Breakout (Brick Breaker)
python codelan.py demo breakout
```
*(On Windows you can also use `codelan demo <name>`)*

### 2. Run Your Own Game
```bash
python codelan.py run mygame.clan
```

### 3. Export to Web (Play in Browser)
```bash
# Exports to mygame.html - share it with friends or upload to itch.io!
python codelan.py export mygame.clan
```

### 4. Live Browser Play
```bash
python codelan.py web mygame.clan
```

---

## 🛠️ CLI Commands & Arguments

The `codelan` CLI provides the following commands:

| Command | Arguments | Description | Example |
| :--- | :--- | :--- | :--- |
| `run` | `<file.clan>` | Runs the game in a native 60 FPS desktop window. | `python codelan.py run game.clan` |
| `web` | `<file.clan> [--port PORT]` | Exports the game to HTML, starts a local server, and opens it in your default web browser. | `python codelan.py web game.clan --port 3000` |
| `export` | `<file.clan> [output.html]` | Transpiles the CodeLan game into a standalone, portable HTML5 file. | `python codelan.py export game.clan dist/index.html` |
| `check` | `<file.clan>` | Performs syntax and token checks, reporting any line and column errors. | `python codelan.py check game.clan` |
| `demo` | `<name>` | Plays a built-in game demo (`pong`, `snake`, `space`, `flappy`, `breakout`). | `python codelan.py demo space` |
| `list-demos`| *(none)* | Lists all available built-in demos. | `python codelan.py list-demos` |
| `repl` | *(none)* | Launches an interactive read-eval-print loop for quick testing. | `python codelan.py repl` |

---

## 🕹️ Your First Game in 20 Lines

Create a file named `bounce.clan`:

```javascript
let x = 200
let y = 150
let vx = 4
let vy = 3
let radius = 20

setup {
    window("Bouncing Ball", 600, 400)
    fps(60)
}

update {
    x += vx
    y += vy

    // Bounce off walls with sound
    if (x - radius <= 0 or x + radius >= width) {
        vx = -vx
        sound("laser")
    }
    if (y - radius <= 0 or y + radius >= height) {
        vy = -vy
        sound("hit")
    }
}

draw {
    clear("#0f172a")
    circle(x, y, radius, "#38bdf8")
    text("Bouncing Ball Demo", 20, 20, 16, "#94a3b8")
}
```

Run it:
```bash
python codelan.py run bounce.clan
```

---

## 📖 Language Architecture

A CodeLan game is structured around three core lifecycle blocks:

```javascript
setup {
    // Runs ONCE when the game launches.
    // Use this to configure window title, size, and initialize state.
}

update {
    // Runs EVERY FRAME (e.g., 60 times/sec).
    // Use this for user input, physics, and gameplay logic.
}

draw {
    // Runs EVERY FRAME right after update.
    // Use this to render shapes, text, sprites, and animations.
}
```

### Event Handlers
You can also define discrete event handlers:
```javascript
on key_down(key) {
    if (key == "space") {
        shoot()
    }
}

on mouse_down(button) {
    spawn_particle(mouse_x, mouse_y)
}
```

---

## 📚 Complete Language Syntax Reference

### 1. Variables & Data Types
```javascript
let player_name = "Nova"     // String
let score = 100               // Number (integer or float)
let is_active = true          // Boolean (true, false)
let target = null             // Null (null or nil)

// Lists (Arrays)
let inventory = ["sword", "shield", "potion"]
push(inventory, "bow")

// Dictionaries (Objects)
let player = {
    x: 100,
    y: 200,
    speed: 5
}
player.x += player.speed
```

### 2. String Interpolation
Strings support inline `{expression}` interpolation:
```javascript
text("Score: {score} | Player: {player_name}", 20, 20, 16)
```

### 3. Operators
- **Arithmetic**: `+`, `-`, `*`, `/`, `%`
- **Assignment**: `=`, `+=`, `-=`, `*=`, `/=`
- **Comparison**: `==`, `!=`, `<`, `<=`, `>`, `>=`
- **Logic**: `and`, `or`, `not` (also supports `&&`, `||`, `!`)

### 4. Control Flow
#### If / Else
```javascript
if (score > 100) {
    level = 2
} else if (score > 50) {
    level = 1
} else {
    level = 0
}
```

#### While Loop
```javascript
while (enemy_count < 5) {
    spawn_enemy()
    enemy_count += 1
}
```

#### For-In Loop
```javascript
for (bullet in bullets) {
    bullet.y -= bullet.speed
}
```

#### Repeat Loop
```javascript
repeat (10) {
    spawn_star()
}
```

### 5. Functions
```javascript
fn make_bullet(start_x, start_y) {
    return {
        x: start_x,
        y: start_y,
        vy: -10
    }
}

let b = make_bullet(100, 200)
```

---

## 🎨 Complete Built-in Commands & Arguments Reference

### 🖥️ Window & Global State
| Command / Variable | Arguments | Description |
| :--- | :--- | :--- |
| `window(title, width, height)` | `title` *(str)*, `width` *(int)*, `height` *(int)* | Sets the game window title and canvas dimensions (default 800x600). |
| `fps(rate)` | `rate` *(int)* | Sets target frames per second (default 60). |
| `width` / `screen_width` | *(read-only)* | Current screen width in pixels. |
| `height` / `screen_height` | *(read-only)* | Current screen height in pixels. |
| `delta` | *(read-only)* | Time elapsed since last frame in seconds (delta time). |
| `frame` | *(read-only)* | Total frame counter. |
| `time()` | *(none)* | Total elapsed game time in seconds. |

---

### 🖌️ Graphics & Drawing
All drawing functions should be called inside the `draw { ... }` block:

| Command | Arguments | Description |
| :--- | :--- | :--- |
| `clear(color)` | `color` *(optional str)* | Clears canvas with background color (e.g. `"#181824"`, `"black"`). |
| `color(fill, stroke, stroke_width)` | `fill` *(str)*, `stroke` *(optional)*, `stroke_width` *(optional)* | Sets default fill and outline color for subsequent shapes. |
| `rect(x, y, w, h, fill, stroke, stroke_width)` | `x, y, w, h` *(num)*, `fill, stroke, stroke_width` *(optional)* | Draws a rectangle at `(x, y)` with width `w` and height `h`. |
| `circle(x, y, radius, fill, stroke, stroke_width)` | `x, y, radius` *(num)*, `fill, stroke, stroke_width` *(optional)* | Draws a circle centered at `(x, y)`. |
| `oval(x, y, w, h, fill, stroke, stroke_width)` | `x, y, w, h` *(num)*, `fill, stroke, stroke_width` *(optional)* | Draws an ellipse inside bounding box `(x, y, w, h)`. |
| `line(x1, y1, x2, y2, color, stroke_width)` | `x1, y1, x2, y2` *(num)*, `color` *(optional)*, `stroke_width` *(optional)* | Draws a line segment from `(x1, y1)` to `(x2, y2)`. |
| `triangle(x1, y1, x2, y2, x3, y3, fill, stroke)` | `x1, y1, x2, y2, x3, y3` *(num)*, `fill, stroke` *(optional)* | Draws a triangle connecting the three points. |
| `text(string, x, y, size, color, align, font)` | `string` *(any)*, `x, y` *(num)*, `size` *(optional int)*, `color` *(optional str)*, `align` *(optional: "left", "center", "right")*, `font` *(optional str)* | Renders text at `(x, y)`. |
| `text_centered(string, x, y, size, color)` | `string` *(any)*, `x, y` *(num)*, `size` *(optional)*, `color` *(optional)* | Convenience shorthand to render centered text. |
| `grid(step, color)` | `step` *(optional int)*, `color` *(optional str)* | Draws a background grid helper with cell size `step`. |
| `camera(cx, cy)` | `cx, cy` *(num)* | Offsets the rendering camera for scrolling or screen shakes. |

---

### 🕹️ Input Handling
| Command / Variable | Arguments | Description |
| :--- | :--- | :--- |
| `key(name)` | `name` *(str)* | Returns `true` if key is currently held down (e.g. `"left"`, `"right"`, `"up"`, `"down"`, `"space"`, `"w"`, `"a"`, `"s"`, `"d"`, `"enter"`, `"escape"`). |
| `key_down(name)` | `name` *(str)* | Returns `true` **only on the frame** the key was initially pressed. |
| `mouse_x` | *(read-only)* | Current mouse X position inside the canvas. |
| `mouse_y` | *(read-only)* | Current mouse Y position inside the canvas. |
| `mouse_down()` | *(none)* | Returns `true` while the left mouse button is held. |
| `mouse_clicked()` | *(none)* | Returns `true` **only on the frame** the mouse was clicked. |

---

### 🔊 Retro Audio Synthesizer
CodeLan includes a built-in sound engine requiring no external sound files:

| Command | Arguments | Description |
| :--- | :--- | :--- |
| `sound(name)` | `name` *(str)* | Plays an asynchronous 8-bit procedural sound effect: `"laser"`, `"jump"`, `"coin"`, `"hit"`, `"explosion"`, `"powerup"`, `"gameover"`, or `"click"`. |
| `beep(freq, duration_ms)` | `freq` *(int)*, `duration_ms` *(int)* | Emits a retro frequency tone in Hz for duration in milliseconds (e.g., `beep(440, 100)`). |

---

### 💥 Physics & Collision Detection
| Command | Arguments | Description |
| :--- | :--- | :--- |
| `collide_rect(x1, y1, w1, h1, x2, y2, w2, h2)` | `8 numbers` | Returns `true` if two axis-aligned rectangles overlap. |
| `collide_circle(x1, y1, r1, x2, y2, r2)` | `6 numbers` | Returns `true` if two circles intersect. |
| `collide_point_rect(px, py, rx, ry, rw, rh)` | `6 numbers` | Returns `true` if point `(px, py)` is inside rectangle `(rx, ry, rw, rh)`. |
| `collide_point_circle(px, py, cx, cy, r)` | `5 numbers` | Returns `true` if point `(px, py)` is inside circle `(cx, cy, r)`. |
| `distance(x1, y1, x2, y2)` | `4 numbers` | Returns the Euclidean distance between two points. |

---

### 📐 Math & Utilities
| Command | Arguments | Description |
| :--- | :--- | :--- |
| `random(min, max)` / `rand(min, max)` | `min, max` *(num)* | Returns a random float or int between `min` and `max`. |
| `random_choice(list)` | `list` *(list)* | Returns a randomly chosen element from `list`. |
| `clamp(val, min, max)` | `val, min, max` *(num)* | Restricts `val` between `min` and `max`. |
| `min(a, b, ...)` | `numbers` | Returns the smallest value. |
| `max(a, b, ...)` | `numbers` | Returns the largest value. |
| `abs(x)` | `x` *(num)* | Absolute value. |
| `floor(x)`, `ceil(x)`, `round(x)` | `x` *(num)* | Rounding utilities. |
| `sin(deg)` | `deg` *(num in degrees)* | Sine of angle in degrees. |
| `cos(deg)` | `deg` *(num in degrees)* | Cosine of angle in degrees. |
| `atan2(dy, dx)` | `dy, dx` *(num)* | Returns angle in degrees (-180 to 180). |
| `lerp(a, b, t)` | `a, b, t` *(num)* | Linear interpolation between `a` and `b` by factor `t` (0.0 to 1.0). |
| `map_range(val, in1, in2, out1, out2)` | `5 numbers` | Re-maps a number from range `[in1, in2]` to `[out1, out2]`. |
| `rgb(r, g, b)` | `r, g, b` *(0-255)* | Converts RGB values to hex color string (e.g. `rgb(255, 0, 128)` -> `"#ff0080"`). |
| `pi` | *(constant)* | Mathematical constant $\pi \approx 3.1415926$. |

---

### 📦 Collections & Conversion
| Command | Arguments | Description |
| :--- | :--- | :--- |
| `len(collection)` / `length(...)` | `list / string` | Returns the number of items or characters. |
| `push(list, item)` / `append(...)` | `list, item` | Appends `item` to end of `list`. |
| `pop(list, [index])` | `list, index` *(optional)* | Removes and returns the item at index (default last). |
| `remove(list, item)` | `list, item` | Removes first occurrence of `item` from `list`. |
| `contains(collection, item)` | `collection, item` | Returns `true` if `item` exists in list, string, or dictionary. |
| `keys(dict)` | `dict` | Returns a list of dictionary keys. |
| `values(dict)` | `dict` | Returns a list of dictionary values. |
| `range(start, end, [step])` | `start, end, step` | Returns a list of integers from `start` to `end`. |
| `str(x)`, `int(x)`, `float(x)`, `bool(x)` | `value` | Type conversion functions. |
| `print(...)` | `any` | Prints values to standard console output. |

---

## 🎮 Included Example Games

Check the `examples/` directory for full source code:

1. **`examples/pong.clan`**:
   - 2-player or vs AI paddle game with accelerating ball volleys and score tracking.
2. **`examples/snake.clan`**:
   - Classic retro snake with grid movement, apple pickups, high score, and body growth.
3. **`examples/space_shooter.clan`**:
   - Spaceship combat with parallax scrolling starfield, laser shooting, falling alien craft, and explosive particle effects.
4. **`examples/flappy.clan`**:
   - Flappy bird physics with gravity, flap impulses, moving pipe obstacles, and score gates.
5. **`examples/breakout.clan`**:
   - Brick breaker with multi-colored destructible brick grid, paddle deflection physics, and combo sounds.

---

## 🧪 Testing

Run the automated test suite:
```bash
python -m unittest discover tests
```

---

## 📄 License
MIT License. Free to use, modify, and build games with!
