"""SSH execution and remote tmux inspection/control."""

from __future__ import annotations

import os
import shlex
from typing import Any

try:
    import paramiko
except ImportError:  # pragma: no cover
    paramiko = None

PARAMIKO_AVAILABLE = paramiko is not None


def command_result(returncode: int, stdout: str = "", stderr: str = "") -> dict[str, Any]:
    return {"returncode": returncode, "stdout": stdout, "stderr": stderr}


class SSHExecutor:
    def run(self, profile: dict[str, Any], command: str) -> dict[str, Any]:
        if paramiko is None:
            raise RuntimeError("paramiko is required for SSH support. Run: python3 -m pip install -e .")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs: dict[str, Any] = {
            "hostname": profile["host"],
            "port": profile["port"],
            "username": profile["username"],
            "timeout": 10,
        }
        if profile.get("password"):
            connect_kwargs["password"] = profile["password"]
            connect_kwargs["look_for_keys"] = False
            connect_kwargs["allow_agent"] = False
        else:
            connect_kwargs["look_for_keys"] = True
            connect_kwargs["allow_agent"] = True
        if profile.get("key_filename"):
            connect_kwargs["key_filename"] = os.path.expanduser(str(profile["key_filename"]))

        try:
            client.connect(**connect_kwargs)
            stdin, stdout, stderr = client.exec_command(command, timeout=15)
            _ = stdin
            exit_status = stdout.channel.recv_exit_status()
            out_text = stdout.read().decode("utf-8", errors="replace")
            err_text = stderr.read().decode("utf-8", errors="replace")
            return command_result(exit_status, out_text, err_text)
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"SSH connection failed for {profile['name']}: {exc}") from exc
        finally:
            client.close()


