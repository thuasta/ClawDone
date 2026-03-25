"""MCP server that runs on a remote machine and wraps local tmux as tools.

Implements JSON-RPC 2.0 over stdio (newline-delimited) or HTTP POST.
No external dependencies.
Start with: python -m clawdone mcp-agent
"""

from __future__ import annotations

import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


TOOLS = [
    {
        "name": "send_command",
        "description": "Send a command to a local tmux session via send-keys.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session": {"type": "string", "description": "tmux session name"},
                "command": {"type": "string", "description": "command text to send"},
                "press_enter": {"type": "boolean", "description": "press Enter after sending (default true)"},
            },
            "required": ["session", "command"],
        },
    },
    {
        "name": "capture_pane",
        "description": "Capture recent output from a local tmux session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session": {"type": "string", "description": "tmux session name"},
                "lines": {"type": "integer", "description": "number of lines to capture (default 120)"},
            },
            "required": ["session"],
        },
    },
    {
        "name": "list_sessions",
        "description": "List all local tmux sessions.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "interrupt",
        "description": "Send Ctrl+C to a local tmux session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session": {"type": "string", "description": "tmux session name"},
            },
            "required": ["session"],
        },
    },
]


def _run(args: list[str], timeout: int = 10) -> str:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"command failed: {' '.join(args)}")
    return result.stdout


def tool_send_command(params: dict[str, Any]) -> str:
    session = str(params.get("session", "")).strip()
    command = str(params.get("command", ""))
    press_enter = bool(params.get("press_enter", True))
    if not session:
        raise ValueError("session is required")
    keys = command + (" Enter" if press_enter else "")
    _run(["tmux", "send-keys", "-t", session, command] + (["Enter"] if press_enter else []))
    return f"sent to {session}"


def tool_capture_pane(params: dict[str, Any]) -> str:
    session = str(params.get("session", "")).strip()
    lines = int(params.get("lines", 120))
    if not session:
        raise ValueError("session is required")
    return _run(["tmux", "capture-pane", "-p", "-t", session, "-S", str(-lines)])


def tool_list_sessions(_params: dict[str, Any]) -> list[str]:
    output = _run(["tmux", "list-sessions", "-F", "#{session_name}"])
    return [line for line in output.splitlines() if line.strip()]


def tool_interrupt(params: dict[str, Any]) -> str:
    session = str(params.get("session", "")).strip()
    if not session:
        raise ValueError("session is required")
    _run(["tmux", "send-keys", "-t", session, "C-c"])
    return f"sent Ctrl+C to {session}"


TOOL_HANDLERS = {
    "send_command": tool_send_command,
    "capture_pane": tool_capture_pane,
    "list_sessions": tool_list_sessions,
    "interrupt": tool_interrupt,
}


def _ok(req_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle(request: dict[str, Any]) -> dict[str, Any] | None:
    req_id = request.get("id")
    method = str(request.get("method", ""))
    params = request.get("params") or {}

    if method == "initialize":
        return _ok(req_id, {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "clawdone-agent", "version": "1.0.0"},
            "capabilities": {"tools": {}},
        })

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return _ok(req_id, {"tools": TOOLS})

    if method == "tools/call":
        name = str(params.get("name", ""))
        args = params.get("arguments") or {}
        handler = TOOL_HANDLERS.get(name)
        if handler is None:
            return _err(req_id, -32601, f"unknown tool: {name}")
        try:
            result = handler(args)
            text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
            return _ok(req_id, {"content": [{"type": "text", "text": text}]})
        except Exception as exc:
            return _ok(req_id, {"content": [{"type": "text", "text": f"error: {exc}"}], "isError": True})

    return _err(req_id, -32601, "Method not found")


def run_stdio() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            response = _err(None, -32700, "Parse error")
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
            continue
        response = handle(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


def run_http(host: str = "0.0.0.0", port: int = 8788) -> None:
    """Serve JSON-RPC 2.0 over HTTP POST for use with mcp_url on profiles."""

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:  # suppress access logs
            pass

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b""
            try:
                request = json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._send(400, _err(None, -32700, "Parse error"))
                return
            response = handle(request)
            self._send(200, response if response is not None else {})

        def _send(self, status: int, payload: Any) -> None:
            data = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"ClawDone MCP agent server listening on http://{host}:{port}", file=sys.stderr)
    server.serve_forever()
