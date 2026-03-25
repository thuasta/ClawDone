"""HTTP route handlers mixin."""

from __future__ import annotations

from .support import *  # noqa: F401,F403

class ClawDoneHttpMixin:
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
            logo_path = Path(__file__).resolve().parents[2] / "assets" / "logo.png"
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

        if parsed.path == "/api/ui-state":
            if identity.get("auth") == "share":
                self.json_response(handler, HTTPStatus.FORBIDDEN, {"error": "share token cannot access ui state"})
                return
            self.json_response(handler, HTTPStatus.OK, {"ui_state": self.store.get_ui_state()})
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
            lines_text = str(query.get("lines", [str(PANE_CAPTURE_DEFAULT_LINES)])[0]).strip()
            interval_text = str(query.get("interval", ["2"])[0]).strip() or "2"
            lines = self.parse_pane_lines(lines_text, default=PANE_CAPTURE_DEFAULT_LINES)
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
            lines_text = str(query.get("lines", [str(PANE_CAPTURE_DEFAULT_LINES)])[0]).strip()
            lines = self.parse_pane_lines(lines_text, default=PANE_CAPTURE_DEFAULT_LINES)
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

        if parsed.path == "/api/ui-state/save":
            if not self.require_role(handler, "operator"):
                return
            ui_state = self.store.save_ui_state(body)
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "ui_state": ui_state})
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

        if parsed.path == "/api/checklist/push":
            if not self.require_role(handler, "operator"):
                return
            profile_name = str(body.get("profile", "")).strip()
            target = str(body.get("target", "")).strip()
            if not self.require_share_scope(handler, profile_name, target):
                return
            result = self.push_checklist(body, actor=actor)
            self.json_response(handler, HTTPStatus.OK, result)
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
            dispatch_requested = bool(body.get("dispatch", True))
            dispatches = self.auto_dispatch_ready_todos(profile_name=todo["profile"]) if (self.todo_autopilot_enabled and dispatch_requested) else []
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
            request_actor = self.require_agent_todo_actor(body.get("actor", ""), actor)
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
            request_actor = self.require_agent_todo_actor(body.get("actor", ""), actor)
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
            request_actor = self.require_agent_todo_actor(body.get("actor", ""), actor)
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
            supervisor_actor = self.require_agent_todo_actor(body.get("actor", ""), actor)
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
                        "actor": supervisor_actor,
                    }
                )
                if auto_send and str(updated.get("status", "")).strip().lower() == "todo":
                    dispatch_result = self.auto_dispatch_todo(updated, actor=supervisor_actor)
                    updated = dispatch_result.get("todo", updated)
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "decision": decision, "todo": updated, "dispatch": dispatch_result})
            return

        if parsed.path == "/api/supervisor/review":
            if not self.require_role(handler, "operator"):
                return
            todo_id = str(body.get("todo_id", "")).strip()
            if not todo_id:
                raise ValueError("todo_id is required")
            supervisor_actor = self.require_agent_todo_actor(body.get("actor", ""), actor)
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
                    updated = self.apply_todo_report(todo_id=todo_id, status=target_status, progress_note=review.get("summary", ""), evidence=evidence, actor=supervisor_actor)
                elif review["verdict"] == "blocked":
                    updated = self.apply_todo_report(todo_id=todo_id, status="blocked", progress_note=review.get("summary", ""), evidence=evidence, actor=supervisor_actor)
                else:
                    updated = self.apply_todo_report(todo_id=todo_id, status="", progress_note=review.get("summary", ""), evidence=evidence, actor=supervisor_actor)
            self.record_audit_safe(
                {
                    "action": "supervisor.review",
                    "profile": updated.get("profile", ""),
                    "target": updated.get("target", ""),
                    "alias": updated.get("alias", ""),
                    "todo_id": updated.get("id", ""),
                    "status": updated.get("status", ""),
                    "note": review.get("summary", ""),
                    "actor": supervisor_actor,
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
            supervisor_actor = self.require_agent_todo_actor(body.get("actor", ""), actor)
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
                updated = self.apply_todo_report(todo_id=todo_id, status="done", progress_note=review.get("summary", ""), evidence=evidence, actor=supervisor_actor)
                evidence = []
            if str(updated.get("status", "")).strip().lower() != "verified":
                updated = self.apply_todo_report(todo_id=todo_id, status="verified", progress_note=review.get("summary", ""), evidence=evidence, actor=supervisor_actor)
            self.record_audit_safe(
                {
                    "action": "supervisor.accept",
                    "profile": updated.get("profile", ""),
                    "target": updated.get("target", ""),
                    "alias": updated.get("alias", ""),
                    "todo_id": updated.get("id", ""),
                    "status": updated.get("status", ""),
                    "note": review.get("summary", ""),
                    "actor": supervisor_actor,
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
            identity = self.identity(handler)
            token = identity.get("token") or ""
            owner_hash = self._user_hash(token) if token else ""
            share = self.store.create_session_share({**body, "created_by": actor, "owner_hash": owner_hash})
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
            self.json_response(
                handler,
                HTTPStatus.OK,
                self._perform_send_command(
                    profile_name=profile_name,
                    target=target,
                    command=cleaned_command,
                    press_enter=press_enter,
                    actor=actor,
                    expected_target=str(body.get("expected_target", "")).strip(),
                    risk=risk,
                ),
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
