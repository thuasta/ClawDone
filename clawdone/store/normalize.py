"""Persistence for SSH profiles, pane aliases, templates, history, and todos."""

from __future__ import annotations

import copy
import json
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4

from ..supervisor import mask_supervisor_config, normalize_supervisor_config

PROFILE_HOST_KEY_POLICIES = {"", "strict", "accept-new", "insecure"}
TODO_STATUSES = {"todo", "in_progress", "done", "verified", "blocked"}
TODO_PRIORITIES = {"low", "medium", "high", "urgent"}
TODO_ROLES = {"general", "planner", "executor", "reviewer"}
SHARE_PERMISSIONS = {"read", "control"}
UI_VIEWS = {"dashboard", "auth", "chat", "todo", "delivery"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_utc(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def normalize_tags(value: Any) -> list[str]:
    if isinstance(value, str):
        items = value.split(",")
    elif isinstance(value, list):
        items = value
    else:
        items = []

    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        tag = str(item).strip()
        if not tag:
            continue
        lowered = tag.lower()
        if lowered in seen:
            continue
        deduped.append(tag)
        seen.add(lowered)
    return deduped


def optional_non_negative_int(value: Any, field_name: str) -> int:
    if value in (None, ""):
        return 0
    parsed = int(value)
    if parsed < 0:
        raise ValueError(f"{field_name} must be >= 0")
    return parsed


def normalize_host_key_policy(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_profile(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(payload.get("name", "")).strip(),
        "host": str(payload.get("host", "")).strip(),
        "username": str(payload.get("username", "")).strip(),
        "port": int(payload.get("port", 22) or 22),
        "password": str(payload.get("password", "")),
        "password_ref": str(payload.get("password_ref", "")).strip(),
        "key_filename": str(payload.get("key_filename", "")).strip(),
        "tmux_bin": str(payload.get("tmux_bin", "tmux") or "tmux").strip(),
        "group": str(payload.get("group", "General")).strip() or "General",
        "tags": normalize_tags(payload.get("tags", [])),
        "favorite": bool(payload.get("favorite", False)),
        "description": str(payload.get("description", "")).strip(),
        "host_key_policy": normalize_host_key_policy(payload.get("host_key_policy", "")),
        "ssh_timeout": optional_non_negative_int(payload.get("ssh_timeout", 0), "ssh_timeout"),
        "ssh_command_timeout": optional_non_negative_int(payload.get("ssh_command_timeout", 0), "ssh_command_timeout"),
        "ssh_retries": optional_non_negative_int(payload.get("ssh_retries", 0), "ssh_retries"),
        "ssh_retry_backoff_ms": optional_non_negative_int(payload.get("ssh_retry_backoff_ms", 0), "ssh_retry_backoff_ms"),
        "mcp_url": str(payload.get("mcp_url", "")).strip(),
        "created_at": str(payload.get("created_at", "")).strip(),
        "updated_at": str(payload.get("updated_at", "")).strip(),
    }


def mask_profile(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        **profile,
        "password": "",
        "has_password": bool(profile.get("password")) or bool(profile.get("password_ref")),
    }


def normalize_template(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(payload.get("id", "")).strip() or uuid4().hex,
        "name": str(payload.get("name", "")).strip(),
        "command": str(payload.get("command", "")).strip(),
        "profile": str(payload.get("profile", "")).strip(),
        "target": str(payload.get("target", "")).strip(),
        "created_at": str(payload.get("created_at", "")).strip(),
        "updated_at": str(payload.get("updated_at", "")).strip(),
    }


def normalize_todo_status(value: Any) -> str:
    status = str(value or "todo").strip().lower() or "todo"
    if status not in TODO_STATUSES:
        allowed = ", ".join(sorted(TODO_STATUSES))
        raise ValueError(f"todo status must be one of: {allowed}")
    return status


def normalize_todo_priority(value: Any) -> str:
    priority = str(value or "medium").strip().lower() or "medium"
    if priority not in TODO_PRIORITIES:
        allowed = ", ".join(sorted(TODO_PRIORITIES))
        raise ValueError(f"todo priority must be one of: {allowed}")
    return priority


def normalize_todo_role(value: Any) -> str:
    role = str(value or "general").strip().lower() or "general"
    if role not in TODO_ROLES:
        allowed = ", ".join(sorted(TODO_ROLES))
        raise ValueError(f"todo role must be one of: {allowed}")
    return role


def normalize_handoff_packet(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    packet = {
        "context": str(value.get("context", "")).strip(),
        "constraints": str(value.get("constraints", "")).strip(),
        "acceptance": str(value.get("acceptance", "")).strip(),
        "rollback": str(value.get("rollback", "")).strip(),
    }
    has_any = any(packet.values())
    if not has_any:
        return {}
    missing = [key for key, val in packet.items() if not val]
    if missing:
        raise ValueError(f"handoff packet is incomplete, missing: {', '.join(missing)}")
    return packet


def normalize_todo_evidence(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        evidence = {
            "id": str(value.get("id", "")).strip() or uuid4().hex,
            "type": str(value.get("type", "text")).strip() or "text",
            "content": str(value.get("content", "")).strip(),
            "source": str(value.get("source", "")).strip(),
            "created_at": str(value.get("created_at", "")).strip() or utc_now(),
        }
    else:
        evidence = {
            "id": uuid4().hex,
            "type": "text",
            "content": str(value).strip(),
            "source": "",
            "created_at": utc_now(),
        }
    if not evidence["content"]:
        raise ValueError("todo evidence content is required")
    return evidence


def normalize_todo_event(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {
            "id": uuid4().hex,
            "type": "note",
            "status": "",
            "note": str(value).strip(),
            "actor": "",
            "created_at": utc_now(),
        }
    return {
        "id": str(value.get("id", "")).strip() or uuid4().hex,
        "type": str(value.get("type", "note")).strip() or "note",
        "status": str(value.get("status", "")).strip().lower(),
        "note": str(value.get("note", "")).strip(),
        "actor": str(value.get("actor", "")).strip(),
        "created_at": str(value.get("created_at", "")).strip() or utc_now(),
    }


def normalize_todo(payload: dict[str, Any]) -> dict[str, Any]:
    evidence_items: list[dict[str, Any]] = []
    for item in payload.get("evidence", []) or []:
        try:
            evidence_items.append(normalize_todo_evidence(item))
        except ValueError:
            continue

    events: list[dict[str, Any]] = []
    for item in payload.get("events", []) or []:
        events.append(normalize_todo_event(item))

    return {
        "id": str(payload.get("id", "")).strip() or uuid4().hex,
        "title": str(payload.get("title", "")).strip(),
        "detail": str(payload.get("detail", "")).strip(),
        "profile": str(payload.get("profile", "")).strip(),
        "target": str(payload.get("target", "")).strip(),
        "alias": str(payload.get("alias", "")).strip(),
        "status": normalize_todo_status(payload.get("status", "todo")),
        "priority": normalize_todo_priority(payload.get("priority", "medium")),
        "role": normalize_todo_role(payload.get("role", "general")),
        "workflow_id": str(payload.get("workflow_id", "")).strip(),
        "parent_todo_id": str(payload.get("parent_todo_id", "")).strip(),
        "blocked_by": [str(item).strip() for item in (payload.get("blocked_by", []) or []) if str(item).strip()],
        "handoff_packet": normalize_handoff_packet(payload.get("handoff_packet", {})),
        "verified_by": str(payload.get("verified_by", "")).strip(),
        "verified_at": str(payload.get("verified_at", "")).strip(),
        "assignee": str(payload.get("assignee", "")).strip(),
        "progress_note": str(payload.get("progress_note", "")).strip(),
        "evidence": evidence_items,
        "events": events,
        "created_at": str(payload.get("created_at", "")).strip(),
        "updated_at": str(payload.get("updated_at", "")).strip(),
    }


def normalize_todo_template(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(payload.get("id", "")).strip() or uuid4().hex,
        "name": str(payload.get("name", "")).strip(),
        "title": str(payload.get("title", "")).strip(),
        "detail": str(payload.get("detail", "")).strip(),
        "priority": normalize_todo_priority(payload.get("priority", "medium")),
        "profile": str(payload.get("profile", "")).strip(),
        "target": str(payload.get("target", "")).strip(),
        "assignee": str(payload.get("assignee", "")).strip(),
        "created_at": str(payload.get("created_at", "")).strip(),
        "updated_at": str(payload.get("updated_at", "")).strip(),
    }


def normalize_share_link(payload: dict[str, Any]) -> dict[str, Any]:
    permission = str(payload.get("permission", "read")).strip().lower() or "read"
    if permission not in SHARE_PERMISSIONS:
        allowed = ", ".join(sorted(SHARE_PERMISSIONS))
        raise ValueError(f"share permission must be one of: {allowed}")
    return {
        "id": str(payload.get("id", "")).strip() or uuid4().hex,
        "token": str(payload.get("token", "")).strip() or uuid4().hex,
        "profile": str(payload.get("profile", "")).strip(),
        "target": str(payload.get("target", "")).strip(),
        "alias": str(payload.get("alias", "")).strip(),
        "permission": permission,
        "expires_at": str(payload.get("expires_at", "")).strip(),
        "revoked_at": str(payload.get("revoked_at", "")).strip(),
        "created_by": str(payload.get("created_by", "")).strip(),
        "owner_hash": str(payload.get("owner_hash", "")).strip(),
        "created_at": str(payload.get("created_at", "")).strip() or utc_now(),
        "updated_at": str(payload.get("updated_at", "")).strip(),
    }


def normalize_workspace_template(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(payload.get("id", "")).strip() or uuid4().hex,
        "name": str(payload.get("name", "")).strip(),
        "profile": str(payload.get("profile", "")).strip(),
        "target": str(payload.get("target", "")).strip(),
        "bootstrap_command": str(payload.get("bootstrap_command", "")).strip(),
        "teardown_command": str(payload.get("teardown_command", "")).strip(),
        "env": str(payload.get("env", "")).strip(),
        "notes": str(payload.get("notes", "")).strip(),
        "created_at": str(payload.get("created_at", "")).strip(),
        "updated_at": str(payload.get("updated_at", "")).strip(),
    }


def normalize_audit_entry(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(payload.get("id", "")).strip() or uuid4().hex,
        "action": str(payload.get("action", "")).strip(),
        "profile": str(payload.get("profile", "")).strip(),
        "target": str(payload.get("target", "")).strip(),
        "alias": str(payload.get("alias", "")).strip(),
        "todo_id": str(payload.get("todo_id", "")).strip(),
        "status": str(payload.get("status", "")).strip(),
        "note": str(payload.get("note", "")).strip(),
        "actor": str(payload.get("actor", "")).strip(),
        "payload": payload.get("payload", {}),
        "created_at": str(payload.get("created_at", "")).strip() or utc_now(),
    }


def normalize_ui_settings(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    bounds = {
        "paneLines": (20, 200),
        "targetPageSize": (1, 24),
        "historyPageSize": (1, 30),
        "todoPageSize": (1, 20),
    }
    normalized: dict[str, int] = {}
    for key, (min_value, max_value) in bounds.items():
        if key not in value:
            continue
        try:
            parsed = int(value.get(key))
        except (TypeError, ValueError):
            continue
        normalized[key] = max(min_value, min(parsed, max_value))
    return normalized


def normalize_fold_states(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, str] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key).strip()
        if not key:
            continue
        state = str(raw_value).strip().lower()
        if state not in {"open", "closed"}:
            continue
        normalized[key] = state
    return normalized


def normalize_ui_state(payload: Any) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    current_view = str(source.get("current_view", "dashboard")).strip().lower() or "dashboard"
    if current_view not in UI_VIEWS:
        current_view = "dashboard"
    selected_profile = str(source.get("selected_profile", "")).strip()
    return {
        "ui_settings": normalize_ui_settings(source.get("ui_settings", {})),
        "current_view": current_view,
        "selected_profile": selected_profile,
        "fold_states": normalize_fold_states(source.get("fold_states", {})),
        "updated_at": str(source.get("updated_at", "")).strip(),
    }

