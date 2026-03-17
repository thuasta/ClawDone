"""Local tmux helpers used by CLI and local diagnostics."""

from __future__ import annotations

import subprocess
from typing import Callable

Runner = Callable[..., subprocess.CompletedProcess[str]]


class TmuxClient:
    def __init__(self, tmux_bin: str = "tmux", runner: Runner | None = None):
        self.tmux_bin = tmux_bin
        self.runner = runner or subprocess.run

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        try:
            return self.runner(
                [self.tmux_bin, *args],
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(f"tmux binary not found: {self.tmux_bin}") from exc

    def list_sessions(self) -> list[str]:
        result = self._run("list-sessions", "-F", "#{session_name}")
        if result.returncode != 0:
            stderr = (result.stderr or "").lower()
            if "no server running" in stderr or "failed to connect to server" in stderr:
                return []
            raise RuntimeError(result.stderr.strip() or "failed to list tmux sessions")
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def send_keys(self, session: str, command: str, press_enter: bool = True) -> None:
        if not session.strip():
            raise ValueError("session name is required")
        if not command:
            raise ValueError("command is required")

        result = self._run("send-keys", "-t", session, "-l", command)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"failed to send command to {session}")

        if press_enter:
            enter_result = self._run("send-keys", "-t", session, "Enter")
            if enter_result.returncode != 0:
                raise RuntimeError(enter_result.stderr.strip() or f"failed to press Enter in {session}")

    def interrupt(self, session: str) -> None:
        result = self._run("send-keys", "-t", session, "C-c")
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"failed to send Ctrl+C to {session}")

    def capture_pane(self, session: str, lines: int = 120) -> str:
        start = f"-{max(1, lines)}"
        result = self._run("capture-pane", "-p", "-t", session, "-S", start)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"failed to capture tmux pane for {session}")
        return result.stdout.rstrip()

    def ping(self) -> bool:
        try:
            self.list_sessions()
            return True
        except RuntimeError:
            return False
