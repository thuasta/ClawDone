"""Todo storage mixin."""

from __future__ import annotations

from .normalize import *  # noqa: F401,F403

class ProfileStoreTodoMixin:
    def _list_todos_unlocked(self, profile_name: str = "", target: str = "", status: str = "") -> list[dict[str, Any]]:
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

    def _get_todo_unlocked(self, todo_id: str) -> dict[str, Any]:
        cleaned_id = str(todo_id).strip()
        if not cleaned_id:
            raise ValueError("todo id is required")
        for todo in self._list_todos_unlocked():
            if todo["id"] == cleaned_id:
                return todo
        raise RuntimeError(f"todo not found: {cleaned_id}")

    def _save_todo_unlocked(self, payload: dict[str, Any]) -> dict[str, Any]:
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

    def list_todos(self, profile_name: str = "", target: str = "", status: str = "") -> list[dict[str, Any]]:
        with self._lock:
            return self._list_todos_unlocked(profile_name=profile_name, target=target, status=status)

    def get_todo(self, todo_id: str) -> dict[str, Any]:
        with self._lock:
            return self._get_todo_unlocked(todo_id)

    def save_todo(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            return self._save_todo_unlocked(payload)

    def delete_todo(self, todo_id: str) -> None:
        with self._lock:
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

    def clear_completed_todos(
        self,
        profile_name: str = "",
        target: str = "",
        keep_recent: int = 5,
        min_age_days: int = 0,
    ) -> list[dict[str, Any]]:
        with self._lock:
            profile_value = str(profile_name).strip()
            target_value = str(target).strip()
            keep_recent_value = max(int(keep_recent), 0)
            min_age_days_value = max(int(min_age_days), 0)
            data = self._read()
            scoped_completed: list[dict[str, Any]] = []
            for item in data.get("todos", []):
                if not isinstance(item, dict):
                    continue
                todo = normalize_todo(item)
                matches_scope = (not profile_value or todo["profile"] == profile_value) and (not target_value or todo["target"] == target_value)
                if matches_scope and todo["status"] in {"done", "verified"}:
                    completed_at = parse_utc(todo.get("verified_at")) or parse_utc(todo.get("updated_at")) or parse_utc(todo.get("created_at"))
                    scoped_completed.append({**todo, "_completed_at": completed_at})

            protected_ids = {
                item["id"]
                for item in sorted(
                    scoped_completed,
                    key=lambda todo: (todo.get("_completed_at") or datetime.min.replace(tzinfo=timezone.utc), str(todo.get("updated_at", ""))),
                    reverse=True,
                )[:keep_recent_value]
            }
            cutoff = datetime.now(timezone.utc) - timedelta(days=min_age_days_value)

            removed: list[dict[str, Any]] = []
            remaining: list[Any] = []
            for item in data.get("todos", []):
                if not isinstance(item, dict):
                    remaining.append(item)
                    continue
                todo = normalize_todo(item)
                matches_scope = (not profile_value or todo["profile"] == profile_value) and (not target_value or todo["target"] == target_value)
                if not matches_scope or todo["status"] not in {"done", "verified"}:
                    remaining.append(item)
                    continue
                if todo["id"] in protected_ids:
                    remaining.append(item)
                    continue
                completed_at = parse_utc(todo.get("verified_at")) or parse_utc(todo.get("updated_at")) or parse_utc(todo.get("created_at"))
                if completed_at and completed_at > cutoff:
                    remaining.append(item)
                    continue
                removed.append(todo)

            data["todos"] = remaining
            if removed:
                self._write(data)
            return removed

    def update_todo_status(self, todo_id: str, status: str, progress_note: str = "", actor: str = "") -> dict[str, Any]:
        with self._lock:
            todo = self._get_todo_unlocked(todo_id)
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
            return self._save_todo_unlocked(todo)

    def append_todo_evidence(self, todo_id: str, evidence: Any, actor: str = "") -> dict[str, Any]:
        with self._lock:
            todo = self._get_todo_unlocked(todo_id)
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
            return self._save_todo_unlocked(todo)

    def todo_summary(self, profile_name: str = "", target: str = "") -> list[dict[str, Any]]:
        with self._lock:
            grouped: dict[tuple[str, str], dict[str, Any]] = {}
            for todo in self._list_todos_unlocked(profile_name=profile_name, target=target):
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
        with self._lock:
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
        with self._lock:
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
        with self._lock:
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
        with self._lock:
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
        with self._lock:
            return self._list_audit_logs_unlocked(profile_name=profile_name, target=target, limit=limit)

    def quick_create_todo(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
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
            return self._save_todo_unlocked(quick_todo)

    def create_workflow_triplet(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
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

            planner = self._save_todo_unlocked(
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
            executor = self._save_todo_unlocked(
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
            reviewer = self._save_todo_unlocked(
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
