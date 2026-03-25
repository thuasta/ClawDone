"""MCP server that exposes ClawDone's todo/dispatch API as tools.

Implements JSON-RPC 2.0 over stdio (newline-delimited). No external dependencies.
Calls ClawDone's own HTTP API so auth and logic stay consistent.
Start with: python -m clawdone mcp-server --port 8787 --token TOKEN
"""

from __future__ import annotations

import json
import sys
import urllib.request
import urllib.error
from typing import Any


TOOLS = [
    {
        "name": "list_profiles",
        "description": "List all SSH profiles configured in ClawDone.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_todos",
        "description": "List todos for a profile, optionally filtered by target agent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "description": "profile name"},
                "target": {"type": "string", "description": "optional target session filter"},
            },
            "required": ["profile"],
        },
    },
    {
        "name": "create_todo",
        "description": "Create a new todo item for an agent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string"},
                "target": {"type": "string"},
                "title": {"type": "string"},
                "detail": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
            },
            "required": ["profile", "target", "title"],
        },
    },
    {
        "name": "dispatch_todo",
        "description": "Auto-dispatch a todo to its assigned agent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "todo_id": {"type": "string", "description": "todo ID to dispatch"},
            },
            "required": ["todo_id"],
        },
    },
    {
        "name": "update_todo_status",
        "description": "Update the status of a todo item.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "todo_id": {"type": "string"},
                "status": {"type": "string", "enum": ["todo", "in_progress", "done", "verified", "blocked"]},
                "progress_note": {"type": "string"},
            },
            "required": ["todo_id", "status"],
        },
    },
    {
        "name": "get_pane_output",
        "description": "Capture recent output from a remote tmux pane.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string"},
                "target": {"type": "string"},
                "lines": {"type": "integer", "description": "number of lines (default 120)"},
            },
            "required": ["profile", "target"],
        },
    },
    {
        "name": "send_command",
        "description": "Send a command to a remote agent's tmux session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string"},
                "target": {"type": "string"},
                "command": {"type": "string"},
            },
            "required": ["profile", "target", "command"],
        },
    },
]


class ClawDoneClient:
    def __init__(self, base_url: str, token: str | None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        url = self.base_url + path
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers: dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {body_text[:200]}") from exc

    def list_profiles(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/profiles")

    def list_todos(self, profile: str, target: str = "") -> list[dict[str, Any]]:
        qs = f"?profile={urllib.parse.quote(profile)}"
        if target:
            qs += f"&target={urllib.parse.quote(target)}"
        return self._request("GET", f"/api/todos{qs}")

    def create_todo(self, profile: str, target: str, title: str, detail: str = "", priority: str = "medium") -> dict[str, Any]:
        return self._request("POST", "/api/todos", {
            "profile": profile, "target": target, "title": title,
            "detail": detail, "priority": priority,
        })

    def dispatch_todo(self, todo_id: str) -> dict[str, Any]:
        return self._request("POST", f"/api/todos/{urllib.parse.quote(todo_id)}/dispatch", {})

    def update_todo_status(self, todo_id: str, status: str, progress_note: str = "") -> dict[str, Any]:
        return self._request("PATCH", f"/api/todos/{urllib.parse.quote(todo_id)}", {
            "status": status, "progress_note": progress_note,
        })

    def get_pane_output(self, profile: str, target: str, lines: int = 120) -> str:
        result = self._request("POST", "/api/capture", {"profile": profile, "target": target, "lines": lines})
        return str(result.get("output", ""))

    def send_command(self, profile: str, target: str, command: str) -> dict[str, Any]:
        return self._request("POST", "/api/send", {"profile": profile, "target": target, "command": command})


# lazy import for urllib.parse used in ClawDoneClient
import urllib.parse  # noqa: E402


def _ok(req_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _text(value: Any) -> str:
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)


def handle(request: dict[str, Any], client: ClawDoneClient) -> dict[str, Any] | None:
    req_id = request.get("id")
    method = str(request.get("method", ""))
    params = request.get("params") or {}

    if method == "initialize":
        return _ok(req_id, {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "clawdone-mcp", "version": "1.0.0"},
            "capabilities": {"tools": {}},
        })

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return _ok(req_id, {"tools": TOOLS})

    if method == "tools/call":
        name = str(params.get("name", ""))
        args = params.get("arguments") or {}
        try:
            result = _dispatch_tool(name, args, client)
            return _ok(req_id, {"content": [{"type": "text", "text": _text(result)}]})
        except Exception as exc:
            return _ok(req_id, {"content": [{"type": "text", "text": f"error: {exc}"}], "isError": True})

    return _err(req_id, -32601, "Method not found")


def _dispatch_tool(name: str, args: dict[str, Any], client: ClawDoneClient) -> Any:
    if name == "list_profiles":
        return client.list_profiles()
    if name == "list_todos":
        return client.list_todos(
            profile=str(args.get("profile", "")),
            target=str(args.get("target", "")),
        )
    if name == "create_todo":
        return client.create_todo(
            profile=str(args.get("profile", "")),
            target=str(args.get("target", "")),
            title=str(args.get("title", "")),
            detail=str(args.get("detail", "")),
            priority=str(args.get("priority", "medium")),
        )
    if name == "dispatch_todo":
        return client.dispatch_todo(todo_id=str(args.get("todo_id", "")))
    if name == "update_todo_status":
        return client.update_todo_status(
            todo_id=str(args.get("todo_id", "")),
            status=str(args.get("status", "")),
            progress_note=str(args.get("progress_note", "")),
        )
    if name == "get_pane_output":
        return client.get_pane_output(
            profile=str(args.get("profile", "")),
            target=str(args.get("target", "")),
            lines=int(args.get("lines", 120)),
        )
    if name == "send_command":
        return client.send_command(
            profile=str(args.get("profile", "")),
            target=str(args.get("target", "")),
            command=str(args.get("command", "")),
        )
    raise ValueError(f"unknown tool: {name}")


def run_stdio(base_url: str, token: str | None) -> None:
    client = ClawDoneClient(base_url=base_url, token=token)
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
        response = handle(request, client)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
