"""CLI entrypoints."""

from __future__ import annotations

import argparse
import json
import os

from .local_tmux import TmuxClient
from .web import create_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ClawDone: control tmux-hosted coding agents from your phone")
    parser.add_argument("--tmux-bin", default=os.getenv("CLAWDONE_TMUX_BIN", "tmux"), help="local tmux binary path")

    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    serve_parser = subparsers.add_parser("serve", help="start the ClawDone mobile web UI")
    serve_parser.add_argument("--host", default=os.getenv("CLAWDONE_HOST", "127.0.0.1"))
    serve_parser.add_argument("--port", type=int, default=int(os.getenv("CLAWDONE_PORT", "8787")))
    serve_parser.add_argument("--token", default=os.getenv("CLAWDONE_TOKEN"), help="optional bearer token")
    serve_parser.add_argument("--store-path", default=os.getenv("CLAWDONE_STORE", os.path.expanduser("~/.clawdone/profiles.json")), help="path to persisted SSH profiles")
    serve_parser.add_argument("--ssh-timeout", type=int, default=int(os.getenv("CLAWDONE_SSH_TIMEOUT", "10")), help="default SSH connect timeout in seconds")
    serve_parser.add_argument("--ssh-command-timeout", type=int, default=int(os.getenv("CLAWDONE_SSH_COMMAND_TIMEOUT", "15")), help="default SSH remote command timeout in seconds")
    serve_parser.add_argument("--ssh-retries", type=int, default=int(os.getenv("CLAWDONE_SSH_RETRIES", "0")), help="default SSH retry count for failed connections")
    serve_parser.add_argument("--ssh-retry-backoff-ms", type=int, default=int(os.getenv("CLAWDONE_SSH_RETRY_BACKOFF_MS", "250")), help="backoff delay between SSH retries in milliseconds")
    serve_parser.add_argument("--dashboard-workers", type=int, default=int(os.getenv("CLAWDONE_DASHBOARD_WORKERS", "6")), help="parallel workers used for dashboard target inspection")
    serve_parser.add_argument("--dispatch-concurrency", type=int, default=int(os.getenv("CLAWDONE_DISPATCH_CONCURRENCY", "8")), help="max concurrent todo dispatches in autopilot loop")
    serve_parser.add_argument(
        "--risk-policy",
        default=os.getenv("CLAWDONE_RISK_POLICY", "confirm"),
        choices=["allow", "confirm", "deny"],
        help="dangerous command policy",
    )
    serve_parser.add_argument(
        "--rbac-tokens-json",
        default=os.getenv("CLAWDONE_RBAC_TOKENS", ""),
        help='optional JSON object mapping token to role, e.g. {"admin-token":"admin","viewer-token":"viewer"}',
    )
    serve_parser.add_argument(
        "--host-key-policy",
        default=os.getenv("CLAWDONE_HOST_KEY_POLICY", "strict"),
        choices=["strict", "accept-new", "insecure"],
        help="default SSH host key policy",
    )
    serve_parser.add_argument(
        "--known-hosts-file",
        default=os.getenv("CLAWDONE_KNOWN_HOSTS_FILE", "~/.ssh/known_hosts"),
        help="known_hosts file used by strict/accept-new policies",
    )

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

    mcp_server_parser = subparsers.add_parser("mcp-server", help="start MCP server wrapping ClawDone HTTP API (stdio transport)")
    mcp_server_parser.add_argument("--port", type=int, default=int(os.getenv("CLAWDONE_PORT", "8787")), help="ClawDone HTTP API port")
    mcp_server_parser.add_argument("--api-host", default=os.getenv("CLAWDONE_HOST", "127.0.0.1"), help="ClawDone HTTP API host")
    mcp_server_parser.add_argument("--token", default=os.getenv("CLAWDONE_TOKEN"), help="ClawDone bearer token")

    mcp_agent_parser = subparsers.add_parser("mcp-agent", help="start MCP agent server wrapping local tmux")
    mcp_agent_parser.add_argument("--http", action="store_true", help="serve over HTTP instead of stdio (for use with mcp_url on profiles)")
    mcp_agent_parser.add_argument("--host", default="0.0.0.0", help="HTTP listen host (default 0.0.0.0)")
    mcp_agent_parser.add_argument("--port", type=int, default=8788, help="HTTP listen port (default 8788)")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    tmux = TmuxClient(tmux_bin=args.tmux_bin)

    try:
        if args.subcommand == "serve":
            rbac_tokens: dict[str, str] = {}
            if args.rbac_tokens_json:
                try:
                    decoded = json.loads(args.rbac_tokens_json)
                except json.JSONDecodeError as exc:
                    raise ValueError("invalid --rbac-tokens-json") from exc
                if not isinstance(decoded, dict):
                    raise ValueError("--rbac-tokens-json must be a JSON object")
                rbac_tokens = {str(k): str(v) for k, v in decoded.items()}
            config = {
                "host": args.host,
                "port": args.port,
                "token": args.token,
                "rbac_tokens": rbac_tokens,
                "tmux_bin": args.tmux_bin,
                "store_path": args.store_path,
                "ssh_timeout": args.ssh_timeout,
                "ssh_command_timeout": args.ssh_command_timeout,
                "ssh_retries": args.ssh_retries,
                "ssh_retry_backoff_ms": args.ssh_retry_backoff_ms,
                "dashboard_workers": args.dashboard_workers,
                "dispatch_concurrency": args.dispatch_concurrency,
                "risk_policy": args.risk_policy,
                "host_key_policy": args.host_key_policy,
                "known_hosts_file": args.known_hosts_file,
            }
            server = create_server(config=config, tmux_client=tmux)
            token_hint = "enabled" if config["token"] else "disabled"
            print(f"ClawDone listening on http://{config['host']}:{config['port']} (token {token_hint})")
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

        if args.subcommand == "mcp-server":
            from .mcp_server import run_stdio as mcp_run_stdio
            base_url = f"http://{args.api_host}:{args.port}"
            import sys
            print(f"ClawDone MCP server ready (connecting to {base_url})", file=sys.stderr)
            mcp_run_stdio(base_url=base_url, token=args.token)
            return 0

        if args.subcommand == "mcp-agent":
            from .mcp_agent_server import run_stdio as agent_run_stdio, run_http as agent_run_http
            import sys
            if args.http:
                agent_run_http(host=args.host, port=args.port)
            else:
                print("ClawDone MCP agent server ready (wrapping local tmux)", file=sys.stderr)
                agent_run_stdio()
            return 0

    except (ValueError, RuntimeError) as exc:
        parser.exit(1, f"Error: {exc}\n")

    parser.exit(2, "unknown command\n")
    return 2

