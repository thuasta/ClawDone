"""HTTP app and request handlers."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from .html import INDEX_HTML
from .local_tmux import TmuxClient
from .remote import HOST_KEY_POLICIES, PARAMIKO_AVAILABLE, RemoteTmuxClient, SSHExecutor
from .store import ProfileStore, mask_profile, normalize_profile

ROLE_LEVELS = {"viewer": 1, "operator": 2, "admin": 3}
RISK_POLICIES = {"allow", "confirm", "deny"}
INDEX_VIEWS = ("dashboard", "auth", "chat", "todo", "delivery")
RISK_HIGH_PATTERNS = [
    re.compile(r"\brm\s+-rf\b", flags=re.IGNORECASE),
    re.compile(r"\bmkfs(\.\w+)?\b", flags=re.IGNORECASE),
    re.compile(r"\bdd\s+if=", flags=re.IGNORECASE),
    re.compile(r"\bshutdown\b", flags=re.IGNORECASE),
    re.compile(r"\breboot\b", flags=re.IGNORECASE),
    re.compile(r":\(\)\s*\{\s*:\|:\s*&\s*\};:", flags=re.IGNORECASE),
]


def _positive_int(config: dict[str, Any], key: str, default: int) -> int:
    value = config.get(key, default)
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{key} must be > 0")
    return parsed


def _non_negative_int(config: dict[str, Any], key: str, default: int) -> int:
    value = config.get(key, default)
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"{key} must be >= 0")
    return parsed


def _host_key_policy(config: dict[str, Any]) -> str:
    policy = str(config.get("host_key_policy", "strict") or "strict").strip().lower()
    if policy not in HOST_KEY_POLICIES:
        allowed = ", ".join(sorted(HOST_KEY_POLICIES))
        raise ValueError(f"host_key_policy must be one of: {allowed}")
    return policy


def normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    raw_rbac = config.get("rbac_tokens", {})
    rbac_tokens: dict[str, str] = {}
    if isinstance(raw_rbac, dict):
        for token, role in raw_rbac.items():
            cleaned_role = str(role).strip().lower()
            if cleaned_role not in ROLE_LEVELS:
                continue
            token_value = str(token).strip()
            if token_value:
                rbac_tokens[token_value] = cleaned_role
    risk_policy = str(config.get("risk_policy", "confirm") or "confirm").strip().lower()
    if risk_policy not in RISK_POLICIES:
        allowed = ", ".join(sorted(RISK_POLICIES))
        raise ValueError(f"risk_policy must be one of: {allowed}")
    return {
        "host": str(config.get("host", "127.0.0.1")),
        "port": int(config.get("port", 8787)),
        "token": config.get("token") or None,
        "rbac_tokens": rbac_tokens,
        "default_role": str(config.get("default_role", "admin") or "admin").strip().lower(),
        "risk_policy": risk_policy,
        "tmux_bin": str(config.get("tmux_bin", "tmux")),
        "store_path": str(config.get("store_path", "~/.clawdone/profiles.json")),
        "ssh_timeout": _positive_int(config, "ssh_timeout", 10),
        "ssh_command_timeout": _positive_int(config, "ssh_command_timeout", 15),
        "ssh_retries": _non_negative_int(config, "ssh_retries", 0),
        "ssh_retry_backoff_ms": _non_negative_int(config, "ssh_retry_backoff_ms", 250),
        "dashboard_workers": _positive_int(config, "dashboard_workers", 6),
        "host_key_policy": _host_key_policy(config),
        "known_hosts_file": str(config.get("known_hosts_file", "~/.ssh/known_hosts")),
    }


def render_index_html(active_view: str = "dashboard") -> str:
    view = str(active_view or "dashboard").strip().lower()
    if view not in INDEX_VIEWS:
        view = "dashboard"

    html = INDEX_HTML
    for item in INDEX_VIEWS:
        active = " active" if item == view else ""
        html = html.replace(
            f'<div class="page-view" id="view-{item}">',
            f'<div class="page-view{active}" id="view-{item}">',
        )
        html = html.replace(
            f'<div class="page-view active" id="view-{item}">',
            f'<div class="page-view{active}" id="view-{item}">',
        )
        html = html.replace(
            f'<button class="tab-button" type="button" data-view-button="{item}">',
            f'<button class="tab-button{active}" type="button" data-view-button="{item}">',
        )
        html = html.replace(
            f'<button class="tab-button active" type="button" data-view-button="{item}">',
            f'<button class="tab-button{active}" type="button" data-view-button="{item}">',
        )
    return html


def extract_token(handler: BaseHTTPRequestHandler) -> str | None:
    auth = handler.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    query = parse_qs(urlparse(handler.path).query)
    query_token = query.get("token", [None])[0]
    if query_token:
        return query_token
    header_token = handler.headers.get("X-ClawDone-Token")
    if header_token:
        return header_token.strip()
    return None


def extract_share_token(handler: BaseHTTPRequestHandler) -> str | None:
    query = parse_qs(urlparse(handler.path).query)
    query_token = query.get("share_token", [None])[0]
    if query_token:
        return str(query_token).strip()
    header_token = handler.headers.get("X-ClawDone-Share-Token")
    if header_token:
        return header_token.strip()
    return None


def is_authorized(handler: BaseHTTPRequestHandler, config: dict[str, Any]) -> bool:
    token = extract_token(handler)
    rbac_tokens = config.get("rbac_tokens", {}) or {}
    if isinstance(rbac_tokens, dict) and rbac_tokens:
        return bool(token and token in rbac_tokens)
    configured = config.get("token")
    if not configured:
        return True
    return token == configured


class ClawDoneApp:
    def __init__(
        self,
        config: dict[str, Any],
        tmux_client: TmuxClient | None = None,
        store: ProfileStore | None = None,
        remote_tmux: RemoteTmuxClient | None = None,
    ):
        self.config = normalize_config(config)
        self.tmux = tmux_client or TmuxClient(tmux_bin=self.config["tmux_bin"])
        self.store = store or ProfileStore(self.config["store_path"])
        if remote_tmux is None:
            ssh_executor = SSHExecutor(
                connect_timeout=self.config["ssh_timeout"],
                command_timeout=self.config["ssh_command_timeout"],
                retries=self.config["ssh_retries"],
                retry_backoff_ms=self.config["ssh_retry_backoff_ms"],
                host_key_policy=self.config["host_key_policy"],
                known_hosts_file=self.config["known_hosts_file"],
            )
            remote_tmux = RemoteTmuxClient(executor=ssh_executor, dashboard_workers=self.config["dashboard_workers"])
        self.remote_tmux = remote_tmux
        if self.config["default_role"] not in ROLE_LEVELS:
            self.config["default_role"] = "admin"

    def json_response(self, handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(data)))
        handler.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        handler.send_header("Pragma", "no-cache")
        handler.send_header("Expires", "0")
        handler.end_headers()
        handler.wfile.write(data)

    def html_response(self, handler: BaseHTTPRequestHandler, html: str) -> None:
        data = html.encode("utf-8")
        handler.send_response(HTTPStatus.OK)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.send_header("Content-Length", str(len(data)))
        handler.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        handler.send_header("Pragma", "no-cache")
        handler.send_header("Expires", "0")
        handler.end_headers()
        handler.wfile.write(data)

    def binary_response(self, handler: BaseHTTPRequestHandler, status: int, payload: bytes, content_type: str) -> None:
        handler.send_response(status)
        handler.send_header("Content-Type", content_type)
        handler.send_header("Content-Length", str(len(payload)))
        handler.send_header("Cache-Control", "public, max-age=3600")
        handler.end_headers()
        handler.wfile.write(payload)

    def read_json(self, handler: BaseHTTPRequestHandler) -> dict[str, Any]:
        length = int(handler.headers.get("Content-Length", "0"))
        raw = handler.rfile.read(length) if length > 0 else b"{}"
        try:
            decoded = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError("invalid JSON request body") from exc
        if not isinstance(decoded, dict):
            raise ValueError("JSON body must be an object")
        return decoded

    def request_identity(self, handler: BaseHTTPRequestHandler) -> dict[str, Any] | None:
        token = extract_token(handler)
        rbac_tokens = self.config.get("rbac_tokens", {}) or {}
        if isinstance(rbac_tokens, dict) and rbac_tokens:
            role = str(rbac_tokens.get(token or "", "")).strip().lower()
            if role in ROLE_LEVELS:
                return {"auth": "token", "token": token, "role": role, "share": None}
        else:
            configured_token = self.config.get("token")
            if configured_token:
                if token == configured_token:
                    return {"auth": "token", "token": token, "role": self.config.get("default_role", "admin"), "share": None}
            else:
                # Open mode: no token configured.
                return {"auth": "open", "token": None, "role": self.config.get("default_role", "admin"), "share": None}

        share_token = extract_share_token(handler)
        if share_token:
            try:
                share = self.store.resolve_session_share(share_token)
            except (ValueError, RuntimeError):
                return None
            role = "operator" if share.get("permission") == "control" else "viewer"
            return {"auth": "share", "token": share_token, "role": role, "share": share}
        return None

    def require_auth(self, handler: BaseHTTPRequestHandler) -> bool:
        identity = self.request_identity(handler)
        if identity is None:
            self.json_response(handler, HTTPStatus.UNAUTHORIZED, {"error": "invalid or missing token"})
            return False
        setattr(handler, "_clawdone_identity", identity)
        return True

    def identity(self, handler: BaseHTTPRequestHandler) -> dict[str, Any]:
        identity = getattr(handler, "_clawdone_identity", None)
        if isinstance(identity, dict):
            return identity
        fallback = {"auth": "token", "role": "admin", "share": None}
        setattr(handler, "_clawdone_identity", fallback)
        return fallback

    def require_role(self, handler: BaseHTTPRequestHandler, role: str) -> bool:
        identity = self.identity(handler)
        current = str(identity.get("role", "viewer")).strip().lower()
        if ROLE_LEVELS.get(current, 0) >= ROLE_LEVELS.get(role, 0):
            return True
        self.json_response(handler, HTTPStatus.FORBIDDEN, {"error": f"insufficient role, requires {role}"})
        return False

    def require_share_scope(self, handler: BaseHTTPRequestHandler, profile: str, target: str) -> bool:
        identity = self.identity(handler)
        share = identity.get("share")
        if not isinstance(share, dict):
            return True
        share_profile = str(share.get("profile", "")).strip()
        share_target = str(share.get("target", "")).strip()
        if share_profile and profile and profile != share_profile:
            self.json_response(handler, HTTPStatus.FORBIDDEN, {"error": "share token profile scope mismatch"})
            return False
        if share_target and target and target != share_target:
            self.json_response(handler, HTTPStatus.FORBIDDEN, {"error": "share token target scope mismatch"})
            return False
        return True

    def request_actor(self, handler: BaseHTTPRequestHandler) -> str:
        actor = str(handler.headers.get("X-ClawDone-Actor", "")).strip()
        if actor:
            return actor
        identity = self.identity(handler)
        if identity.get("auth") == "share":
            return "shared-user"
        return "mobile-user"

    def evaluate_command_risk(self, command: str) -> dict[str, Any]:
        cleaned = str(command or "").strip()
        lowered = cleaned.lower()
        level = "low"
        matched: list[str] = []
        for pattern in RISK_HIGH_PATTERNS:
            if pattern.search(lowered):
                level = "high"
                matched.append(pattern.pattern)
        return {"level": level, "matched": matched}

    def enforce_command_risk(self, command: str, confirm_risk: bool) -> dict[str, Any]:
        risk = self.evaluate_command_risk(command)
        if risk["level"] != "high":
            return risk
        policy = self.config.get("risk_policy", "confirm")
        if policy == "allow":
            return risk
        if policy == "deny":
            raise ValueError("dangerous command blocked by risk policy (deny)")
        if not confirm_risk:
            raise ValueError("dangerous command requires confirm_risk=true")
        return risk

    def profile_from_body(self, body: dict[str, Any]) -> dict[str, Any]:
        return normalize_profile(body)

    def get_profile(self, name: str) -> dict[str, Any]:
        return self.store.get_profile(name)

    def list_profiles_payload(self) -> list[dict[str, Any]]:
        return [mask_profile(profile) for profile in self.store.list_profiles()]

    def dashboard_payload(self) -> dict[str, Any]:
        profiles = self.store.list_profiles()
        aliases = {profile["name"]: self.store.aliases_for(profile["name"]) for profile in profiles}
        dashboard = self.remote_tmux.dashboard(profiles, aliases_by_profile=aliases)
        todo_summaries = self.store.todo_summary()
        summary_by_profile: dict[str, list[dict[str, Any]]] = {}
        for summary in todo_summaries:
            summary_by_profile.setdefault(str(summary.get("profile", "")), []).append(summary)

        for target in dashboard.get("targets", []):
            profile_summaries = summary_by_profile.get(str(target.get("name", "")), [])
            in_progress_count = sum(int(item.get("in_progress_count", 0)) for item in profile_summaries)
            sorted_summaries = sorted(profile_summaries, key=lambda item: str(item.get("last_updated_at", "")), reverse=True)
            latest = sorted_summaries[0] if sorted_summaries else None
            target["todo_summary"] = {
                "agent_count": len(profile_summaries),
                "in_progress_count": in_progress_count,
                "last_updated_at": latest.get("last_updated_at", "") if latest else "",
                "last_note": latest.get("last_note", "") if latest else "",
                "last_title": latest.get("last_title", "") if latest else "",
                "last_target": latest.get("target", "") if latest else "",
            }
            target["workflow_metrics"] = self.store.workflow_metrics(profile_name=str(target.get("name", "")), window_days=30)
        return {
            **dashboard,
            "profile_count": len(profiles),
            "online_count": sum(1 for target in dashboard["targets"] if target.get("online")),
            "workflow_metrics": self.store.workflow_metrics(window_days=30),
        }

    def record_audit_safe(self, payload: dict[str, Any]) -> None:
        try:
            self.store.record_audit(payload)
        except Exception:
            return

    def stream_todos(self, handler: BaseHTTPRequestHandler, profile_name: str, target: str, interval_sec: float) -> None:
        if not profile_name:
            raise ValueError("profile is required")
        if not target:
            raise ValueError("target is required")
        interval = max(1.0, min(interval_sec, 30.0))

        handler.send_response(HTTPStatus.OK)
        handler.send_header("Content-Type", "text/event-stream; charset=utf-8")
        handler.send_header("Cache-Control", "no-cache")
        handler.send_header("Connection", "keep-alive")
        handler.end_headers()

        last_payload = ""
        # Bound stream duration so handlers can be recycled by clients.
        for _ in range(300):
            payload = json.dumps(
                {"todos": self.store.list_todos(profile_name=profile_name, target=target)},
                ensure_ascii=False,
            )
            try:
                if payload != last_payload:
                    handler.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                    last_payload = payload
                else:
                    handler.wfile.write(b": keepalive\n\n")
                handler.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                break
            time.sleep(interval)

    def stream_terminal(
        self,
        handler: BaseHTTPRequestHandler,
        profile_name: str,
        target: str,
        lines: int,
        interval_sec: float,
    ) -> None:
        if not profile_name:
            raise ValueError("profile is required")
        if not target:
            raise ValueError("target is required")
        profile = self.get_profile(profile_name)
        interval = max(1.0, min(interval_sec, 10.0))
        max_lines = max(20, min(int(lines), 1000))

        handler.send_response(HTTPStatus.OK)
        handler.send_header("Content-Type", "text/event-stream; charset=utf-8")
        handler.send_header("Cache-Control", "no-cache")
        handler.send_header("Connection", "keep-alive")
        handler.end_headers()

        last_payload = ""
        for _ in range(300):
            output = self.remote_tmux.capture_pane(profile, target=target, lines=max_lines)
            payload = json.dumps({"profile": profile_name, "target": target, "output": output}, ensure_ascii=False)
            try:
                if payload != last_payload:
                    handler.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                    last_payload = payload
                else:
                    handler.wfile.write(b": keepalive\n\n")
                handler.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                break
            time.sleep(interval)

    def handle_get(self, handler: BaseHTTPRequestHandler) -> None:
        parsed = urlparse(handler.path)
        if parsed.path == "/":
            requested_view = str(parse_qs(parsed.query).get("view", ["dashboard"])[0]).strip().lower()
            self.html_response(handler, render_index_html(requested_view))
            return
        if parsed.path == "/assets/logo.png":
            logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
            if not logo_path.exists():
                self.json_response(handler, HTTPStatus.NOT_FOUND, {"error": "logo not found"})
                return
            self.binary_response(handler, HTTPStatus.OK, logo_path.read_bytes(), "image/png")
            return
        if not self.require_auth(handler):
            return

        identity = self.identity(handler)
        query = parse_qs(parsed.query)

        if parsed.path == "/api/health":
            self.json_response(
                handler,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "ssh_backend_available": PARAMIKO_AVAILABLE,
                    "profile_count": len(self.store.list_profiles()),
                    "template_count": len(self.store.list_templates()),
                    "host_key_policy": self.config["host_key_policy"],
                    "dashboard_workers": self.config["dashboard_workers"],
                    "risk_policy": self.config["risk_policy"],
                    "role": identity.get("role", "viewer"),
                },
            )
            return

        if parsed.path == "/api/profiles":
            if identity.get("auth") == "share":
                self.json_response(handler, HTTPStatus.FORBIDDEN, {"error": "share token cannot list all profiles"})
                return
            self.json_response(handler, HTTPStatus.OK, {"profiles": self.list_profiles_payload()})
            return

        if parsed.path == "/api/dashboard":
            if identity.get("auth") == "share":
                share = identity.get("share") or {}
                profile_name = str(share.get("profile", "")).strip()
                if not profile_name:
                    self.json_response(handler, HTTPStatus.FORBIDDEN, {"error": "share token missing profile scope"})
                    return
                dashboard = self.dashboard_payload()
                dashboard["targets"] = [item for item in dashboard.get("targets", []) if item.get("name") == profile_name]
                dashboard["profile_count"] = len(dashboard["targets"])
                dashboard["online_count"] = sum(1 for item in dashboard["targets"] if item.get("online"))
                self.json_response(handler, HTTPStatus.OK, dashboard)
                return
            self.json_response(handler, HTTPStatus.OK, self.dashboard_payload())
            return

        if parsed.path == "/api/connections/hub":
            dashboard = self.dashboard_payload()
            groups: dict[str, list[dict[str, Any]]] = {}
            for target in dashboard.get("targets", []):
                groups.setdefault(str(target.get("group", "General")), []).append(target)
            self.json_response(handler, HTTPStatus.OK, {"groups": groups, "total": len(dashboard.get("targets", []))})
            return

        if parsed.path == "/api/templates":
            profile_name = str(query.get("profile", [""])[0]).strip()
            if not self.require_share_scope(handler, profile_name, ""):
                return
            self.json_response(handler, HTTPStatus.OK, {"templates": self.store.list_templates(profile_name=profile_name)})
            return

        if parsed.path == "/api/history":
            profile_name = str(query.get("profile", [""])[0]).strip()
            if not self.require_share_scope(handler, profile_name, ""):
                return
            limit_text = str(query.get("limit", ["20"])[0]).strip() or "20"
            try:
                limit = int(limit_text)
            except ValueError as exc:
                raise ValueError("limit must be an integer") from exc
            self.json_response(handler, HTTPStatus.OK, {"history": self.store.list_history(profile_name=profile_name, limit=limit)})
            return

        if parsed.path == "/api/todos":
            profile_name = str(query.get("profile", [""])[0]).strip()
            target = str(query.get("target", [""])[0]).strip()
            status = str(query.get("status", [""])[0]).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            self.json_response(
                handler,
                HTTPStatus.OK,
                {"todos": self.store.list_todos(profile_name=profile_name, target=target, status=status)},
            )
            return

        if parsed.path == "/api/todos/summary":
            profile_name = str(query.get("profile", [""])[0]).strip()
            target = str(query.get("target", [""])[0]).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            self.json_response(
                handler,
                HTTPStatus.OK,
                {"summaries": self.store.todo_summary(profile_name=profile_name, target=target)},
            )
            return

        if parsed.path == "/api/workflow/metrics":
            profile_name = str(query.get("profile", [""])[0]).strip()
            target = str(query.get("target", [""])[0]).strip()
            days_text = str(query.get("days", ["30"])[0]).strip() or "30"
            if not self.require_share_scope(handler, profile_name, target):
                return
            try:
                days = int(days_text)
            except ValueError as exc:
                raise ValueError("days must be an integer") from exc
            self.json_response(
                handler,
                HTTPStatus.OK,
                {"metrics": self.store.workflow_metrics(profile_name=profile_name, target=target, window_days=days)},
            )
            return

        if parsed.path == "/api/todo-templates":
            profile_name = str(query.get("profile", [""])[0]).strip()
            target = str(query.get("target", [""])[0]).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            self.json_response(
                handler,
                HTTPStatus.OK,
                {"templates": self.store.list_todo_templates(profile_name=profile_name, target=target)},
            )
            return

        if parsed.path == "/api/workspace-templates":
            profile_name = str(query.get("profile", [""])[0]).strip()
            target = str(query.get("target", [""])[0]).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            self.json_response(
                handler,
                HTTPStatus.OK,
                {"templates": self.store.list_workspace_templates(profile_name=profile_name, target=target)},
            )
            return

        if parsed.path == "/api/audit":
            profile_name = str(query.get("profile", [""])[0]).strip()
            target = str(query.get("target", [""])[0]).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            limit_text = str(query.get("limit", ["100"])[0]).strip() or "100"
            try:
                limit = int(limit_text)
            except ValueError as exc:
                raise ValueError("limit must be an integer") from exc
            self.json_response(
                handler,
                HTTPStatus.OK,
                {"logs": self.store.list_audit_logs(profile_name=profile_name, target=target, limit=limit)},
            )
            return

        if parsed.path == "/api/events":
            profile_name = str(query.get("profile", [""])[0]).strip()
            target = str(query.get("target", [""])[0]).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            limit_text = str(query.get("limit", ["200"])[0]).strip() or "200"
            try:
                limit = int(limit_text)
            except ValueError as exc:
                raise ValueError("limit must be an integer") from exc
            self.json_response(
                handler,
                HTTPStatus.OK,
                {"events": self.store.list_events(profile_name=profile_name, target=target, limit=limit)},
            )
            return

        if parsed.path == "/api/todos/stream":
            profile_name = str(query.get("profile", [""])[0]).strip()
            target = str(query.get("target", [""])[0]).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            interval_text = str(query.get("interval", ["3"])[0]).strip() or "3"
            try:
                interval = float(interval_text)
            except ValueError as exc:
                raise ValueError("interval must be a number") from exc
            self.stream_todos(handler, profile_name=profile_name, target=target, interval_sec=interval)
            return

        if parsed.path == "/api/terminal/stream":
            profile_name = str(query.get("profile", [""])[0]).strip()
            target = str(query.get("target", [""])[0]).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            lines_text = str(query.get("lines", ["120"])[0]).strip() or "120"
            interval_text = str(query.get("interval", ["2"])[0]).strip() or "2"
            try:
                lines = int(lines_text)
            except ValueError as exc:
                raise ValueError("lines must be an integer") from exc
            try:
                interval = float(interval_text)
            except ValueError as exc:
                raise ValueError("interval must be a number") from exc
            self.stream_terminal(handler, profile_name=profile_name, target=target, lines=lines, interval_sec=interval)
            return

        if parsed.path == "/api/terminal/ws":
            self.json_response(
                handler,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "mode": "sse-fallback",
                    "stream_endpoint": "/api/terminal/stream",
                    "input_endpoint": "/api/terminal/input",
                    "heartbeat_seconds": 2,
                },
            )
            return

        if parsed.path == "/api/session-shares":
            profile_name = str(query.get("profile", [""])[0]).strip()
            target = str(query.get("target", [""])[0]).strip()
            include_expired = str(query.get("include_expired", ["0"])[0]).strip() in {"1", "true", "yes"}
            if not self.require_share_scope(handler, profile_name, target):
                return
            self.json_response(
                handler,
                HTTPStatus.OK,
                {"shares": self.store.list_session_shares(profile_name=profile_name, target=target, include_expired=include_expired)},
            )
            return

        if parsed.path == "/api/workflows":
            workflow_id = str(query.get("workflow_id", [""])[0]).strip()
            todos = self.store.list_workflow_todos(workflow_id)
            self.json_response(handler, HTTPStatus.OK, {"workflow_id": workflow_id, "todos": todos})
            return

        if parsed.path == "/api/remote/state":
            profile_name = str(query.get("profile", [""])[0]).strip()
            if not self.require_share_scope(handler, profile_name, ""):
                return
            profile = self.get_profile(profile_name)
            payload = self.remote_tmux.snapshot(profile, aliases=self.store.aliases_for(profile_name))
            self.json_response(handler, HTTPStatus.OK, payload)
            return

        if parsed.path == "/api/pane":
            profile_name = str(query.get("profile", [""])[0]).strip()
            target = str(query.get("target", [""])[0]).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            lines_text = str(query.get("lines", ["120"])[0]).strip() or "120"
            try:
                lines = int(lines_text)
            except ValueError as exc:
                raise ValueError("lines must be an integer") from exc
            profile = self.get_profile(profile_name)
            output = self.remote_tmux.capture_pane(profile, target=target, lines=lines)
            self.json_response(handler, HTTPStatus.OK, {"profile": profile_name, "target": target, "output": output})
            return

        self.json_response(handler, HTTPStatus.NOT_FOUND, {"error": "not found"})

    def handle_post(self, handler: BaseHTTPRequestHandler) -> None:
        parsed = urlparse(handler.path)
        if not self.require_auth(handler):
            return
        body = self.read_json(handler)
        actor = self.request_actor(handler)

        if parsed.path == "/api/profiles/save":
            if not self.require_role(handler, "admin"):
                return
            profile = self.profile_from_body(body)
            saved = self.store.save_profile(profile)
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "profile": mask_profile(saved)})
            return

        if parsed.path == "/api/profiles/delete":
            if not self.require_role(handler, "admin"):
                return
            name = str(body.get("name", "")).strip()
            self.store.delete_profile(name)
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "name": name})
            return

        if parsed.path == "/api/profiles/test":
            if not self.require_role(handler, "operator"):
                return
            profile = self.profile_from_body(body)
            if not self.require_share_scope(handler, profile.get("name", ""), ""):
                return
            self.json_response(handler, HTTPStatus.OK, self.remote_tmux.test_connection(profile))
            return

        if parsed.path == "/api/alias/save":
            if not self.require_role(handler, "operator"):
                return
            profile_name = str(body.get("profile", "")).strip()
            target = str(body.get("target", "")).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            alias = str(body.get("alias", ""))
            self.store.set_alias(profile_name, target, alias)
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "profile": profile_name, "target": target, "alias": alias.strip()})
            return

        if parsed.path == "/api/templates/save":
            if not self.require_role(handler, "operator"):
                return
            profile_name = str(body.get("profile", "")).strip()
            if not self.require_share_scope(handler, profile_name, ""):
                return
            template = self.store.save_template(body)
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "template": template})
            return

        if parsed.path == "/api/templates/delete":
            if not self.require_role(handler, "operator"):
                return
            template_id = str(body.get("id", "")).strip()
            self.store.delete_template(template_id)
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "id": template_id})
            return

        if parsed.path == "/api/history/clear":
            if not self.require_role(handler, "operator"):
                return
            profile_name = str(body.get("profile", "")).strip()
            if not self.require_share_scope(handler, profile_name, ""):
                return
            self.store.clear_history(profile_name=profile_name)
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "profile": profile_name})
            return

        if parsed.path == "/api/todos/quick":
            if not self.require_role(handler, "operator"):
                return
            profile_name = str(body.get("profile", "")).strip()
            target = str(body.get("target", "")).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            todo = self.store.quick_create_todo(body)
            self.record_audit_safe(
                {
                    "action": "todo.quick_create",
                    "profile": todo["profile"],
                    "target": todo["target"],
                    "alias": todo.get("alias", ""),
                    "todo_id": todo["id"],
                    "status": todo["status"],
                    "note": todo.get("title", ""),
                    "actor": actor,
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "todo": todo})
            return

        if parsed.path == "/api/workflows/triplet":
            if not self.require_role(handler, "operator"):
                return
            profile_name = str(body.get("profile", "")).strip()
            target = str(body.get("target", "")).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            workflow = self.store.create_workflow_triplet(body)
            self.record_audit_safe(
                {
                    "action": "workflow.triplet.create",
                    "profile": profile_name,
                    "target": target,
                    "note": str(body.get("title", "")).strip(),
                    "actor": actor,
                    "payload": {"workflow_id": workflow["workflow_id"]},
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, **workflow})
            return

        if parsed.path == "/api/todos":
            if not self.require_role(handler, "operator"):
                return
            profile_name = str(body.get("profile", "")).strip()
            target = str(body.get("target", "")).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            todo = self.store.save_todo(body)
            self.record_audit_safe(
                {
                    "action": "todo.create",
                    "profile": todo["profile"],
                    "target": todo["target"],
                    "alias": todo.get("alias", ""),
                    "todo_id": todo["id"],
                    "status": todo["status"],
                    "note": todo.get("title", ""),
                    "actor": actor,
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "todo": todo})
            return

        if parsed.path == "/api/todos/delete":
            if not self.require_role(handler, "operator"):
                return
            todo_id = str(body.get("id", "")).strip()
            todo = self.store.get_todo(todo_id)
            if not self.require_share_scope(handler, todo.get("profile", ""), todo.get("target", "")):
                return
            self.store.delete_todo(todo_id)
            self.record_audit_safe(
                {
                    "action": "todo.delete",
                    "profile": todo["profile"],
                    "target": todo["target"],
                    "alias": todo.get("alias", ""),
                    "todo_id": todo_id,
                    "status": todo.get("status", ""),
                    "note": todo.get("title", ""),
                    "actor": actor,
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "id": todo_id})
            return

        if parsed.path == "/api/todos/status":
            if not self.require_role(handler, "operator"):
                return
            todo_id = str(body.get("todo_id", "")).strip()
            status = str(body.get("status", "")).strip()
            progress_note = str(body.get("progress_note", ""))
            request_actor = str(body.get("actor", "")).strip() or actor
            current_todo = self.store.get_todo(todo_id)
            if not self.require_share_scope(handler, current_todo.get("profile", ""), current_todo.get("target", "")):
                return
            todo = self.store.update_todo_status(todo_id=todo_id, status=status, progress_note=progress_note, actor=request_actor)
            self.record_audit_safe(
                {
                    "action": "todo.status",
                    "profile": todo["profile"],
                    "target": todo["target"],
                    "alias": todo.get("alias", ""),
                    "todo_id": todo["id"],
                    "status": todo["status"],
                    "note": progress_note.strip(),
                    "actor": request_actor,
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "todo": todo})
            return

        if parsed.path == "/api/todos/evidence":
            if not self.require_role(handler, "operator"):
                return
            todo_id = str(body.get("todo_id", "")).strip()
            request_actor = str(body.get("actor", "")).strip() or actor
            evidence = body.get("evidence")
            if evidence in (None, "", []):
                raise ValueError("todo evidence is required")
            scoped_todo = self.store.get_todo(todo_id)
            if not self.require_share_scope(handler, scoped_todo.get("profile", ""), scoped_todo.get("target", "")):
                return
            if isinstance(evidence, list):
                if not evidence:
                    raise ValueError("todo evidence is required")
                todo = self.store.get_todo(todo_id)
                for item in evidence:
                    todo = self.store.append_todo_evidence(todo["id"], item, actor=request_actor)
            else:
                todo = self.store.append_todo_evidence(todo_id, evidence, actor=request_actor)
            self.record_audit_safe(
                {
                    "action": "todo.evidence",
                    "profile": todo["profile"],
                    "target": todo["target"],
                    "alias": todo.get("alias", ""),
                    "todo_id": todo["id"],
                    "status": todo["status"],
                    "note": "evidence added",
                    "actor": request_actor,
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "todo": todo})
            return

        if parsed.path == "/api/todos/report":
            if not self.require_role(handler, "operator"):
                return
            todo_id = str(body.get("todo_id", "")).strip()
            if not todo_id:
                raise ValueError("todo_id is required")
            request_actor = str(body.get("actor", "agent")).strip() or "agent"
            status = str(body.get("status", "")).strip()
            progress_note = str(body.get("progress_note", ""))
            evidence = body.get("evidence")

            updated = self.store.get_todo(todo_id)
            if not self.require_share_scope(handler, updated.get("profile", ""), updated.get("target", "")):
                return
            # If report requests done/verified, append evidence first so DoD constraints are satisfiable.
            if status.strip().lower() in {"done", "verified"} and evidence not in (None, "", []):
                if isinstance(evidence, list):
                    for item in evidence:
                        updated = self.store.append_todo_evidence(updated["id"], item, actor=request_actor)
                else:
                    updated = self.store.append_todo_evidence(updated["id"], evidence, actor=request_actor)
                evidence = None
            if status:
                updated = self.store.update_todo_status(
                    todo_id=todo_id,
                    status=status,
                    progress_note=progress_note,
                    actor=request_actor,
                )
            elif progress_note.strip():
                event = {
                    "type": "status",
                    "status": updated.get("status", ""),
                    "note": progress_note.strip(),
                    "actor": request_actor,
                    "created_at": "",
                }
                updated["events"] = [event, *(updated.get("events", []) or [])]
                updated["progress_note"] = progress_note.strip()
                updated = self.store.save_todo(updated)

            if evidence not in (None, "", []):
                if isinstance(evidence, list):
                    for item in evidence:
                        updated = self.store.append_todo_evidence(updated["id"], item, actor=request_actor)
                else:
                    updated = self.store.append_todo_evidence(updated["id"], evidence, actor=request_actor)

            self.record_audit_safe(
                {
                    "action": "todo.report",
                    "profile": updated["profile"],
                    "target": updated["target"],
                    "alias": updated.get("alias", ""),
                    "todo_id": updated["id"],
                    "status": updated["status"],
                    "note": progress_note.strip(),
                    "actor": request_actor,
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "todo": updated})
            return

        if parsed.path == "/api/todo-templates/save":
            if not self.require_role(handler, "operator"):
                return
            if not self.require_share_scope(
                handler,
                str(body.get("profile", "")).strip(),
                str(body.get("target", "")).strip(),
            ):
                return
            template = self.store.save_todo_template(body)
            self.record_audit_safe(
                {
                    "action": "todo_template.save",
                    "profile": template.get("profile", ""),
                    "target": template.get("target", ""),
                    "note": template.get("name", ""),
                    "actor": actor,
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "template": template})
            return

        if parsed.path == "/api/todo-templates/delete":
            if not self.require_role(handler, "operator"):
                return
            template_id = str(body.get("id", "")).strip()
            self.store.delete_todo_template(template_id)
            self.record_audit_safe({"action": "todo_template.delete", "note": template_id, "actor": actor})
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "id": template_id})
            return

        if parsed.path == "/api/workspace-templates/save":
            if not self.require_role(handler, "operator"):
                return
            profile_name = str(body.get("profile", "")).strip()
            target = str(body.get("target", "")).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            template = self.store.save_workspace_template(body)
            self.record_audit_safe(
                {
                    "action": "workspace_template.save",
                    "profile": template.get("profile", ""),
                    "target": template.get("target", ""),
                    "note": template.get("name", ""),
                    "actor": actor,
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "template": template})
            return

        if parsed.path == "/api/workspace-templates/delete":
            if not self.require_role(handler, "operator"):
                return
            template_id = str(body.get("id", "")).strip()
            self.store.delete_workspace_template(template_id)
            self.record_audit_safe({"action": "workspace_template.delete", "note": template_id, "actor": actor})
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "id": template_id})
            return

        if parsed.path == "/api/session-shares/create":
            if not self.require_role(handler, "admin"):
                return
            share = self.store.create_session_share({**body, "created_by": actor})
            self.record_audit_safe(
                {
                    "action": "session_share.create",
                    "profile": share.get("profile", ""),
                    "target": share.get("target", ""),
                    "note": share.get("permission", ""),
                    "actor": actor,
                    "payload": {"share_id": share["id"]},
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "share": share})
            return

        if parsed.path == "/api/session-shares/revoke":
            if not self.require_role(handler, "admin"):
                return
            share_id = str(body.get("id", "")).strip()
            token = str(body.get("token", "")).strip()
            revoked = self.store.revoke_session_share(share_id=share_id, token=token)
            self.record_audit_safe(
                {
                    "action": "session_share.revoke",
                    "profile": revoked.get("profile", ""),
                    "target": revoked.get("target", ""),
                    "note": revoked.get("id", ""),
                    "actor": actor,
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "share": revoked})
            return

        if parsed.path == "/api/profiles/batch-test":
            if not self.require_role(handler, "operator"):
                return
            names = body.get("names", [])
            if not isinstance(names, list) or not names:
                raise ValueError("names must be a non-empty array")
            results: list[dict[str, Any]] = []
            for item in names:
                profile_name = str(item).strip()
                if not profile_name:
                    continue
                if not self.require_share_scope(handler, profile_name, ""):
                    return
                profile = self.get_profile(profile_name)
                test_result = self.remote_tmux.test_connection(profile)
                results.append({"profile": profile_name, **test_result})
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "results": results})
            return

        if parsed.path == "/api/send":
            if not self.require_role(handler, "operator"):
                return
            profile_name = str(body.get("profile", "")).strip()
            target = str(body.get("target", "")).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            command = str(body.get("command", ""))
            cleaned_command = command.strip()
            if not cleaned_command:
                raise ValueError("command is required")
            press_enter = bool(body.get("press_enter", True))
            confirm_risk = bool(body.get("confirm_risk", False))
            risk = self.enforce_command_risk(cleaned_command, confirm_risk=confirm_risk)
            profile = self.get_profile(profile_name)
            alias = self.store.aliases_for(profile_name).get(target, "")
            self.store.record_history({"profile": profile_name, "target": target, "alias": alias, "command": cleaned_command})
            self.remote_tmux.send_keys(profile, target=target, command=cleaned_command, press_enter=press_enter)
            expected_target = str(body.get("expected_target", "")).strip()
            misroute = bool(expected_target and expected_target != target)
            self.record_audit_safe(
                {
                    "action": "agent.send",
                    "profile": profile_name,
                    "target": target,
                    "alias": alias,
                    "note": cleaned_command[:200],
                    "actor": actor,
                    "payload": {"risk": risk, "misroute": misroute},
                }
            )
            self.json_response(
                handler,
                HTTPStatus.OK,
                {"ok": True, "profile": profile_name, "target": target, "alias": alias, "risk": risk, "misroute": misroute},
            )
            return

        if parsed.path == "/api/send/batch":
            if not self.require_role(handler, "operator"):
                return
            profile_name = str(body.get("profile", "")).strip()
            targets = body.get("targets", [])
            command = str(body.get("command", "")).strip()
            if not profile_name:
                raise ValueError("profile is required")
            if not isinstance(targets, list) or not targets:
                raise ValueError("targets must be a non-empty array")
            if not command:
                raise ValueError("command is required")
            confirm_risk = bool(body.get("confirm_risk", False))
            risk = self.enforce_command_risk(command, confirm_risk=confirm_risk)
            profile = self.get_profile(profile_name)
            press_enter = bool(body.get("press_enter", True))
            sent: list[dict[str, Any]] = []
            for raw_target in targets:
                target = str(raw_target).strip()
                if not target:
                    continue
                if not self.require_share_scope(handler, profile_name, target):
                    return
                alias = self.store.aliases_for(profile_name).get(target, "")
                self.remote_tmux.send_keys(profile, target=target, command=command, press_enter=press_enter)
                self.store.record_history({"profile": profile_name, "target": target, "alias": alias, "command": command})
                sent.append({"target": target, "alias": alias})
            self.record_audit_safe(
                {
                    "action": "agent.send.batch",
                    "profile": profile_name,
                    "target": "",
                    "note": command[:200],
                    "actor": actor,
                    "payload": {"targets": [item["target"] for item in sent], "risk": risk},
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "profile": profile_name, "sent": sent, "risk": risk})
            return

        if parsed.path == "/api/terminal/input":
            if not self.require_role(handler, "operator"):
                return
            profile_name = str(body.get("profile", "")).strip()
            target = str(body.get("target", "")).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            command = str(body.get("command", "")).strip()
            if not command:
                raise ValueError("command is required")
            confirm_risk = bool(body.get("confirm_risk", False))
            risk = self.enforce_command_risk(command, confirm_risk=confirm_risk)
            press_enter = bool(body.get("press_enter", False))
            profile = self.get_profile(profile_name)
            self.remote_tmux.send_keys(profile, target=target, command=command, press_enter=press_enter)
            self.record_audit_safe(
                {
                    "action": "terminal.input",
                    "profile": profile_name,
                    "target": target,
                    "note": command[:200],
                    "actor": actor,
                    "payload": {"risk": risk, "press_enter": press_enter},
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "risk": risk})
            return

        if parsed.path == "/api/interrupt":
            if not self.require_role(handler, "operator"):
                return
            profile_name = str(body.get("profile", "")).strip()
            target = str(body.get("target", "")).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            profile = self.get_profile(profile_name)
            self.remote_tmux.interrupt(profile, target=target)
            alias = self.store.aliases_for(profile_name).get(target, "")
            self.record_audit_safe(
                {
                    "action": "agent.interrupt",
                    "profile": profile_name,
                    "target": target,
                    "alias": alias,
                    "actor": actor,
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "profile": profile_name, "target": target})
            return

        self.json_response(handler, HTTPStatus.NOT_FOUND, {"error": "not found"})


def build_handler(app: ClawDoneApp) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            try:
                app.handle_get(self)
            except (ValueError, RuntimeError) as exc:
                app.json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            except Exception as exc:  # pragma: no cover
                app.json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

        def do_POST(self) -> None:
            try:
                app.handle_post(self)
            except (ValueError, RuntimeError) as exc:
                app.json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            except Exception as exc:  # pragma: no cover
                app.json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def create_server(
    config: dict[str, Any],
    tmux_client: TmuxClient | None = None,
    store: ProfileStore | None = None,
    remote_tmux: RemoteTmuxClient | None = None,
) -> ThreadingHTTPServer:
    app = ClawDoneApp(config=config, tmux_client=tmux_client, store=store, remote_tmux=remote_tmux)
    return ThreadingHTTPServer((app.config["host"], app.config["port"]), build_handler(app))
