"""Supervisor and routing mixin."""

from __future__ import annotations

from .support import *  # noqa: F401,F403

class ClawDoneSupervisorMixin:
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

    def process_supervisor_review_queue(self) -> list[dict[str, Any]]:
        return self._run_async(self._process_supervisor_review_queue_async())

    async def _process_supervisor_review_queue_async(self) -> list[dict[str, Any]]:
        todos = await asyncio.to_thread(self.store.list_todos)
        candidates = [
            t for t in todos
            if str(t.get("status", "")).strip().lower() in FINAL_TODO_STATUSES
        ]
        tasks = [asyncio.to_thread(self.maybe_run_supervisor_review, t, "supervisor") for t in candidates]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, dict)]
