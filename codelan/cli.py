"""
Command-Line Interface for CodeLan.
"""

import os
import sys
import argparse
import webbrowser
import http.server
import socketserver
import threading
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from .lexer import Lexer, LexerError
from .parser import Parser, ParserError
from .interpreter import Interpreter, CodeLanRuntimeError
from .runtime import DesktopGameRunner
from .web_exporter import export_to_html

DEMOS = {
    "pong": "pong.clan",
    "snake": "snake.clan",
    "space": "space_shooter.clan",
    "flappy": "flappy.clan",
    "breakout": "breakout.clan",
}

def get_examples_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "examples"

def parse_file(filepath: str):
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)

    code = path.read_text(encoding="utf-8")
    lexer = Lexer(code)
    try:
        tokens = lexer.tokenize()
        parser = Parser(tokens, filename=str(path))
        program = parser.parse()
        return program
    except LexerError as le:
        print(f"\n❌ {le}")
        sys.exit(1)
    except ParserError as pe:
        print(f"\n❌ {pe}")
        sys.exit(1)

def cmd_run(args):
    program = parse_file(args.file)
    interpreter = Interpreter()
    try:
        interpreter.run_program(program)
        runner = DesktopGameRunner(interpreter)
        runner.run()
    except CodeLanRuntimeError as re:
        print(f"\n❌ {re}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nGame stopped.")

def cmd_web(args):
    path = Path(args.file)
    program = parse_file(args.file)
    title = path.stem.replace("_", " ").title()
    html_content = export_to_html(program, title=title)

    out_file = path.with_suffix(".html")
    out_file.write_text(html_content, encoding="utf-8")
    print(f"✨ Compiled to HTML: {out_file}")

    # Launch local HTTP server and open browser
    port = args.port or 8080
    handler = http.server.SimpleHTTPRequestHandler
    os.chdir(out_file.parent)

    print(f"[SERVER] Starting local web server at http://localhost:{port}/{out_file.name}")

    def start_server():
        with socketserver.TCPServer(("", port), handler) as httpd:
            try:
                httpd.serve_forever()
            except Exception:
                pass

    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    webbrowser.open(f"http://localhost:{port}/{out_file.name}")
    print("Press Ctrl+C to stop the server.")
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("\nWeb server stopped.")

def cmd_export(args):
    path = Path(args.file)
    program = parse_file(args.file)
    title = path.stem.replace("_", " ").title()
    html_content = export_to_html(program, title=title)

    out_path = Path(args.output) if args.output else path.with_suffix(".html")
    out_path.write_text(html_content, encoding="utf-8")
    print(f"[EXPORT] Standalone game created at: {out_path.resolve()}")
    print("You can double-click this file to play in any browser or upload it to itch.io/GitHub!")

def cmd_check(args):
    path = Path(args.file)
    print(f"Checking syntax of '{path}'...")
    parse_file(args.file)
    print(f"[OK] Syntax check passed! No errors detected in {path.name}.")

def cmd_demo(args):
    name = args.name.lower()
    examples_dir = get_examples_dir()

    if name not in DEMOS:
        print(f"Unknown demo '{name}'. Available demos: {', '.join(DEMOS.keys())}")
        return

    demo_file = examples_dir / DEMOS[name]
    if not demo_file.exists():
        print(f"Demo file '{demo_file}' not found.")
        return

    print(f"[GAME] Launching {name.upper()} demo...")
    args.file = str(demo_file)
    cmd_run(args)

def cmd_list_demos(args):
    print("\n[CodeLan] Available Built-in Game Demos:")
    print("=" * 45)
    for key, filename in DEMOS.items():
        print(f"  * {key.ljust(10)} - {filename}")
    print("\nRun any demo with: python codelan.py demo <name>  (or codelan demo <name>)")
    print("Example: codelan demo pong\n")

def cmd_repl(args):
    print("CodeLan Interactive REPL")
    print("Type 'exit' or press Ctrl+C to quit.\n")
    interpreter = Interpreter()

    while True:
        try:
            line = input("clan> ").strip()
            if not line:
                continue
            if line in ("exit", "quit"):
                break
            lexer = Lexer(line)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            prog = parser.parse()
            for stmt in prog.statements:
                result = interpreter.execute(stmt, interpreter.global_env)
                if result is not None:
                    print(result)
        except (LexerError, ParserError, CodeLanRuntimeError) as e:
            print(f"❌ {e}")
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

def main():
    parser = argparse.ArgumentParser(
        prog="codelan",
        description="CodeLan: A Simple & Fun Game Programming Language",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # run
    p_run = subparsers.add_parser("run", help="Run a CodeLan game in desktop window")
    p_run.add_argument("file", help="Path to .clan source file")

    # web
    p_web = subparsers.add_parser("web", help="Run a CodeLan game in web browser")
    p_web.add_argument("file", help="Path to .clan source file")
    p_web.add_argument("--port", type=int, default=8080, help="Port for web server (default 8080)")

    # export
    p_export = subparsers.add_parser("export", help="Export CodeLan game to standalone HTML file")
    p_export.add_argument("file", help="Path to .clan source file")
    p_export.add_argument("output", nargs="?", default=None, help="Output HTML file path (optional)")

    # check
    p_check = subparsers.add_parser("check", help="Syntax check a CodeLan file")
    p_check.add_argument("file", help="Path to .clan source file")

    # demo
    p_demo = subparsers.add_parser("demo", help="Play a built-in game demo")
    p_demo.add_argument("name", choices=list(DEMOS.keys()), help="Name of demo: pong, snake, space, flappy, breakout")

    # list-demos
    subparsers.add_parser("list-demos", help="List all built-in game demos")

    # repl
    subparsers.add_parser("repl", help="Start interactive REPL session")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    commands = {
        "run": cmd_run,
        "web": cmd_web,
        "export": cmd_export,
        "check": cmd_check,
        "demo": cmd_demo,
        "list-demos": cmd_list_demos,
        "repl": cmd_repl,
    }

    cmd_fn = commands.get(args.command)
    if cmd_fn:
        cmd_fn(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