class RemoteTmuxClient:
    def __init__(self, executor: SSHExecutor | None = None):
        self.executor = executor or SSHExecutor()

    def _tmux_command(self, profile: dict[str, Any], *args: str) -> str:
        parts = [profile.get("tmux_bin") or "tmux", *args]
        return " ".join(shlex.quote(str(part)) for part in parts)

    def _run_tmux(self, profile: dict[str, Any], *args: str) -> dict[str, Any]:
        result = self.executor.run(profile, self._tmux_command(profile, *args))
        if result["returncode"] != 0:
            stderr = str(result.get("stderr", "")).strip()
            lowered = stderr.lower()
            if "no server running" in lowered or "failed to connect to server" in lowered:
                return command_result(0, "", stderr)
            raise RuntimeError(stderr or f"remote tmux command failed for {profile['name']}")
        return result

    def list_sessions(self, profile: dict[str, Any]) -> list[dict[str, Any]]:
        result = self._run_tmux(profile, "list-sessions", "-F", "#{session_name}\t#{session_windows}\t#{session_attached}")
        sessions: list[dict[str, Any]] = []
        for line in str(result["stdout"]).splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            sessions.append({
                "name": parts[0],
                "window_count": int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0,
                "attached": bool(int(parts[2])) if len(parts) > 2 and parts[2].isdigit() else False,
            })
        return sessions

    def list_windows(self, profile: dict[str, Any]) -> list[dict[str, Any]]:
        result = self._run_tmux(profile, "list-windows", "-a", "-F", "#{session_name}\t#{window_index}\t#{window_name}\t#{window_active}")
        windows: list[dict[str, Any]] = []
        for line in str(result["stdout"]).splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            windows.append({
                "session": parts[0],
                "index": int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0,
                "name": parts[2] if len(parts) > 2 else "",
                "active": bool(int(parts[3])) if len(parts) > 3 and parts[3].isdigit() else False,
            })
        return windows

    def list_panes(self, profile: dict[str, Any]) -> list[dict[str, Any]]:
        result = self._run_tmux(profile, "list-panes", "-a", "-F", "#{session_name}\t#{window_index}\t#{window_name}\t#{pane_index}\t#{pane_title}\t#{pane_current_command}\t#{pane_active}")
        panes: list[dict[str, Any]] = []
        for line in str(result["stdout"]).splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            session_name = parts[0]
            window_index = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
            pane_index = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0
            panes.append({
                "session": session_name,
                "window_index": window_index,
                "window_name": parts[2] if len(parts) > 2 else "",
                "pane_index": pane_index,
                "title": parts[4] if len(parts) > 4 else "",
                "current_command": parts[5] if len(parts) > 5 else "",
                "active": bool(int(parts[6])) if len(parts) > 6 and parts[6].isdigit() else False,
                "target": f"{session_name}:{window_index}.{pane_index}",
            })
        return panes

    def snapshot(self, profile: dict[str, Any], aliases: dict[str, str] | None = None) -> dict[str, Any]:
        alias_map = aliases or {}
        sessions = {item["name"]: {**item, "windows": []} for item in self.list_sessions(profile)}
        windows_by_key: dict[tuple[str, int], dict[str, Any]] = {}

        for window in self.list_windows(profile):
            session = sessions.setdefault(window["session"], {"name": window["session"], "window_count": 0, "attached": False, "windows": []})
            payload = {**window, "panes": []}
            session["windows"].append(payload)
            windows_by_key[(window["session"], window["index"])] = payload

        for pane in self.list_panes(profile):
            session = sessions.setdefault(pane["session"], {"name": pane["session"], "window_count": 0, "attached": False, "windows": []})
            window_key = (pane["session"], pane["window_index"])
            window = windows_by_key.get(window_key)
            if window is None:
                window = {
                    "session": pane["session"],
                    "index": pane["window_index"],
                    "name": pane["window_name"],
                    "active": False,
                    "panes": [],
                }
                session["windows"].append(window)
                windows_by_key[window_key] = window
            window["panes"].append({**pane, "alias": alias_map.get(pane["target"], "")})

        session_list = sorted(sessions.values(), key=lambda item: item["name"])
        for session in session_list:
            session["windows"] = sorted(session["windows"], key=lambda item: item["index"])
            for window in session["windows"]:
                window["panes"] = sorted(window["panes"], key=lambda item: item["pane_index"])
        return {"profile": profile["name"], "sessions": session_list}

    def send_keys(self, profile: dict[str, Any], target: str, command: str, press_enter: bool = True) -> None:
        if not target.strip():
            raise ValueError("target is required")
        if not command:
            raise ValueError("command is required")
        result = self.executor.run(profile, self._tmux_command(profile, "send-keys", "-t", target, "-l", command))
        if result["returncode"] != 0:
            raise RuntimeError(str(result.get("stderr", "")).strip() or f"failed to send command to {target}")
        if press_enter:
            enter_result = self.executor.run(profile, self._tmux_command(profile, "send-keys", "-t", target, "Enter"))
            if enter_result["returncode"] != 0:
                raise RuntimeError(str(enter_result.get("stderr", "")).strip() or f"failed to press Enter in {target}")

    def interrupt(self, profile: dict[str, Any], target: str) -> None:
        result = self.executor.run(profile, self._tmux_command(profile, "send-keys", "-t", target, "C-c"))
        if result["returncode"] != 0:
            raise RuntimeError(str(result.get("stderr", "")).strip() or f"failed to send Ctrl+C to {target}")

    def capture_pane(self, profile: dict[str, Any], target: str, lines: int = 120) -> str:
        start = f"-{max(1, lines)}"
        result = self.executor.run(profile, self._tmux_command(profile, "capture-pane", "-p", "-t", target, "-S", start))
        if result["returncode"] != 0:
            raise RuntimeError(str(result.get("stderr", "")).strip() or f"failed to capture pane {target}")
        return str(result.get("stdout", "")).rstrip()

    def test_connection(self, profile: dict[str, Any]) -> dict[str, Any]:
        sessions = self.list_sessions(profile)
        return {"ok": True, "session_count": len(sessions), "sessions": sessions}
