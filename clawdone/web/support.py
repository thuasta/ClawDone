"""HTTP app and request handlers."""

from __future__ import annotations

import gzip
import asyncio
import errno
import hashlib
import json
import logging
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from ..html import INDEX_HTML
from ..local_tmux import TmuxClient
from ..remote import HOST_KEY_POLICIES, PARAMIKO_AVAILABLE, RemoteTmuxClient, SSHExecutor
from ..store import ProfileStore, mask_profile, mask_supervisor_config, normalize_profile
from ..supervisor import SupervisorClient
from ..utils import extract_json_object

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
PANE_CAPTURE_DEFAULT_LINES = 120
PANE_CAPTURE_MIN_LINES = 20
PANE_CAPTURE_MAX_LINES = 200
REPORT_PAYLOAD_KEY_ALIASES = {
    "todoid": "todo_id",
    "todo_id": "todo_id",
    "status": "status",
    "progressnote": "progress_note",
    "progress_note": "progress_note",
    "evidence": "evidence",
    "delivery": "delivery",
}
CHECKLIST_NOISE_KEYS = {
    "task",
    "tasks",
    "todo",
    "todos",
    "checklist",
    "low",
    "medium",
    "high",
    "urgent",
    "save checklist",
    "send checklist to current agent",
    "refresh checklist",
    "clear completed",
    "clear all",
    "clear all tasks",
    "select all",
}
CHECKLIST_LINE_PREFIX = re.compile(r"^(?:[-*•]\s+|\d+[.)]\s+|\[(?: |x|X)?\]\s+|-\s*\[(?: |x|X)?\]\s+)")


def _is_client_disconnect(exc: BaseException) -> bool:
    if isinstance(exc, (BrokenPipeError, ConnectionResetError)):
        return True
    if isinstance(exc, OSError):
        return exc.errno in {errno.EPIPE, errno.ECONNRESET}
    return False


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
        "dispatch_concurrency": _positive_int(config, "dispatch_concurrency", 8),
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
        html = html.replace(
            f'<a class="tab-button" href="/?view={item}" data-view-button="{item}">',
            f'<a class="tab-button{active}" href="/?view={item}" data-view-button="{item}">',
        )
        html = html.replace(
            f'<a class="tab-button active" href="/?view={item}" data-view-button="{item}">',
            f'<a class="tab-button{active}" href="/?view={item}" data-view-button="{item}">',
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

