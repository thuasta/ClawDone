"""SSH execution and remote tmux inspection/control."""

from __future__ import annotations

import os
import shlex
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

try:
    import paramiko
except ImportError:  # pragma: no cover
    paramiko = None

PARAMIKO_AVAILABLE = paramiko is not None
HOST_KEY_POLICIES = {"strict", "accept-new", "insecure"}


def command_result(returncode: int, stdout: str = "", stderr: str = "") -> dict[str, Any]:
    return {"returncode": returncode, "stdout": stdout, "stderr": stderr}


class SSHExecutor:
    def __init__(
        self,
        connect_timeout: float = 10.0,
        command_timeout: float = 15.0,
        retries: int = 0,
        retry_backoff_ms: int = 250,
        host_key_policy: str = "strict",
        known_hosts_file: str = "~/.ssh/known_hosts",
    ):
        self.connect_timeout = self._positive_float(connect_timeout, field_name="connect_timeout")
        self.command_timeout = self._positive_float(command_timeout, field_name="command_timeout")
        self.retries = self._non_negative_int(retries, field_name="retries")
        self.retry_backoff_ms = self._non_negative_int(retry_backoff_ms, field_name="retry_backoff_ms")
        self.host_key_policy = self._normalize_host_key_policy(host_key_policy)
        self.known_hosts_file = os.path.expanduser(known_hosts_file)

    @staticmethod
    def _positive_float(value: Any, field_name: str) -> float:
        parsed = float(value)
        if parsed <= 0:
            raise ValueError(f"{field_name} must be > 0")
        return parsed

    @staticmethod
    def _non_negative_int(value: Any, field_name: str) -> int:
        parsed = int(value)
        if parsed < 0:
            raise ValueError(f"{field_name} must be >= 0")
        return parsed

    @staticmethod
    def _normalize_host_key_policy(value: Any) -> str:
        policy = str(value or "").strip().lower()
        if policy not in HOST_KEY_POLICIES:
            allowed = ", ".join(sorted(HOST_KEY_POLICIES))
            raise ValueError(f"host_key_policy must be one of: {allowed}")
        return policy

    def _resolve_positive_float(self, value: Any, fallback: float, field_name: str) -> float:
        if value in (None, "", 0, 0.0, "0"):
            return fallback
        return self._positive_float(value, field_name=field_name)

    def _resolve_non_negative_int(self, value: Any, fallback: int, field_name: str) -> int:
        if value in (None, ""):
            return fallback
        return self._non_negative_int(value, field_name=field_name)

    def _resolve_host_key_policy(self, value: Any) -> str:
        if value in (None, ""):
            return self.host_key_policy
        return self._normalize_host_key_policy(value)

    def _configure_host_key_policy(self, client: Any, policy: str) -> None:
        client.load_system_host_keys()
        if policy == "strict":
            if self.known_hosts_file and Path(self.known_hosts_file).exists():
                client.load_host_keys(self.known_hosts_file)
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
            return

        if policy == "accept-new":
            if self.known_hosts_file:
                known_hosts = Path(self.known_hosts_file)
                known_hosts.parent.mkdir(parents=True, exist_ok=True)
                if not known_hosts.exists():
                    known_hosts.touch(mode=0o600)
                client.load_host_keys(str(known_hosts))
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            return

        client.set_missing_host_key_policy(paramiko.WarningPolicy())

    def run(self, profile: dict[str, Any], command: str) -> dict[str, Any]:
        if paramiko is None:
            raise RuntimeError("paramiko is required for SSH support. Run: python3 -m pip install -e .")

        profile_name = str(profile.get("name", "<unknown>"))
        connect_timeout = self._resolve_positive_float(profile.get("ssh_timeout"), self.connect_timeout, field_name="ssh_timeout")
        command_timeout = self._resolve_positive_float(
            profile.get("ssh_command_timeout"), self.command_timeout, field_name="ssh_command_timeout"
        )
        retries = self._resolve_non_negative_int(profile.get("ssh_retries"), self.retries, field_name="ssh_retries")
        retry_backoff_ms = self._resolve_non_negative_int(
            profile.get("ssh_retry_backoff_ms"), self.retry_backoff_ms, field_name="ssh_retry_backoff_ms"
        )
        host_key_policy = self._resolve_host_key_policy(profile.get("host_key_policy"))

        connect_kwargs: dict[str, Any] = {
            "hostname": profile["host"],
            "port": profile["port"],
            "username": profile["username"],
            "timeout": connect_timeout,
        }
        resolved_password = self._resolve_profile_password(profile)
        if resolved_password:
            connect_kwargs["password"] = resolved_password
            connect_kwargs["look_for_keys"] = False
            connect_kwargs["allow_agent"] = False
        else:
            connect_kwargs["look_for_keys"] = True
            connect_kwargs["allow_agent"] = True
        if profile.get("key_filename"):
            connect_kwargs["key_filename"] = os.path.expanduser(str(profile["key_filename"]))

        attempts = retries + 1
        last_exc: Exception | None = None
        for attempt in range(attempts):
            client = paramiko.SSHClient()
            self._configure_host_key_policy(client, host_key_policy)
            try:
                client.connect(**connect_kwargs)
                stdin, stdout, stderr = client.exec_command(command, timeout=command_timeout)
                _ = stdin
                exit_status = stdout.channel.recv_exit_status()
                out_text = stdout.read().decode("utf-8", errors="replace")
                err_text = stderr.read().decode("utf-8", errors="replace")
                return command_result(exit_status, out_text, err_text)
            except Exception as exc:  # pragma: no cover
                last_exc = exc
                if attempt + 1 >= attempts:
                    break
                if retry_backoff_ms > 0:
                    time.sleep(retry_backoff_ms / 1000)
            finally:
                client.close()

        assert last_exc is not None  # pragma: no cover
        raise RuntimeError(f"SSH connection failed for {profile_name} after {attempts} attempt(s): {last_exc}") from last_exc

    def _resolve_profile_password(self, profile: dict[str, Any]) -> str:
        direct = str(profile.get("password", ""))
        if direct:
            return direct
        ref = str(profile.get("password_ref", "")).strip()
        if not ref:
            return ""
        if ref.startswith("env:"):
            env_key = ref[4:].strip()
            if not env_key:
                raise ValueError("password_ref env key is required")
            return str(os.getenv(env_key, ""))
        if ref.startswith("file:"):
            file_path = os.path.expanduser(ref[5:].strip())
            if not file_path:
                raise ValueError("password_ref file path is required")
            try:
                return Path(file_path).read_text(encoding="utf-8").strip()
            except OSError as exc:
                raise RuntimeError(f"failed to read password_ref file: {file_path}") from exc
        raise ValueError("password_ref must start with env: or file:")


