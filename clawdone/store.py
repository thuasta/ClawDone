"""Persistence for SSH profiles, pane aliases, templates, history, and todos."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4

PROFILE_HOST_KEY_POLICIES = {"", "strict", "accept-new", "insecure"}
TODO_STATUSES = {"todo", "in_progress", "done", "verified", "blocked"}
TODO_PRIORITIES = {"low", "medium", "high", "urgent"}
TODO_ROLES = {"general", "planner", "executor", "reviewer"}
SHARE_PERMISSIONS = {"read", "control"}


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


class ProfileStore:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()

    def _empty(self) -> dict[str, Any]:
        return {
            "profiles": [],
            "aliases": {},
            "templates": [],
            "history": [],
            "todos": [],
            "todo_templates": [],
            "audit_logs": [],
            "session_shares": [],
            "workspace_templates": [],
        }

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        content = self.path.read_text(encoding="utf-8").strip()
        if not content:
            return self._empty()
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"invalid profile store JSON: {self.path}") from exc
        if not isinstance(data, dict):
            raise RuntimeError("profile store content must be a JSON object")
        data.setdefault("profiles", [])
        data.setdefault("aliases", {})
        data.setdefault("templates", [])
        data.setdefault("history", [])
        data.setdefault("todos", [])
        data.setdefault("todo_templates", [])
        data.setdefault("audit_logs", [])
        data.setdefault("session_shares", [])
        data.setdefault("workspace_templates", [])
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.path.parent) as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temp_name = handle.name
        Path(temp_name).replace(self.path)

    def list_profiles(self) -> list[dict[str, Any]]:
        raw_profiles = self._read().get("profiles", [])
        profiles: list[dict[str, Any]] = []
        for item in raw_profiles:
            if isinstance(item, dict):
                profiles.append(normalize_profile(item))
        return sorted(
            profiles,
            key=lambda profile: (
                not bool(profile.get("favorite")),
                str(profile.get("group", "")).lower(),
                str(profile["name"]).lower(),
            ),
        )

    def get_profile(self, name: str) -> dict[str, Any]:
        if not name.strip():
            raise ValueError("profile name is required")
        for profile in self.list_profiles():
            if profile["name"] == name:
                return profile
        raise RuntimeError(f"profile not found: {name}")

    def save_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        normalized = normalize_profile(profile)
        existing: dict[str, Any] | None = None
        try:
            existing = self.get_profile(normalized["name"])
        except RuntimeError:
            existing = None

        if existing and not normalized["password"] and not normalized["password_ref"]:
            normalized["password"] = str(existing.get("password", ""))
            normalized["password_ref"] = str(existing.get("password_ref", "")).strip()
        if normalized["password"] and normalized["password_ref"]:
            raise ValueError("profile password and password_ref cannot both be set")
        if not normalized["name"]:
            raise ValueError("profile name is required")
        if not normalized["host"]:
            raise ValueError("profile host is required")
        if not normalized["username"]:
            raise ValueError("profile username is required")
        if normalized["port"] <= 0:
            raise ValueError("profile port must be positive")
        if normalized["host_key_policy"] not in PROFILE_HOST_KEY_POLICIES:
            allowed = ", ".join(sorted(policy for policy in PROFILE_HOST_KEY_POLICIES if policy))
            raise ValueError(f"profile host_key_policy must be empty or one of: {allowed}")

        now = utc_now()
        normalized["created_at"] = existing.get("created_at", now) if existing else now
        normalized["updated_at"] = now

        data = self._read()
        profiles = [
            item
            for item in data.get("profiles", [])
            if isinstance(item, dict) and item.get("name") != normalized["name"]
        ]
        profiles.append(normalized)
        data["profiles"] = sorted(profiles, key=lambda item: str(item.get("name", "")).lower())
        self._write(data)
        return normalized

    def delete_profile(self, name: str) -> None:
        data = self._read()
        profiles = [
            item
            for item in data.get("profiles", [])
            if isinstance(item, dict) and item.get("name") != name
        ]
        if len(profiles) == len(data.get("profiles", [])):
            raise RuntimeError(f"profile not found: {name}")
        data["profiles"] = profiles
        aliases = data.get("aliases", {})
        if isinstance(aliases, dict):
            aliases.pop(name, None)
        data["aliases"] = aliases
        templates = data.get("templates", [])
        data["templates"] = [
            item for item in templates if not isinstance(item, dict) or str(item.get("profile", "")).strip() != name
        ]
        history = data.get("history", [])
        data["history"] = [
            item for item in history if not isinstance(item, dict) or str(item.get("profile", "")).strip() != name
        ]
        todos = data.get("todos", [])
        data["todos"] = [
            item for item in todos if not isinstance(item, dict) or str(item.get("profile", "")).strip() != name
        ]
        todo_templates = data.get("todo_templates", [])
        data["todo_templates"] = [
            item for item in todo_templates if not isinstance(item, dict) or str(item.get("profile", "")).strip() != name
        ]
        audit_logs = data.get("audit_logs", [])
        data["audit_logs"] = [
            item for item in audit_logs if not isinstance(item, dict) or str(item.get("profile", "")).strip() != name
        ]
        session_shares = data.get("session_shares", [])
        data["session_shares"] = [
            item for item in session_shares if not isinstance(item, dict) or str(item.get("profile", "")).strip() != name
        ]
        workspace_templates = data.get("workspace_templates", [])
        data["workspace_templates"] = [
            item
            for item in workspace_templates
            if not isinstance(item, dict) or str(item.get("profile", "")).strip() != name
        ]
        self._write(data)

    def aliases_for(self, profile_name: str) -> dict[str, str]:
        aliases = self._read().get("aliases", {})
        if not isinstance(aliases, dict):
            return {}
        profile_aliases = aliases.get(profile_name, {})
        if not isinstance(profile_aliases, dict):
            return {}
        return {str(key): str(value) for key, value in profile_aliases.items()}

    def set_alias(self, profile_name: str, target: str, alias: str) -> None:
        if not profile_name.strip():
            raise ValueError("profile name is required")
        if not target.strip():
            raise ValueError("target is required")
        data = self._read()
        aliases = data.setdefault("aliases", {})
        if not isinstance(aliases, dict):
            aliases = {}
            data["aliases"] = aliases
        profile_aliases = aliases.setdefault(profile_name, {})
        if not isinstance(profile_aliases, dict):
            profile_aliases = {}
            aliases[profile_name] = profile_aliases
        cleaned_alias = alias.strip()
        if cleaned_alias:
            profile_aliases[target] = cleaned_alias
        else:
            profile_aliases.pop(target, None)
        self._write(data)

    def list_templates(self, profile_name: str = "") -> list[dict[str, Any]]:
        templates = self._read().get("templates", [])
        result: list[dict[str, Any]] = []
        for item in templates:
            if not isinstance(item, dict):
                continue
            template = normalize_template(item)
            if profile_name and template["profile"] not in {"", profile_name}:
                continue
            result.append(template)
        return sorted(result, key=lambda item: (item["profile"] != "", item["name"].lower()))

    def save_template(self, payload: dict[str, Any]) -> dict[str, Any]:
        template = normalize_template(payload)
        if not template["name"]:
            raise ValueError("template name is required")
        if not template["command"]:
            raise ValueError("template command is required")
        data = self._read()
        now = utc_now()
        existing: dict[str, Any] | None = None
        for item in data.get("templates", []):
            if isinstance(item, dict) and str(item.get("id", "")) == template["id"]:
                existing = normalize_template(item)
                break
        template["created_at"] = existing.get("created_at", now) if existing else now
        template["updated_at"] = now
        templates = [
            item for item in data.get("templates", []) if not isinstance(item, dict) or str(item.get("id", "")) != template["id"]
        ]
        templates.append(template)
        data["templates"] = templates
        self._write(data)
        return template

    def delete_template(self, template_id: str) -> None:
        if not template_id.strip():
            raise ValueError("template id is required")
        data = self._read()
        templates = [
            item for item in data.get("templates", []) if not isinstance(item, dict) or str(item.get("id", "")) != template_id
        ]
        if len(templates) == len(data.get("templates", [])):
            raise RuntimeError(f"template not found: {template_id}")
        data["templates"] = templates
        self._write(data)

    def record_history(self, payload: dict[str, Any], limit: int = 200) -> dict[str, Any]:
        entry = {
            "id": uuid4().hex,
            "profile": str(payload.get("profile", "")).strip(),
            "target": str(payload.get("target", "")).strip(),
            "alias": str(payload.get("alias", "")).strip(),
            "command": str(payload.get("command", "")).strip(),
            "created_at": utc_now(),
        }
        if not entry["profile"]:
            raise ValueError("history profile is required")
        if not entry["target"]:
            raise ValueError("history target is required")
        if not entry["command"]:
            raise ValueError("history command is required")
        data = self._read()
        history = [entry]
        for item in data.get("history", []):
            if isinstance(item, dict):
                history.append(item)
        data["history"] = history[: max(1, limit)]
        self._write(data)
        return entry

    def list_history(self, profile_name: str = "", limit: int = 20) -> list[dict[str, Any]]:
        history = self._read().get("history", [])
        result: list[dict[str, Any]] = []
        for item in history:
            if not isinstance(item, dict):
                continue
            if profile_name and str(item.get("profile", "")).strip() != profile_name:
                continue
            result.append({
                "id": str(item.get("id", "")).strip(),
                "profile": str(item.get("profile", "")).strip(),
                "target": str(item.get("target", "")).strip(),
                "alias": str(item.get("alias", "")).strip(),
                "command": str(item.get("command", "")).strip(),
                "created_at": str(item.get("created_at", "")).strip(),
            })
            if len(result) >= max(1, limit):
                break
        return result

    def clear_history(self, profile_name: str = "") -> None:
        data = self._read()
        if not profile_name:
            data["history"] = []
        else:
            data["history"] = [
                item
                for item in data.get("history", [])
                if not isinstance(item, dict) or str(item.get("profile", "")).strip() != profile_name
            ]
        self._write(data)

    def list_todos(self, profile_name: str = "", target: str = "", status: str = "") -> list[dict[str, Any]]:
        desired_status = str(status).strip().lower()
        if desired_status and desired_status not in TODO_STATUSES:
            allowed = ", ".join(sorted(TODO_STATUSES))
            raise ValueError(f"todo status must be one of: {allowed}")

        todos = self._read().get("todos", [])
        result: list[dict[str, Any]] = []
        for item in todos:
            if not isinstance(item, dict):
                continue
            todo = normalize_todo(item)
            if profile_name and todo["profile"] != profile_name:
                continue
            if target and todo["target"] != target:
                continue
            if desired_status and todo["status"] != desired_status:
                continue
            result.append(todo)
        return result

    def get_todo(self, todo_id: str) -> dict[str, Any]:
        cleaned_id = str(todo_id).strip()
        if not cleaned_id:
            raise ValueError("todo id is required")
        for todo in self.list_todos():
            if todo["id"] == cleaned_id:
                return todo
        raise RuntimeError(f"todo not found: {cleaned_id}")

    def save_todo(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        todo_id = str(payload.get("id", "")).strip()
        existing: dict[str, Any] | None = None
        for item in data.get("todos", []):
            if isinstance(item, dict) and todo_id and str(item.get("id", "")).strip() == todo_id:
                existing = normalize_todo(item)
                break

        merged: dict[str, Any] = {}
        if existing:
            merged.update(existing)
        merged.update(payload)
        todo = normalize_todo(merged)
        if not todo["title"]:
            raise ValueError("todo title is required")
        if not todo["profile"]:
            raise ValueError("todo profile is required")
        if not todo["target"]:
            raise ValueError("todo target is required")
        if todo["status"] in {"done", "verified"} and not (todo.get("evidence") or []):
            raise ValueError("todo done/verified requires at least one evidence item")
        if todo["status"] == "verified" and not todo.get("verified_at"):
            todo["verified_at"] = utc_now()
            if not todo.get("verified_by"):
                todo["verified_by"] = "reviewer"

        now = utc_now()
        todo["created_at"] = existing.get("created_at", now) if existing else now
        todo["updated_at"] = now
        if not existing and not (todo.get("events") or []):
            create_event = normalize_todo_event(
                {
                    "type": "create",
                    "status": todo["status"],
                    "note": "todo created",
                    "actor": "mobile-user",
                    "created_at": now,
                }
            )
            todo["events"] = [create_event]
        if todo["status"] != "verified":
            if not existing or existing.get("status") != "verified":
                todo["verified_by"] = ""
                todo["verified_at"] = ""

        todos = [
            item for item in data.get("todos", []) if not isinstance(item, dict) or str(item.get("id", "")).strip() != todo["id"]
        ]
        data["todos"] = [todo, *todos]
        self._write(data)
        return todo

    def delete_todo(self, todo_id: str) -> None:
        cleaned_id = str(todo_id).strip()
        if not cleaned_id:
            raise ValueError("todo id is required")
        data = self._read()
        todos = [
            item for item in data.get("todos", []) if not isinstance(item, dict) or str(item.get("id", "")).strip() != cleaned_id
        ]
        if len(todos) == len(data.get("todos", [])):
            raise RuntimeError(f"todo not found: {cleaned_id}")
        data["todos"] = todos
        self._write(data)

    def update_todo_status(self, todo_id: str, status: str, progress_note: str = "", actor: str = "") -> dict[str, Any]:
        todo = self.get_todo(todo_id)
        current_status = str(todo.get("status", "todo")).strip().lower()
        status_value = normalize_todo_status(status)
        note = str(progress_note).strip()
        actor_value = str(actor).strip()
        evidence_count = len(todo.get("evidence", []) or [])
        if status_value in {"done", "verified"} and evidence_count <= 0:
            raise ValueError("cannot set done/verified without evidence")
        if status_value == "verified" and current_status not in {"done", "verified"}:
            raise ValueError("todo can be verified only after it is done")
        todo["status"] = status_value
        if note:
            todo["progress_note"] = note
        if status_value == "verified":
            todo["verified_by"] = actor_value or "reviewer"
            todo["verified_at"] = utc_now()
        event = normalize_todo_event(
            {
                "type": "status",
                "status": status_value,
                "note": note,
                "actor": actor_value,
                "created_at": utc_now(),
            }
        )
        todo["events"] = [event, *(todo.get("events", []) or [])]
        return self.save_todo(todo)

    def append_todo_evidence(self, todo_id: str, evidence: Any, actor: str = "") -> dict[str, Any]:
        todo = self.get_todo(todo_id)
        evidence_item = normalize_todo_evidence(evidence)
        todo["evidence"] = [evidence_item, *(todo.get("evidence", []) or [])]
        note = evidence_item["content"][:120]
        event = normalize_todo_event(
            {
                "type": "evidence",
                "status": todo.get("status", ""),
                "note": note,
                "actor": str(actor).strip(),
                "created_at": evidence_item["created_at"],
            }
        )
        todo["events"] = [event, *(todo.get("events", []) or [])]
        return self.save_todo(todo)

    def todo_summary(self, profile_name: str = "", target: str = "") -> list[dict[str, Any]]:
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        for todo in self.list_todos(profile_name=profile_name, target=target):
            key = (todo["profile"], todo["target"])
            summary = grouped.get(
                key,
                {
                    "profile": todo["profile"],
                    "target": todo["target"],
                    "alias": todo.get("alias", ""),
                    "todo_count": 0,
                    "in_progress_count": 0,
                    "last_updated_at": "",
                    "last_status": "",
                    "last_note": "",
                    "last_actor": "",
                    "last_title": "",
                },
            )
            summary["todo_count"] += 1
            if todo.get("status") == "in_progress":
                summary["in_progress_count"] += 1
            updated_at = str(todo.get("updated_at", "")).strip()
            if updated_at >= str(summary.get("last_updated_at", "")):
                summary["last_updated_at"] = updated_at
                summary["last_status"] = str(todo.get("status", ""))
                summary["last_title"] = str(todo.get("title", ""))
                summary["alias"] = str(todo.get("alias", "")) or str(summary.get("alias", ""))
                events = todo.get("events", []) or []
                if events and isinstance(events[0], dict):
                    summary["last_note"] = str(events[0].get("note", "")).strip()
                    summary["last_actor"] = str(events[0].get("actor", "")).strip()
                else:
                    summary["last_note"] = str(todo.get("progress_note", "")).strip()
            grouped[key] = summary
        return sorted(
            grouped.values(),
            key=lambda item: (str(item.get("last_updated_at", "")), str(item.get("target", ""))),
            reverse=True,
        )

    def list_todo_templates(self, profile_name: str = "", target: str = "") -> list[dict[str, Any]]:
        templates = self._read().get("todo_templates", [])
        result: list[dict[str, Any]] = []
        for item in templates:
            if not isinstance(item, dict):
                continue
            template = normalize_todo_template(item)
            if profile_name and template["profile"] not in {"", profile_name}:
                continue
            if target and template["target"] not in {"", target}:
                continue
            result.append(template)
        return sorted(result, key=lambda item: (item["profile"] != "", item["target"] != "", item["name"].lower()))

    def save_todo_template(self, payload: dict[str, Any]) -> dict[str, Any]:
        template = normalize_todo_template(payload)
        if not template["name"]:
            raise ValueError("todo template name is required")
        if not template["title"]:
            raise ValueError("todo template title is required")
        data = self._read()
        now = utc_now()
        existing: dict[str, Any] | None = None
        for item in data.get("todo_templates", []):
            if isinstance(item, dict) and str(item.get("id", "")) == template["id"]:
                existing = normalize_todo_template(item)
                break
        template["created_at"] = existing.get("created_at", now) if existing else now
        template["updated_at"] = now
        templates = [
            item
            for item in data.get("todo_templates", [])
            if not isinstance(item, dict) or str(item.get("id", "")) != template["id"]
        ]
        templates.append(template)
        data["todo_templates"] = templates
        self._write(data)
        return template

    def delete_todo_template(self, template_id: str) -> None:
        cleaned_id = str(template_id).strip()
        if not cleaned_id:
            raise ValueError("todo template id is required")
        data = self._read()
        templates = [
            item
            for item in data.get("todo_templates", [])
            if not isinstance(item, dict) or str(item.get("id", "")) != cleaned_id
        ]
        if len(templates) == len(data.get("todo_templates", [])):
            raise RuntimeError(f"todo template not found: {cleaned_id}")
        data["todo_templates"] = templates
        self._write(data)

    def record_audit(self, payload: dict[str, Any], limit: int = 2000) -> dict[str, Any]:
        entry = normalize_audit_entry(payload)
        if not entry["action"]:
            raise ValueError("audit action is required")
        data = self._read()
        history = [entry]
        for item in data.get("audit_logs", []):
            if isinstance(item, dict):
                history.append(normalize_audit_entry(item))
        data["audit_logs"] = history[: max(1, limit)]
        self._write(data)
        return entry

    def list_audit_logs(self, profile_name: str = "", target: str = "", limit: int = 100) -> list[dict[str, Any]]:
        logs = self._read().get("audit_logs", [])
        result: list[dict[str, Any]] = []
        for item in logs:
            if not isinstance(item, dict):
                continue
            entry = normalize_audit_entry(item)
            if profile_name and entry["profile"] != profile_name:
                continue
            if target and entry["target"] != target:
                continue
            result.append(entry)
            if len(result) >= max(1, limit):
                break
        return result

    def quick_create_todo(self, payload: dict[str, Any]) -> dict[str, Any]:
        title = str(payload.get("title", "")).strip()
        if not title:
            raise ValueError("todo title is required")
        profile = str(payload.get("profile", "")).strip()
        target = str(payload.get("target", "")).strip()
        if not profile:
            raise ValueError("todo profile is required")
        if not target:
            raise ValueError("todo target is required")
        quick_todo = {
            "title": title,
            "detail": str(payload.get("detail", "")).strip(),
            "profile": profile,
            "target": target,
            "alias": str(payload.get("alias", "")).strip(),
            "priority": str(payload.get("priority", "medium")).strip() or "medium",
            "assignee": str(payload.get("assignee", "")).strip(),
            "role": str(payload.get("role", "general")).strip() or "general",
            "status": "todo",
        }
        handoff = payload.get("handoff_packet", {})
        if isinstance(handoff, dict) and any(str(handoff.get(k, "")).strip() for k in ("context", "constraints", "acceptance", "rollback")):
            quick_todo["handoff_packet"] = handoff
        return self.save_todo(quick_todo)

    def create_workflow_triplet(self, payload: dict[str, Any]) -> dict[str, Any]:
        title = str(payload.get("title", "")).strip()
        profile = str(payload.get("profile", "")).strip()
        if not title:
            raise ValueError("workflow title is required")
        if not profile:
            raise ValueError("workflow profile is required")
        workflow_id = str(payload.get("workflow_id", "")).strip() or uuid4().hex
        default_target = str(payload.get("target", "")).strip()
        if not default_target:
            raise ValueError("workflow target is required")
        handoff_packet = normalize_handoff_packet(payload.get("handoff_packet", {}))
        planner_target = str(payload.get("planner_target", "")).strip() or default_target
        executor_target = str(payload.get("executor_target", "")).strip() or default_target
        reviewer_target = str(payload.get("reviewer_target", "")).strip() or default_target
        priority = normalize_todo_priority(payload.get("priority", "medium"))

        planner = self.save_todo(
            {
                "title": f"[planner] {title}",
                "detail": str(payload.get("detail", "")).strip(),
                "profile": profile,
                "target": planner_target,
                "alias": str(payload.get("planner_alias", "")).strip(),
                "role": "planner",
                "priority": priority,
                "status": "todo",
                "workflow_id": workflow_id,
                "handoff_packet": handoff_packet,
            }
        )
        executor = self.save_todo(
            {
                "title": f"[executor] {title}",
                "detail": str(payload.get("detail", "")).strip(),
                "profile": profile,
                "target": executor_target,
                "alias": str(payload.get("executor_alias", "")).strip(),
                "role": "executor",
                "priority": priority,
                "status": "todo",
                "workflow_id": workflow_id,
                "parent_todo_id": planner["id"],
                "blocked_by": [planner["id"]],
                "handoff_packet": handoff_packet,
            }
        )
        reviewer = self.save_todo(
            {
                "title": f"[reviewer] {title}",
                "detail": str(payload.get("detail", "")).strip(),
                "profile": profile,
                "target": reviewer_target,
                "alias": str(payload.get("reviewer_alias", "")).strip(),
                "role": "reviewer",
                "priority": priority,
                "status": "todo",
                "workflow_id": workflow_id,
                "parent_todo_id": executor["id"],
                "blocked_by": [executor["id"]],
                "handoff_packet": handoff_packet,
            }
        )
        return {"workflow_id": workflow_id, "todos": [planner, executor, reviewer]}

    def list_workflow_todos(self, workflow_id: str) -> list[dict[str, Any]]:
        cleaned = str(workflow_id).strip()
        if not cleaned:
            raise ValueError("workflow_id is required")
        role_order = {"planner": 0, "executor": 1, "reviewer": 2, "general": 3}
        todos = [todo for todo in self.list_todos() if str(todo.get("workflow_id", "")).strip() == cleaned]
        return sorted(
            todos,
            key=lambda item: (role_order.get(str(item.get("role", "general")), 9), str(item.get("created_at", ""))),
        )

    def _share_is_active(self, share: dict[str, Any]) -> bool:
        if str(share.get("revoked_at", "")).strip():
            return False
        expires_at = parse_utc(share.get("expires_at"))
        if expires_at is None:
            return True
        return expires_at > datetime.now(timezone.utc)

    def list_session_shares(self, profile_name: str = "", target: str = "", include_expired: bool = False) -> list[dict[str, Any]]:
        shares = self._read().get("session_shares", [])
        result: list[dict[str, Any]] = []
        for item in shares:
            if not isinstance(item, dict):
                continue
            share = normalize_share_link(item)
            if profile_name and share["profile"] != profile_name:
                continue
            if target and share["target"] != target:
                continue
            if not include_expired and not self._share_is_active(share):
                continue
            result.append(share)
        return result

    def create_session_share(self, payload: dict[str, Any]) -> dict[str, Any]:
        share = normalize_share_link(payload)
        if not share["profile"]:
            raise ValueError("share profile is required")
        if not share["target"]:
            raise ValueError("share target is required")
        if not share["expires_at"]:
            expires_in_minutes = optional_non_negative_int(payload.get("expires_in_minutes", 60), "expires_in_minutes")
            if expires_in_minutes <= 0:
                expires_in_minutes = 60
            share["expires_at"] = (
                datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
            ).isoformat(timespec="seconds").replace("+00:00", "Z")
        now = utc_now()
        share["updated_at"] = now
        data = self._read()
        existing = None
        for item in data.get("session_shares", []):
            if isinstance(item, dict) and str(item.get("id", "")).strip() == share["id"]:
                existing = normalize_share_link(item)
                break
        share["created_at"] = existing.get("created_at", now) if existing else now
        shares = [
            item
            for item in data.get("session_shares", [])
            if not isinstance(item, dict) or str(item.get("id", "")).strip() != share["id"]
        ]
        shares.append(share)
        data["session_shares"] = shares
        self._write(data)
        return share

    def revoke_session_share(self, share_id: str = "", token: str = "") -> dict[str, Any]:
        cleaned_id = str(share_id).strip()
        cleaned_token = str(token).strip()
        if not cleaned_id and not cleaned_token:
            raise ValueError("share id or token is required")
        data = self._read()
        shares = data.get("session_shares", [])
        updated: dict[str, Any] | None = None
        next_shares: list[dict[str, Any]] = []
        for item in shares:
            if not isinstance(item, dict):
                continue
            share = normalize_share_link(item)
            if (cleaned_id and share["id"] == cleaned_id) or (cleaned_token and share["token"] == cleaned_token):
                share["revoked_at"] = utc_now()
                share["updated_at"] = share["revoked_at"]
                updated = share
            next_shares.append(share)
        if not updated:
            raise RuntimeError("share link not found")
        data["session_shares"] = next_shares
        self._write(data)
        return updated

    def resolve_session_share(self, token: str) -> dict[str, Any]:
        cleaned = str(token).strip()
        if not cleaned:
            raise ValueError("share token is required")
        for share in self.list_session_shares(include_expired=True):
            if share["token"] != cleaned:
                continue
            if not self._share_is_active(share):
                raise RuntimeError("share link expired or revoked")
            return share
        raise RuntimeError("share link not found")

    def list_workspace_templates(self, profile_name: str = "", target: str = "") -> list[dict[str, Any]]:
        templates = self._read().get("workspace_templates", [])
        result: list[dict[str, Any]] = []
        for item in templates:
            if not isinstance(item, dict):
                continue
            template = normalize_workspace_template(item)
            if profile_name and template["profile"] not in {"", profile_name}:
                continue
            if target and template["target"] not in {"", target}:
                continue
            result.append(template)
        return sorted(result, key=lambda item: (item["profile"] != "", item["target"] != "", item["name"].lower()))

    def save_workspace_template(self, payload: dict[str, Any]) -> dict[str, Any]:
        template = normalize_workspace_template(payload)
        if not template["name"]:
            raise ValueError("workspace template name is required")
        data = self._read()
        now = utc_now()
        existing = None
        for item in data.get("workspace_templates", []):
            if isinstance(item, dict) and str(item.get("id", "")).strip() == template["id"]:
                existing = normalize_workspace_template(item)
                break
        template["created_at"] = existing.get("created_at", now) if existing else now
        template["updated_at"] = now
        templates = [
            item
            for item in data.get("workspace_templates", [])
            if not isinstance(item, dict) or str(item.get("id", "")).strip() != template["id"]
        ]
        templates.append(template)
        data["workspace_templates"] = templates
        self._write(data)
        return template

    def delete_workspace_template(self, template_id: str) -> None:
        cleaned = str(template_id).strip()
        if not cleaned:
            raise ValueError("workspace template id is required")
        data = self._read()
        templates = [
            item
            for item in data.get("workspace_templates", [])
            if not isinstance(item, dict) or str(item.get("id", "")).strip() != cleaned
        ]
        if len(templates) == len(data.get("workspace_templates", [])):
            raise RuntimeError(f"workspace template not found: {cleaned}")
        data["workspace_templates"] = templates
        self._write(data)

    def list_events(self, profile_name: str = "", target: str = "", limit: int = 200) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for entry in self.list_audit_logs(profile_name=profile_name, target=target, limit=max(1, limit * 2)):
            result.append(
                {
                    "id": entry["id"],
                    "source": "audit",
                    "action": entry["action"],
                    "profile": entry["profile"],
                    "target": entry["target"],
                    "todo_id": entry.get("todo_id", ""),
                    "status": entry.get("status", ""),
                    "actor": entry.get("actor", ""),
                    "note": entry.get("note", ""),
                    "created_at": entry["created_at"],
                }
            )
        for todo in self.list_todos(profile_name=profile_name, target=target):
            for event in todo.get("events", []) or []:
                if not isinstance(event, dict):
                    continue
                normalized_event = normalize_todo_event(event)
                result.append(
                    {
                        "id": normalized_event["id"],
                        "source": "todo",
                        "action": normalized_event["type"],
                        "profile": todo["profile"],
                        "target": todo["target"],
                        "todo_id": todo["id"],
                        "status": normalized_event.get("status", ""),
                        "actor": normalized_event.get("actor", ""),
                        "note": normalized_event.get("note", ""),
                        "created_at": normalized_event["created_at"],
                    }
                )
        sorted_events = sorted(
            result,
            key=lambda item: (str(item.get("created_at", "")), str(item.get("id", ""))),
            reverse=True,
        )
        return sorted_events[: max(1, limit)]

    def workflow_metrics(self, profile_name: str = "", target: str = "", window_days: int = 30) -> dict[str, Any]:
        days = max(1, min(int(window_days), 365))
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        todos = self.list_todos(profile_name=profile_name, target=target)
        dispatch_samples: list[float] = []
        done_samples: list[float] = []
        verify_samples: list[float] = []
        trend: dict[str, dict[str, Any]] = {}

        for todo in todos:
            created_at = parse_utc(todo.get("created_at"))
            if not created_at or created_at < cutoff:
                continue
            in_progress_at: datetime | None = None
            done_at: datetime | None = None
            verified_at: datetime | None = parse_utc(todo.get("verified_at"))
            for event in (todo.get("events", []) or []):
                if not isinstance(event, dict):
                    continue
                event_status = str(event.get("status", "")).strip().lower()
                event_time = parse_utc(event.get("created_at"))
                if event_time is None:
                    continue
                if event_status == "in_progress":
                    in_progress_at = event_time if in_progress_at is None else min(in_progress_at, event_time)
                if event_status == "done":
                    done_at = event_time if done_at is None else min(done_at, event_time)
                if event_status == "verified":
                    verified_at = event_time if verified_at is None else min(verified_at, event_time)
            if in_progress_at and in_progress_at >= created_at:
                dispatch_samples.append((in_progress_at - created_at).total_seconds())
            if done_at and done_at >= created_at:
                done_samples.append((done_at - created_at).total_seconds())
            if verified_at and done_at and verified_at >= done_at:
                verify_samples.append((verified_at - done_at).total_seconds())

            week_key = created_at.strftime("%G-W%V")
            bucket = trend.setdefault(
                week_key,
                {"week": week_key, "dispatch_seconds": [], "done_seconds": [], "verify_seconds": [], "count": 0},
            )
            bucket["count"] += 1
            if in_progress_at and in_progress_at >= created_at:
                bucket["dispatch_seconds"].append((in_progress_at - created_at).total_seconds())
            if done_at and done_at >= created_at:
                bucket["done_seconds"].append((done_at - created_at).total_seconds())
            if verified_at and done_at and verified_at >= done_at:
                bucket["verify_seconds"].append((verified_at - done_at).total_seconds())

        sends = self.list_audit_logs(profile_name=profile_name, target=target, limit=5000)
        send_events = [entry for entry in sends if entry.get("action") == "agent.send"]
        misrouted = 0
        for entry in send_events:
            payload = entry.get("payload", {})
            if isinstance(payload, dict) and bool(payload.get("misroute")):
                misrouted += 1

        trend_rows = []
        for week in sorted(trend.keys()):
            row = trend[week]
            dispatch_avg = sum(row["dispatch_seconds"]) / len(row["dispatch_seconds"]) if row["dispatch_seconds"] else None
            done_avg = sum(row["done_seconds"]) / len(row["done_seconds"]) if row["done_seconds"] else None
            verify_avg = sum(row["verify_seconds"]) / len(row["verify_seconds"]) if row["verify_seconds"] else None
            trend_rows.append(
                {
                    "week": week,
                    "todo_count": row["count"],
                    "t_dispatch_avg_sec": round(dispatch_avg, 1) if dispatch_avg is not None else None,
                    "t_done_avg_sec": round(done_avg, 1) if done_avg is not None else None,
                    "t_verify_avg_sec": round(verify_avg, 1) if verify_avg is not None else None,
                }
            )

        dispatch_avg = sum(dispatch_samples) / len(dispatch_samples) if dispatch_samples else None
        done_avg = sum(done_samples) / len(done_samples) if done_samples else None
        verify_avg = sum(verify_samples) / len(verify_samples) if verify_samples else None
        misroute_rate = (misrouted / len(send_events) * 100.0) if send_events else 0.0
        return {
            "window_days": days,
            "sample_todo_count": len(dispatch_samples) if dispatch_samples else len([todo for todo in todos if parse_utc(todo.get("created_at")) and parse_utc(todo.get("created_at")) >= cutoff]),
            "t_dispatch_avg_sec": round(dispatch_avg, 1) if dispatch_avg is not None else None,
            "t_done_avg_sec": round(done_avg, 1) if done_avg is not None else None,
            "t_verify_avg_sec": round(verify_avg, 1) if verify_avg is not None else None,
            "misroute_pct": round(misroute_rate, 2),
            "trend": trend_rows,
        }
