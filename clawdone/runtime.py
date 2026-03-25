"""AgentRuntime abstraction for pluggable agent backends."""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any


class AgentRuntime(ABC):
    @abstractmethod
    async def send_command(self, target: str, command: str) -> None: ...

    @abstractmethod
    async def capture_output(self, target: str, lines: int = 120) -> str: ...

    @abstractmethod
    async def list_targets(self) -> list[str]: ...

    @abstractmethod
    async def test_connection(self) -> dict[str, Any]: ...


class SshTmuxRuntime(AgentRuntime):
    """Wraps RemoteTmuxClient with asyncio.to_thread for non-blocking calls."""

    def __init__(self, profile: dict[str, Any], remote_tmux: Any) -> None:
        self._profile = profile
        self._remote_tmux = remote_tmux

    async def send_command(self, target: str, command: str) -> None:
        await asyncio.to_thread(
            self._remote_tmux.send_keys, self._profile, target=target, command=command, press_enter=True
        )

    async def capture_output(self, target: str, lines: int = 120) -> str:
        return await asyncio.to_thread(
            self._remote_tmux.capture_pane, self._profile, target=target, lines=lines
        )

    async def list_targets(self) -> list[str]:
        aliases: dict[str, str] = {}
        snapshot = await asyncio.to_thread(self._remote_tmux.snapshot, self._profile, aliases=aliases)
        targets: list[str] = []
        for session in snapshot.get("sessions", []):
            for window in session.get("windows", []):
                for pane in window.get("panes", []):
                    t = str(pane.get("target", "")).strip()
                    if t:
                        targets.append(t)
        return targets

    async def test_connection(self) -> dict[str, Any]:
        result = await asyncio.to_thread(self._remote_tmux.test_connection, self._profile)
        return result if isinstance(result, dict) else {"ok": bool(result)}


class McpRuntime(AgentRuntime):
    """Calls a remote MCP agent server over HTTP using urllib (no extra deps)."""

    def __init__(self, mcp_url: str, timeout: float = 15.0) -> None:
        self._url = mcp_url.rstrip("/")
        self._timeout = timeout

    def _post(self, method: str, arguments: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": method, "arguments": arguments},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._url, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"MCP HTTP {exc.code}") from exc
        if "error" in result:
            raise RuntimeError(f"MCP error: {result['error']}")
        content = result.get("result", {}).get("content", [])
        if content and content[0].get("isError"):
            raise RuntimeError(f"MCP tool error: {content[0].get('text', '')}")
        return result

    async def send_command(self, target: str, command: str) -> None:
        await asyncio.to_thread(
            self._post, "send_command", {"session": target, "command": command, "press_enter": True}
        )

    async def capture_output(self, target: str, lines: int = 120) -> str:
        result = await asyncio.to_thread(
            self._post, "capture_pane", {"session": target, "lines": lines}
        )
        content = result.get("result", {}).get("content", [])
        if content:
            return str(content[0].get("text", ""))
        return ""

    async def list_targets(self) -> list[str]:
        result = await asyncio.to_thread(self._post, "list_sessions", {})
        content = result.get("result", {}).get("content", [])
        if content:
            try:
                data = json.loads(content[0].get("text", "[]"))
                if isinstance(data, list):
                    return [str(s) for s in data]
            except (json.JSONDecodeError, TypeError):
                pass
        return []

    async def test_connection(self) -> dict[str, Any]:
        try:
            await asyncio.to_thread(self._post, "list_sessions", {})
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