class RemoteTmuxClient:
    def __init__(self, executor: SSHExecutor | None = None, dashboard_workers: int = 6):
        self.executor = executor or SSHExecutor()
        self.dashboard_workers = max(1, int(dashboard_workers))

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
            sessions.append(
                {
                    "name": parts[0],
                    "window_count": int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0,
                    "attached": bool(int(parts[2])) if len(parts) > 2 and parts[2].isdigit() else False,
                }
            )
        return sessions

    def list_windows(self, profile: dict[str, Any]) -> list[dict[str, Any]]:
        result = self._run_tmux(profile, "list-windows", "-a", "-F", "#{session_name}\t#{window_index}\t#{window_name}\t#{window_active}")
        windows: list[dict[str, Any]] = []
        for line in str(result["stdout"]).splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            windows.append(
                {
                    "session": parts[0],
                    "index": int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0,
                    "name": parts[2] if len(parts) > 2 else "",
                    "active": bool(int(parts[3])) if len(parts) > 3 and parts[3].isdigit() else False,
                }
            )
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
            panes.append(
                {
                    "session": session_name,
                    "window_index": window_index,
                    "window_name": parts[2] if len(parts) > 2 else "",
                    "pane_index": pane_index,
                    "title": parts[4] if len(parts) > 4 else "",
                    "current_command": parts[5] if len(parts) > 5 else "",
                    "active": bool(int(parts[6])) if len(parts) > 6 and parts[6].isdigit() else False,
                    "target": f"{session_name}:{window_index}.{pane_index}",
                }
            )
        return panes

    def snapshot(self, profile: dict[str, Any], aliases: dict[str, str] | None = None) -> dict[str, Any]:
        alias_map = aliases or {}
        sessions = {item["name"]: {**item, "windows": []} for item in self.list_sessions(profile)}
        windows_by_key: dict[tuple[str, int], dict[str, Any]] = {}

        for window in self.list_windows(profile):
            session = sessions.setdefault(
                window["session"],
                {"name": window["session"], "window_count": 0, "attached": False, "windows": []},
            )
            payload = {**window, "panes": []}
            session["windows"].append(payload)
            windows_by_key[(window["session"], window["index"])] = payload

        for pane in self.list_panes(profile):
            session = sessions.setdefault(
                pane["session"],
                {"name": pane["session"], "window_count": 0, "attached": False, "windows": []},
            )
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

    def _offline_summary(self, profile: dict[str, Any], error: str, latency_ms: float) -> dict[str, Any]:
        return {
            "name": profile["name"],
            "group": profile.get("group", "General"),
            "tags": profile.get("tags", []),
            "favorite": bool(profile.get("favorite", False)),
            "description": profile.get("description", ""),
            "host": profile.get("host", ""),
            "online": False,
            "error": error,
            "latency_ms": latency_ms,
            "session_count": 0,
            "window_count": 0,
            "pane_count": 0,
            "sessions": [],
        }

    def inspect_profile(self, profile: dict[str, Any], aliases: dict[str, str] | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            snapshot = self.snapshot(profile, aliases=aliases)
            sessions = snapshot.get("sessions", [])
            windows = [window for session in sessions for window in session.get("windows", [])]
            panes = [pane for window in windows for pane in window.get("panes", [])]
            return {
                "name": profile["name"],
                "group": profile.get("group", "General"),
                "tags": profile.get("tags", []),
                "favorite": bool(profile.get("favorite", False)),
                "description": profile.get("description", ""),
                "host": profile.get("host", ""),
                "online": True,
                "error": "",
                "latency_ms": round((time.perf_counter() - started) * 1000, 1),
                "session_count": len(sessions),
                "window_count": len(windows),
                "pane_count": len(panes),
                "sessions": sessions,
            }
        except Exception as exc:
            return self._offline_summary(
                profile,
                error=str(exc),
                latency_ms=round((time.perf_counter() - started) * 1000, 1),
            )

    def dashboard(self, profiles: list[dict[str, Any]], aliases_by_profile: dict[str, dict[str, str]] | None = None) -> dict[str, Any]:
        aliases_by_profile = aliases_by_profile or {}
        if not profiles:
            return {"targets": [], "groups": []}

        if self.dashboard_workers <= 1 or len(profiles) <= 1:
            targets = [self.inspect_profile(profile, aliases=aliases_by_profile.get(profile["name"], {})) for profile in profiles]
        else:
            targets: list[dict[str, Any] | None] = [None] * len(profiles)
            max_workers = min(self.dashboard_workers, len(profiles))
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {
                    pool.submit(self.inspect_profile, profile, aliases_by_profile.get(profile["name"], {})): (index, profile)
                    for index, profile in enumerate(profiles)
                }
                for future in as_completed(futures):
                    index, profile = futures[future]
                    try:
                        targets[index] = future.result()
                    except Exception as exc:  # pragma: no cover
                        targets[index] = self._offline_summary(profile, error=str(exc), latency_ms=0.0)
            targets = [target if target is not None else self._offline_summary(profiles[index], error="unknown error", latency_ms=0.0) for index, target in enumerate(targets)]

        groups = sorted({target.get("group", "General") for target in targets})
        return {"targets": targets, "groups": groups}

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
        summary = self.inspect_profile(profile)
        return {
            "ok": summary["online"],
            "session_count": summary["session_count"],
            "window_count": summary["window_count"],
            "pane_count": summary["pane_count"],
            "error": summary["error"],
        }
