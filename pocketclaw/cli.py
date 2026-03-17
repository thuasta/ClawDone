"""CLI entrypoints."""

from __future__ import annotations

import argparse
import json
import os

from .local_tmux import TmuxClient
from .web import create_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PocketClaw: control tmux-hosted coding agents from your phone")
    parser.add_argument("--tmux-bin", default=os.getenv("POCKETCLAW_TMUX_BIN", "tmux"), help="local tmux binary path")

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    serve_parser = subparsers.add_parser("serve", help="start the PocketClaw mobile web UI")
    serve_parser.add_argument("--host", default=os.getenv("POCKETCLAW_HOST", "127.0.0.1"))
    serve_parser.add_argument("--port", type=int, default=int(os.getenv("POCKETCLAW_PORT", "8787")))
    serve_parser.add_argument("--token", default=os.getenv("POCKETCLAW_TOKEN"), help="optional bearer token")
    serve_parser.add_argument("--store-path", default=os.getenv("POCKETCLAW_STORE", os.path.expanduser("~/.pocketclaw/profiles.json")), help="path to persisted SSH profiles")

    list_parser = subparsers.add_parser("list-sessions", help="list available local tmux sessions")
    list_parser.add_argument("--json", action="store_true", help="output JSON")

    send_parser = subparsers.add_parser("send", help="send a command into a local tmux session")
    send_parser.add_argument("--session", required=True, help="target tmux session")
    send_parser.add_argument("--command", dest="command_text", required=True, help="command text to send")
    send_parser.add_argument("--no-enter", action="store_true", help="do not press Enter after sending")

    interrupt_parser = subparsers.add_parser("interrupt", help="send Ctrl+C to a local tmux session")
    interrupt_parser.add_argument("--session", required=True, help="target tmux session")

    capture_parser = subparsers.add_parser("capture", help="show recent output from a local tmux session")
    capture_parser.add_argument("--session", required=True, help="target tmux session")
    capture_parser.add_argument("--lines", type=int, default=120, help="number of pane lines to capture")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    tmux = TmuxClient(tmux_bin=args.tmux_bin)

    try:
        if args.subcommand == "serve":
            config = {
                "host": args.host,
                "port": args.port,
                "token": args.token,
                "tmux_bin": args.tmux_bin,
                "store_path": args.store_path,
            }
            server = create_server(config=config, tmux_client=tmux)
            token_hint = "enabled" if config["token"] else "disabled"
            print(f"PocketClaw listening on http://{config['host']}:{config['port']} (token {token_hint})")
            print(f"SSH profiles store: {config['store_path']}")
            server.serve_forever()
            return 0

        if args.subcommand == "list-sessions":
            sessions = tmux.list_sessions()
            if args.json:
                print(json.dumps({"sessions": sessions}, ensure_ascii=False))
            else:
                for session in sessions:
                    print(session)
            return 0

        if args.subcommand == "send":
            tmux.send_keys(session=args.session, command=args.command_text, press_enter=not args.no_enter)
            print(f"sent command to {args.session}")
            return 0

        if args.subcommand == "interrupt":
            tmux.interrupt(session=args.session)
            print(f"sent Ctrl+C to {args.session}")
            return 0

        if args.subcommand == "capture":
            print(tmux.capture_pane(session=args.session, lines=args.lines))
            return 0
    except (ValueError, RuntimeError) as exc:
        parser.exit(1, f"Error: {exc}\n")

    parser.exit(2, "unknown command\n")
    return 2
