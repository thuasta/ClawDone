"""HTTP app and request handlers."""

from __future__ import annotations

import gzip
import json
import logging
import re
import threading
import time
from collections import OrderedDict
from pathlib import Path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from .html import INDEX_HTML
from .local_tmux import TmuxClient
from .remote import HOST_KEY_POLICIES, PARAMIKO_AVAILABLE, RemoteTmuxClient, SSHExecutor
from .store import ProfileStore, mask_profile, mask_supervisor_config, normalize_profile
from .supervisor import SupervisorClient
from .utils import extract_json_object

logger = logging.getLogger("clawdone")

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
AUTO_REPORT_PATTERN = re.compile(r"CLAWDONE_REPORT\s+(\{[^\r\n]*\})")
FINAL_TODO_STATUSES = {"done", "verified"}
READY_TODO_STATUSES = {"todo", "in_progress", "done"}


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
        "todo_autopilot": bool(config.get("todo_autopilot", True)),
        "todo_autopilot_interval_sec": _positive_int(config, "todo_autopilot_interval_sec", 3),
        "todo_autopilot_lines": _positive_int(config, "todo_autopilot_lines", 200),
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
        self.supervisor_client = SupervisorClient()
        self.todo_autopilot_enabled = bool(self.config.get("todo_autopilot", True))
        self.todo_autopilot_interval_sec = max(1.0, float(self.config.get("todo_autopilot_interval_sec", 3)))
        self.todo_autopilot_lines = max(40, int(self.config.get("todo_autopilot_lines", 200)))
        self._todo_autopilot_stop = threading.Event()
        self._todo_autopilot_thread: threading.Thread | None = None
        self._processed_report_keys: OrderedDict[str, None] = OrderedDict()
        self._todo_dispatch_lock = threading.Lock()
        if self.config["default_role"] not in ROLE_LEVELS:
            self.config["default_role"] = "admin"
        # Pre-compute HTML view variants and their gzipped forms at startup.
        self._html_cache: dict[str, str] = {}
        self._html_cache_gzipped: dict[str, bytes] = {}
        for view in INDEX_VIEWS:
            html = render_index_html(view)
            self._html_cache[view] = html
            self._html_cache_gzipped[view] = gzip.compress(html.encode("utf-8"))

    def _accepts_gzip(self, handler: BaseHTTPRequestHandler) -> bool:
        return "gzip" in handler.headers.get("Accept-Encoding", "")

    def json_response(self, handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        use_gzip = len(data) > 1024 and self._accepts_gzip(handler)
        if use_gzip:
            data = gzip.compress(data)
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(data)))
        if use_gzip:
            handler.send_header("Content-Encoding", "gzip")
        handler.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        handler.send_header("Pragma", "no-cache")
        handler.send_header("Expires", "0")
        handler.end_headers()
        handler.wfile.write(data)

    def html_response(self, handler: BaseHTTPRequestHandler, html: str, gzipped: bytes | None = None) -> None:
        if gzipped is not None and self._accepts_gzip(handler):
            data = gzipped
            handler.send_response(HTTPStatus.OK)
            handler.send_header("Content-Type", "text/html; charset=utf-8")
            handler.send_header("Content-Length", str(len(data)))
            handler.send_header("Content-Encoding", "gzip")
        else:
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
        aliases = self.store.all_aliases()
        dashboard = self.remote_tmux.dashboard(profiles, aliases_by_profile=aliases)
        todo_summaries = self.store.todo_summary()
        summary_by_profile: dict[str, list[dict[str, Any]]] = {}
        for summary in todo_summaries:
            summary_by_profile.setdefault(str(summary.get("profile", "")), []).append(summary)

        profile_names = [profile["name"] for profile in profiles]
        bulk_metrics = self.store.bulk_workflow_metrics(profile_names, window_days=30)

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
            target["workflow_metrics"] = bulk_metrics.get(str(target.get("name", "")), {})
        return {
            **dashboard,
            "profile_count": len(profiles),
            "online_count": sum(1 for target in dashboard["targets"] if target.get("online")),
            "workflow_metrics": bulk_metrics.get("", {}),
        }

    def record_audit_safe(self, payload: dict[str, Any]) -> None:
        try:
            self.store.record_audit(payload)
        except Exception:
            logger.debug("audit recording failed", exc_info=True)
            return

    def supervisor_config_payload(self, profile_name: str = "", config_id: str = "") -> dict[str, Any]:
        return mask_supervisor_config(self.store.get_supervisor_config(config_id=config_id, profile_name=profile_name))

    def require_supervisor_permission(self, config: dict[str, Any], permission: str) -> None:
        permissions = {str(item).strip().lower() for item in (config.get("permissions", []) or [])}
        if permission not in permissions:
            raise ValueError(f"supervisor permission denied for: {permission}")
        if not bool(config.get("enabled", True)):
            raise ValueError("supervisor config is disabled")

    def list_supervisor_candidates(self, profile_name: str) -> list[dict[str, Any]]:
        profile = self.get_profile(profile_name)
        aliases = self.store.aliases_for(profile_name)
        snapshot = self.remote_tmux.snapshot(profile, aliases=aliases)
        candidates: list[dict[str, Any]] = []
        for session in snapshot.get("sessions", []):
            if not isinstance(session, dict):
                continue
            for window in session.get("windows", []):
                if not isinstance(window, dict):
                    continue
                for pane in window.get("panes", []):
                    if not isinstance(pane, dict):
                        continue
                    target = str(pane.get("target", "")).strip()
                    if not target:
                        continue
                    candidates.append(
                        {
                            "target": target,
                            "alias": str(pane.get("alias", "")).strip(),
                            "session": str(session.get("name", "")).strip(),
                            "window_name": str(window.get("name", "")).strip(),
                            "window_index": str(window.get("index", "")).strip(),
                            "command": str(pane.get("current_command", "")).strip(),
                            "active": bool(pane.get("active", False)),
                        }
                    )
        return candidates

    def capture_todo_output(self, todo: dict[str, Any], lines: int = 200) -> str:
        profile_name = str(todo.get("profile", "")).strip()
        target = str(todo.get("target", "")).strip()
        if not profile_name or not target:
            return ""
        try:
            return self.capture_pane_with_reports(profile_name=profile_name, target=target, lines=lines)
        except Exception:
            return ""

    def active_supervisor_config(self, profile_name: str, permission: str = "", auto_flag: str = "") -> dict[str, Any] | None:
        try:
            config = self.store.get_supervisor_config(profile_name=profile_name)
        except RuntimeError:
            return None
        if not bool(config.get("enabled", True)):
            return None
        permissions = {str(item).strip().lower() for item in (config.get("permissions", []) or [])}
        if permission and permission not in permissions:
            return None
        if auto_flag and not bool(config.get(auto_flag, False)):
            return None
        return config

    def todo_has_recent_audit(self, todo: dict[str, Any], actions: set[str]) -> bool:
        todo_id = str(todo.get("id", "")).strip()
        if not todo_id:
            return False
        updated_at = str(todo.get("updated_at", "")).strip()
        logs = self.store.list_audit_logs(
            profile_name=str(todo.get("profile", "")).strip(),
            target=str(todo.get("target", "")).strip(),
            limit=200,
        )
        for entry in logs:
            if str(entry.get("todo_id", "")).strip() != todo_id:
                continue
            if str(entry.get("action", "")).strip() not in actions:
                continue
            if not updated_at or str(entry.get("created_at", "")).strip() >= updated_at:
                return True
        return False

    def supervisor_route_todo(self, todo: dict[str, Any] | str, actor: str = "supervisor", auto_send: bool = True) -> dict[str, Any]:
        current = self.store.get_todo(todo) if isinstance(todo, str) else self.store.get_todo(str(todo.get("id", "")))
        profile_name = str(current.get("profile", "")).strip()
        config = self.active_supervisor_config(profile_name, permission="dispatch", auto_flag="auto_dispatch")
        if config is None:
            return {"used_supervisor": False, "todo": current, "dispatch": self.auto_dispatch_todo(current, actor=actor if actor else "autopilot")}
        try:
            candidates = self.list_supervisor_candidates(profile_name)
            if not candidates:
                raise RuntimeError("no candidate agents available for supervisor routing")
            decision = self.supervisor_client.dispatch(config=config, todo=current, candidates=candidates)
            updated = current
            if decision.get("target") or decision.get("alias"):
                updated = self.store.save_todo(
                    {
                        **current,
                        "id": current["id"],
                        "target": str(decision.get("target", current.get("target", ""))).strip() or current.get("target", ""),
                        "alias": str(decision.get("alias", current.get("alias", ""))).strip(),
                    }
                )
            self.record_audit_safe(
                {
                    "action": "supervisor.auto_dispatch",
                    "profile": updated.get("profile", ""),
                    "target": updated.get("target", ""),
                    "alias": updated.get("alias", ""),
                    "todo_id": updated.get("id", ""),
                    "status": updated.get("status", ""),
                    "note": str(decision.get("reason", "")).strip(),
                    "actor": actor,
                    "payload": {"confidence": decision.get("confidence", 0)},
                }
            )
            dispatch = {"dispatched": False, "todo": updated}
            if auto_send and str(updated.get("status", "")).strip().lower() == "todo":
                dispatch = self.auto_dispatch_todo(updated, actor=actor)
                updated = dispatch.get("todo", updated)
            return {"used_supervisor": True, "decision": decision, "todo": updated, "dispatch": dispatch}
        except Exception as exc:
            self.record_audit_safe(
                {
                    "action": "supervisor.auto_dispatch_error",
                    "profile": current.get("profile", ""),
                    "target": current.get("target", ""),
                    "alias": current.get("alias", ""),
                    "todo_id": current.get("id", ""),
                    "status": current.get("status", ""),
                    "note": str(exc)[:200],
                    "actor": actor,
                }
            )
            return {"used_supervisor": True, "todo": current, "error": str(exc), "dispatch": {"dispatched": False, "todo": current}}

    def maybe_run_supervisor_review(self, todo: dict[str, Any] | str, actor: str = "supervisor") -> dict[str, Any] | None:
        current = self.store.get_todo(todo) if isinstance(todo, str) else self.store.get_todo(str(todo.get("id", "")))
        if str(current.get("status", "")).strip().lower() not in FINAL_TODO_STATUSES:
            return None
        profile_name = str(current.get("profile", "")).strip()
        config = self.active_supervisor_config(profile_name, permission="review", auto_flag="auto_review")
        if config is None:
            return None
        if self.todo_has_recent_audit(current, {"supervisor.auto_review", "supervisor.auto_accept"}):
            return None
        try:
            pane_output = self.capture_todo_output(current)
            review = self.supervisor_client.review(config=config, todo=current, pane_output=pane_output)
            self.record_audit_safe(
                {
                    "action": "supervisor.auto_review",
                    "profile": current.get("profile", ""),
                    "target": current.get("target", ""),
                    "alias": current.get("alias", ""),
                    "todo_id": current.get("id", ""),
                    "status": current.get("status", ""),
                    "note": review.get("summary", ""),
                    "actor": actor,
                    "payload": {"verdict": review.get("verdict", "needs_work")},
                }
            )
            verdict = str(review.get("verdict", "needs_work")).strip().lower()
            if verdict == "accept" and bool(config.get("auto_accept", True)) and self.active_supervisor_config(profile_name, permission="accept"):
                evidence = review.get("evidence", [])
                updated = current
                current_status = str(updated.get("status", "")).strip().lower()
                if current_status not in {"done", "verified"}:
                    updated = self.apply_todo_report(todo_id=updated["id"], status="done", progress_note=review.get("summary", ""), evidence=evidence, actor=actor)
                    evidence = []
                if str(updated.get("status", "")).strip().lower() != "verified":
                    updated = self.apply_todo_report(todo_id=updated["id"], status="verified", progress_note=review.get("summary", ""), evidence=evidence, actor=actor)
                self.record_audit_safe(
                    {
                        "action": "supervisor.auto_accept",
                        "profile": updated.get("profile", ""),
                        "target": updated.get("target", ""),
                        "alias": updated.get("alias", ""),
                        "todo_id": updated.get("id", ""),
                        "status": updated.get("status", ""),
                        "note": review.get("summary", ""),
                        "actor": actor,
                    }
                )
                return {"review": review, "todo": updated, "accepted": True}
            return {"review": review, "todo": current, "accepted": False}
        except Exception as exc:
            self.record_audit_safe(
                {
                    "action": "supervisor.auto_review_error",
                    "profile": current.get("profile", ""),
                    "target": current.get("target", ""),
                    "alias": current.get("alias", ""),
                    "todo_id": current.get("id", ""),
                    "status": current.get("status", ""),
                    "note": str(exc)[:200],
                    "actor": actor,
                }
            )
            return None

    def _build_recent_audit_set(self, actions: set[str]) -> set[str]:
        """Build a set of todo_ids that have recent audit entries for the given actions."""
        logs = self.store.list_audit_logs(limit=500)
        return {
            str(entry.get("todo_id", "")).strip()
            for entry in logs
            if str(entry.get("action", "")).strip() in actions
        }

    def process_supervisor_review_queue(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        reviewed_todo_ids = self._build_recent_audit_set({"supervisor.auto_review", "supervisor.auto_accept"})
        for todo in self.store.list_todos():
            if str(todo.get("status", "")).strip().lower() not in FINAL_TODO_STATUSES:
                continue
            todo_id = str(todo.get("id", "")).strip()
            if todo_id in reviewed_todo_ids:
                continue
            result = self.maybe_run_supervisor_review(todo, actor="supervisor")
            if result is not None:
                results.append(result)
        return results

    def start_background_tasks(self) -> None:
        if not self.todo_autopilot_enabled:
            return
        if self._todo_autopilot_thread and self._todo_autopilot_thread.is_alive():
            return
        self._todo_autopilot_stop.clear()
        self._todo_autopilot_thread = threading.Thread(
            target=self._todo_autopilot_loop,
            name="clawdone-todo-autopilot",
            daemon=True,
        )
        self._todo_autopilot_thread.start()

    def stop_background_tasks(self) -> None:
        self._todo_autopilot_stop.set()
        if self._todo_autopilot_thread and self._todo_autopilot_thread.is_alive():
            self._todo_autopilot_thread.join(timeout=1.0)

    def _todo_autopilot_loop(self) -> None:
        while not self._todo_autopilot_stop.is_set():
            try:
                self.run_todo_autopilot_cycle()
            except Exception:
                logger.exception("autopilot cycle failed")
            self._todo_autopilot_stop.wait(self.todo_autopilot_interval_sec)

    def run_todo_autopilot_cycle(self) -> None:
        if not self.todo_autopilot_enabled:
            return
        self.auto_dispatch_ready_todos()
        self.process_active_todo_reports()
        self.process_supervisor_review_queue()

    def _todo_is_unblocked(self, todo: dict[str, Any], todos_by_id: dict[str, dict[str, Any]] | None = None) -> bool:
        blockers = [str(item).strip() for item in (todo.get("blocked_by", []) or []) if str(item).strip()]
        if not blockers:
            return True
        if todos_by_id is None:
            todos_by_id = {item["id"]: item for item in self.store.list_todos(profile_name=str(todo.get("profile", "")).strip())}
        for blocker_id in blockers:
            blocker = todos_by_id.get(blocker_id)
            if not blocker:
                return False
            if str(blocker.get("status", "")).strip().lower() not in FINAL_TODO_STATUSES:
                return False
        return True

    def compose_todo_dispatch_command(self, todo: dict[str, Any]) -> str:
        handoff = todo.get("handoff_packet", {}) or {}
        role = str(todo.get("role", "general")).strip() or "general"
        title = " ".join(str(todo.get("title", "")).split())
        detail = " ".join(str(todo.get("detail", "")).split())
        example_payload = {
            "todo_id": todo["id"],
            "status": "done",
            "progress_note": "short delivery summary",
            "evidence": [{"type": "summary", "content": "what shipped and how it was verified"}],
        }
        parts = [
            f"ClawDone task {todo['id']}.",
            f"Role: {role}.",
            f"Title: {title}.",
        ]
        if detail:
            parts.append(f"Detail: {detail}.")
        for label, key in (("Context", "context"), ("Constraints", "constraints"), ("Acceptance", "acceptance"), ("Rollback", "rollback")):
            value = " ".join(str(handoff.get(key, "")).split())
            if value:
                parts.append(f"{label}: {value}.")
        parts.append("When you start or finish, print exactly one single-line report prefixed with CLAWDONE_REPORT and valid JSON only.")
        parts.append(
            f"Final example: CLAWDONE_REPORT {json.dumps(example_payload, ensure_ascii=False, separators=(',', ':'))}"
        )
        parts.append("Use status in_progress when started; use blocked if you are blocked; never wrap the JSON in backticks.")
        return " ".join(part for part in parts if part).strip()

    def auto_dispatch_todo(self, todo: dict[str, Any] | str, actor: str = "autopilot") -> dict[str, Any]:
        with self._todo_dispatch_lock:
            current = self.store.get_todo(todo) if isinstance(todo, str) else self.store.get_todo(str(todo.get("id", "")))
            alias = current.get("alias", "") or self.store.aliases_for(current["profile"]).get(current["target"], "")
            if str(current.get("status", "")).strip().lower() != "todo":
                return {"dispatched": False, "todo": current, "target": current["target"], "alias": alias, "reason": "status"}
            todos_by_id = {item["id"]: item for item in self.store.list_todos(profile_name=current["profile"])}
            if not self._todo_is_unblocked(current, todos_by_id=todos_by_id):
                return {"dispatched": False, "todo": current, "target": current["target"], "alias": alias, "reason": "blocked"}
            command = self.compose_todo_dispatch_command(current)
            try:
                profile = self.get_profile(current["profile"])
                self.remote_tmux.send_keys(profile, target=current["target"], command=command, press_enter=True)
                self.store.record_history({"profile": current["profile"], "target": current["target"], "alias": alias, "command": command})
                updated = self.store.update_todo_status(
                    todo_id=current["id"],
                    status="in_progress",
                    progress_note="Auto-dispatched to agent.",
                    actor=actor,
                )
                self.record_audit_safe(
                    {
                        "action": "todo.auto_dispatch",
                        "profile": updated["profile"],
                        "target": updated["target"],
                        "alias": alias,
                        "todo_id": updated["id"],
                        "status": updated["status"],
                        "note": updated.get("title", ""),
                        "actor": actor,
                        "payload": {"role": updated.get("role", "general")},
                    }
                )
                return {"dispatched": True, "todo": updated, "target": updated["target"], "alias": alias, "command": command}
            except Exception as exc:
                self.record_audit_safe(
                    {
                        "action": "todo.auto_dispatch_error",
                        "profile": current["profile"],
                        "target": current["target"],
                        "alias": alias,
                        "todo_id": current["id"],
                        "status": current.get("status", "todo"),
                        "note": str(exc)[:200],
                        "actor": actor,
                    }
                )
                return {"dispatched": False, "todo": current, "target": current["target"], "alias": alias, "error": str(exc)}

    def auto_dispatch_ready_todos(self, profile_name: str = "") -> list[dict[str, Any]]:
        dispatched: list[dict[str, Any]] = []
        todos = self.store.list_todos(profile_name=profile_name)
        todos_by_id = {item["id"]: item for item in todos}
        ordered = sorted(todos, key=lambda item: (str(item.get("created_at", "")), str(item.get("id", ""))))
        for todo in ordered:
            if str(todo.get("status", "")).strip().lower() != "todo":
                continue
            if not self._todo_is_unblocked(todo, todos_by_id=todos_by_id):
                continue
            route_result = self.supervisor_route_todo(todo, actor="supervisor", auto_send=True)
            result = route_result.get("dispatch", {"dispatched": False, "todo": route_result.get("todo", todo)})
            if result.get("dispatched"):
                dispatched.append({**result, "supervisor": route_result.get("decision")})
                todos_by_id[todo["id"]] = result["todo"]
        return dispatched

    def _extract_balanced_report_json(self, text: str, start_index: int) -> tuple[str, int] | None:
        return extract_json_object(text, start_index)

    def extract_todo_reports(self, output: str) -> list[dict[str, Any]]:
        text = str(output or "")
        reports: list[dict[str, Any]] = []
        marker = "CLAWDONE_REPORT"
        cursor = 0
        while True:
            marker_index = text.find(marker, cursor)
            if marker_index < 0:
                break
            parsed = self._extract_balanced_report_json(text, marker_index + len(marker))
            if parsed is None:
                cursor = marker_index + len(marker)
                continue
            raw, next_index = parsed
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                cursor = marker_index + len(marker)
                continue
            if isinstance(payload, dict):
                canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                reports.append({"raw": raw, "payload": payload, "key": canonical})
            cursor = next_index
        return reports

    def apply_todo_report(
        self,
        todo_id: str,
        status: str = "",
        progress_note: str = "",
        evidence: Any = None,
        actor: str = "agent",
    ) -> dict[str, Any]:
        updated = self.store.get_todo(todo_id)
        status_value = str(status or "").strip().lower()
        note = str(progress_note or "")
        report_evidence = evidence
        if status_value in FINAL_TODO_STATUSES and report_evidence in (None, "", []) and note.strip():
            report_evidence = {"type": "summary", "content": note.strip()}

        if status_value in FINAL_TODO_STATUSES and report_evidence not in (None, "", []):
            if isinstance(report_evidence, list):
                for item in report_evidence:
                    updated = self.store.append_todo_evidence(updated["id"], item, actor=actor)
            else:
                updated = self.store.append_todo_evidence(updated["id"], report_evidence, actor=actor)
            report_evidence = None

        if status_value:
            updated = self.store.update_todo_status(
                todo_id=todo_id,
                status=status_value,
                progress_note=note,
                actor=actor,
            )
        elif note.strip():
            event = {
                "type": "status",
                "status": updated.get("status", ""),
                "note": note.strip(),
                "actor": actor,
                "created_at": "",
            }
            updated["events"] = [event, *(updated.get("events", []) or [])]
            updated["progress_note"] = note.strip()
            updated = self.store.save_todo(updated)

        if report_evidence not in (None, "", []):
            if isinstance(report_evidence, list):
                for item in report_evidence:
                    updated = self.store.append_todo_evidence(updated["id"], item, actor=actor)
            else:
                updated = self.store.append_todo_evidence(updated["id"], report_evidence, actor=actor)

        self.record_audit_safe(
            {
                "action": "todo.report",
                "profile": updated["profile"],
                "target": updated["target"],
                "alias": updated.get("alias", ""),
                "todo_id": updated["id"],
                "status": updated["status"],
                "note": note.strip(),
                "actor": actor,
            }
        )
        if status_value in FINAL_TODO_STATUSES:
            self.auto_dispatch_ready_todos(profile_name=updated["profile"])
            if str(actor).strip().lower() != "supervisor":
                self.maybe_run_supervisor_review(updated, actor="supervisor")
                updated = self.store.get_todo(updated["id"])
        return updated

    def process_pane_reports(self, profile_name: str, target: str, output: str) -> list[dict[str, Any]]:
        applied: list[dict[str, Any]] = []
        for report in self.extract_todo_reports(output):
            key = f"{profile_name}:{target}:{report.get('key', report['raw'])}"
            if key in self._processed_report_keys:
                continue
            payload = report["payload"]
            todo_id = str(payload.get("todo_id", "")).strip()
            if not todo_id:
                continue
            try:
                current = self.store.get_todo(todo_id)
            except RuntimeError:
                continue
            if current.get("profile") != profile_name or current.get("target") != target:
                self.record_audit_safe(
                    {
                        "action": "todo.report_ignored",
                        "profile": profile_name,
                        "target": target,
                        "todo_id": todo_id,
                        "note": "report target mismatch",
                        "actor": "autopilot",
                    }
                )
                self._processed_report_keys[key] = None
                if len(self._processed_report_keys) > 10000:
                    self._processed_report_keys.popitem(last=False)
                continue
            status = str(payload.get("status", "")).strip().lower()
            progress_note = str(payload.get("progress_note", ""))
            evidence = payload.get("evidence")
            if status in FINAL_TODO_STATUSES and evidence in (None, "", []):
                summary = progress_note.strip() or str(payload.get("delivery", "")).strip() or report["raw"]
                evidence = {"type": "summary", "content": summary}
            updated = self.apply_todo_report(todo_id=todo_id, status=status, progress_note=progress_note, evidence=evidence, actor="agent")
            applied.append(updated)
            self._processed_report_keys[key] = None
            if len(self._processed_report_keys) > 10000:
                self._processed_report_keys.popitem(last=False)
        return applied

    def process_active_todo_reports(self) -> list[dict[str, Any]]:
        active_targets: set[tuple[str, str]] = set()
        for todo in self.store.list_todos():
            status = str(todo.get("status", "")).strip().lower()
            if status not in {"in_progress", "done"}:
                continue
            profile_name = str(todo.get("profile", "")).strip()
            target = str(todo.get("target", "")).strip()
            if profile_name and target:
                active_targets.add((profile_name, target))
        applied: list[dict[str, Any]] = []
        for profile_name, target in sorted(active_targets):
            try:
                profile = self.get_profile(profile_name)
                output = self.remote_tmux.capture_pane(profile, target=target, lines=self.todo_autopilot_lines)
            except Exception:
                continue
            applied.extend(self.process_pane_reports(profile_name, target, output))
        return applied

    def capture_pane_with_reports(self, profile_name: str, target: str, lines: int) -> str:
        profile = self.get_profile(profile_name)
        output = self.remote_tmux.capture_pane(profile, target=target, lines=lines)
        if self.todo_autopilot_enabled:
            self.process_pane_reports(profile_name, target, output)
        return output

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
            output = self.capture_pane_with_reports(profile_name=profile_name, target=target, lines=max_lines)
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
            if requested_view not in self._html_cache:
                requested_view = "dashboard"
            self.html_response(
                handler,
                self._html_cache[requested_view],
                gzipped=self._html_cache_gzipped[requested_view],
            )
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

        if parsed.path == "/api/supervisor/configs":
            profile_name = str(query.get("profile", [""])[0]).strip()
            if profile_name and not self.require_share_scope(handler, profile_name, ""):
                return
            configs = [mask_supervisor_config(item) for item in self.store.list_supervisor_configs(profile_name=profile_name)]
            self.json_response(handler, HTTPStatus.OK, {"configs": configs})
            return

        if parsed.path == "/api/supervisor/config":
            profile_name = str(query.get("profile", [""])[0]).strip()
            config_id = str(query.get("id", [""])[0]).strip()
            if profile_name and not self.require_share_scope(handler, profile_name, ""):
                return
            self.json_response(handler, HTTPStatus.OK, {"config": self.supervisor_config_payload(profile_name=profile_name, config_id=config_id)})
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
            output = self.capture_pane_with_reports(profile_name=profile_name, target=target, lines=lines)
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
            dispatches = self.auto_dispatch_ready_todos(profile_name=todo["profile"]) if self.todo_autopilot_enabled else []
            latest = next((item for item in dispatches if item.get("todo", {}).get("id") == todo["id"]), None)
            resolved = latest.get("todo", todo) if latest else self.store.get_todo(todo["id"])
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "todo": resolved, "dispatch": latest or {"dispatched": False, "todo": resolved}})
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
            dispatches = self.auto_dispatch_ready_todos(profile_name=profile_name) if self.todo_autopilot_enabled else []
            todos = self.store.list_workflow_todos(workflow["workflow_id"])
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "workflow_id": workflow["workflow_id"], "todos": todos, "dispatches": dispatches})
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
            dispatches = self.auto_dispatch_ready_todos(profile_name=todo["profile"]) if self.todo_autopilot_enabled else []
            latest = next((item for item in dispatches if item.get("todo", {}).get("id") == todo["id"]), None)
            resolved = latest.get("todo", todo) if latest else self.store.get_todo(todo["id"])
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "todo": resolved, "dispatch": latest or {"dispatched": False, "todo": resolved}})
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

        if parsed.path == "/api/todos/clear-completed":
            if not self.require_role(handler, "operator"):
                return
            profile_name = str(body.get("profile", "")).strip()
            target = str(body.get("target", "")).strip()
            keep_recent = body.get("keep_recent", 5)
            min_age_days = body.get("min_age_days", 0)
            if not profile_name:
                self.json_response(handler, HTTPStatus.BAD_REQUEST, {"error": "todo profile is required"})
                return
            if not self.require_share_scope(handler, profile_name, target):
                return
            removed = self.store.clear_completed_todos(
                profile_name=profile_name,
                target=target,
                keep_recent=int(keep_recent or 0),
                min_age_days=int(min_age_days or 0),
            )
            for todo in removed:
                self.record_audit_safe(
                    {
                        "action": "todo.delete.completed",
                        "profile": todo["profile"],
                        "target": todo["target"],
                        "alias": todo.get("alias", ""),
                        "todo_id": todo["id"],
                        "status": todo.get("status", ""),
                        "note": todo.get("title", ""),
                        "actor": actor,
                    }
                )
            self.json_response(
                handler,
                HTTPStatus.OK,
                {
                    "ok": True,
                    "removed_count": len(removed),
                    "removed_ids": [todo["id"] for todo in removed],
                    "keep_recent": int(keep_recent or 0),
                    "min_age_days": int(min_age_days or 0),
                },
            )
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
            status_now = str(todo.get("status", "")).strip().lower()
            dispatches = self.auto_dispatch_ready_todos(profile_name=todo["profile"]) if status_now in FINAL_TODO_STATUSES | {"todo"} else []
            if status_now in FINAL_TODO_STATUSES and request_actor.strip().lower() != "supervisor":
                self.maybe_run_supervisor_review(todo, actor="supervisor")
                todo = self.store.get_todo(todo_id)
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "todo": todo, "dispatches": dispatches})
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

            scoped_todo = self.store.get_todo(todo_id)
            if not self.require_share_scope(handler, scoped_todo.get("profile", ""), scoped_todo.get("target", "")):
                return
            updated = self.apply_todo_report(
                todo_id=todo_id,
                status=status,
                progress_note=progress_note,
                evidence=evidence,
                actor=request_actor,
            )
            dispatches = self.auto_dispatch_ready_todos(profile_name=updated["profile"]) if str(updated.get("status", "")).strip().lower() in FINAL_TODO_STATUSES else []
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "todo": updated, "dispatches": dispatches})
            return

        if parsed.path == "/api/supervisor/config/save":
            if not self.require_role(handler, "operator"):
                return
            profile_name = str(body.get("profile", "")).strip()
            if profile_name and not self.require_share_scope(handler, profile_name, ""):
                return
            config = self.store.save_supervisor_config(body)
            self.record_audit_safe(
                {
                    "action": "supervisor.config.save",
                    "profile": config.get("profile", ""),
                    "note": config.get("name", ""),
                    "actor": actor,
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "config": mask_supervisor_config(config)})
            return

        if parsed.path == "/api/supervisor/config/delete":
            if not self.require_role(handler, "operator"):
                return
            config_id = str(body.get("id", "")).strip()
            config = self.store.get_supervisor_config(config_id=config_id)
            if config.get("profile") and not self.require_share_scope(handler, str(config.get("profile", "")), ""):
                return
            self.store.delete_supervisor_config(config_id)
            self.record_audit_safe({"action": "supervisor.config.delete", "profile": config.get("profile", ""), "note": config_id, "actor": actor})
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "id": config_id})
            return

        if parsed.path == "/api/supervisor/dispatch":
            if not self.require_role(handler, "operator"):
                return
            todo_id = str(body.get("todo_id", "")).strip()
            if not todo_id:
                raise ValueError("todo_id is required")
            todo = self.store.get_todo(todo_id)
            if not self.require_share_scope(handler, todo.get("profile", ""), todo.get("target", "")):
                return
            config = self.store.get_supervisor_config(config_id=str(body.get("config_id", "")).strip(), profile_name=str(todo.get("profile", "")).strip())
            self.require_supervisor_permission(config, "dispatch")
            decision = self.supervisor_client.dispatch(config=config, todo=todo, candidates=self.list_supervisor_candidates(str(todo.get("profile", "")).strip()))
            apply_decision = bool(body.get("apply", True))
            auto_send = bool(body.get("auto_send", True))
            updated = todo
            dispatch_result: dict[str, Any] = {"dispatched": False}
            if apply_decision:
                updated = self.store.save_todo({**todo, "id": todo["id"], "target": decision["target"], "alias": decision.get("alias", "")})
                self.record_audit_safe(
                    {
                        "action": "supervisor.dispatch",
                        "profile": updated["profile"],
                        "target": updated["target"],
                        "alias": updated.get("alias", ""),
                        "todo_id": updated["id"],
                        "status": updated["status"],
                        "note": decision.get("reason", ""),
                        "actor": actor,
                    }
                )
                if auto_send and str(updated.get("status", "")).strip().lower() == "todo":
                    dispatch_result = self.auto_dispatch_todo(updated, actor="supervisor")
                    updated = dispatch_result.get("todo", updated)
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "decision": decision, "todo": updated, "dispatch": dispatch_result})
            return

        if parsed.path == "/api/supervisor/review":
            if not self.require_role(handler, "operator"):
                return
            todo_id = str(body.get("todo_id", "")).strip()
            if not todo_id:
                raise ValueError("todo_id is required")
            todo = self.store.get_todo(todo_id)
            if not self.require_share_scope(handler, todo.get("profile", ""), todo.get("target", "")):
                return
            config = self.store.get_supervisor_config(config_id=str(body.get("config_id", "")).strip(), profile_name=str(todo.get("profile", "")).strip())
            self.require_supervisor_permission(config, "review")
            pane_output = str(body.get("pane_output", ""))
            if not pane_output and bool(body.get("include_pane_output", True)):
                pane_output = self.capture_todo_output(todo)
            review = self.supervisor_client.review(config=config, todo=todo, pane_output=pane_output)
            apply_review = bool(body.get("apply", False))
            updated = todo
            if apply_review:
                evidence = review.get("evidence", [])
                if review["verdict"] == "accept":
                    target_status = "verified" if str(todo.get("status", "")).strip().lower() in {"done", "verified"} else "done"
                    updated = self.apply_todo_report(todo_id=todo_id, status=target_status, progress_note=review.get("summary", ""), evidence=evidence, actor="supervisor")
                elif review["verdict"] == "blocked":
                    updated = self.apply_todo_report(todo_id=todo_id, status="blocked", progress_note=review.get("summary", ""), evidence=evidence, actor="supervisor")
                else:
                    updated = self.apply_todo_report(todo_id=todo_id, status="", progress_note=review.get("summary", ""), evidence=evidence, actor="supervisor")
            self.record_audit_safe(
                {
                    "action": "supervisor.review",
                    "profile": updated.get("profile", ""),
                    "target": updated.get("target", ""),
                    "alias": updated.get("alias", ""),
                    "todo_id": updated.get("id", ""),
                    "status": updated.get("status", ""),
                    "note": review.get("summary", ""),
                    "actor": actor,
                    "payload": {"verdict": review.get("verdict", "needs_work")},
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "review": review, "todo": updated})
            return

        if parsed.path == "/api/supervisor/accept":
            if not self.require_role(handler, "operator"):
                return
            todo_id = str(body.get("todo_id", "")).strip()
            if not todo_id:
                raise ValueError("todo_id is required")
            todo = self.store.get_todo(todo_id)
            if not self.require_share_scope(handler, todo.get("profile", ""), todo.get("target", "")):
                return
            config = self.store.get_supervisor_config(config_id=str(body.get("config_id", "")).strip(), profile_name=str(todo.get("profile", "")).strip())
            self.require_supervisor_permission(config, "accept")
            pane_output = str(body.get("pane_output", ""))
            if not pane_output and bool(body.get("include_pane_output", True)):
                pane_output = self.capture_todo_output(todo)
            review = self.supervisor_client.review(config=config, todo=todo, pane_output=pane_output)
            if review.get("verdict") != "accept":
                self.json_response(handler, HTTPStatus.OK, {"ok": True, "accepted": False, "review": review, "todo": todo})
                return
            evidence = review.get("evidence", [])
            current_status = str(todo.get("status", "")).strip().lower()
            updated = todo
            if current_status not in {"done", "verified"}:
                updated = self.apply_todo_report(todo_id=todo_id, status="done", progress_note=review.get("summary", ""), evidence=evidence, actor="supervisor")
                evidence = []
            if str(updated.get("status", "")).strip().lower() != "verified":
                updated = self.apply_todo_report(todo_id=todo_id, status="verified", progress_note=review.get("summary", ""), evidence=evidence, actor="supervisor")
            self.record_audit_safe(
                {
                    "action": "supervisor.accept",
                    "profile": updated.get("profile", ""),
                    "target": updated.get("target", ""),
                    "alias": updated.get("alias", ""),
                    "todo_id": updated.get("id", ""),
                    "status": updated.get("status", ""),
                    "note": review.get("summary", ""),
                    "actor": actor,
                }
            )
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "accepted": True, "review": review, "todo": updated})
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


class ClawDoneServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler_cls: type[BaseHTTPRequestHandler], app: ClawDoneApp):
        super().__init__(server_address, handler_cls)
        self.app = app

    def shutdown(self) -> None:
        self.app.stop_background_tasks()
        super().shutdown()

    def server_close(self) -> None:
        self.app.stop_background_tasks()
        super().server_close()


def create_server(
    config: dict[str, Any],
    tmux_client: TmuxClient | None = None,
    store: ProfileStore | None = None,
    remote_tmux: RemoteTmuxClient | None = None,
) -> ThreadingHTTPServer:
    app = ClawDoneApp(config=config, tmux_client=tmux_client, store=store, remote_tmux=remote_tmux)
    server = ClawDoneServer((app.config["host"], app.config["port"]), build_handler(app), app)
    app.start_background_tasks()
    return server
