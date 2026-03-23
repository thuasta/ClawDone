from __future__ import annotations

import io
import json
import os
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from clawdone.app import (
    ProfileStore,
    RemoteTmuxClient,
    SSHExecutor,
    TmuxClient,
    build_parser,
    command_result,
    create_server,
    extract_token,
    mask_profile,
    normalize_config,
    normalize_profile,
)
from clawdone.html import INDEX_HTML
from clawdone.supervisor import SupervisorClient, normalize_supervisor_config
from clawdone.web import ClawDoneApp, render_index_html

SNAPSHOT_CMD = (
    "tmux list-sessions -F '#{session_name}\t#{session_windows}\t#{session_attached}' 2>/dev/null; "
    "echo '---DELIM---'; "
    "tmux list-windows -a -F '#{session_name}\t#{window_index}\t#{window_name}\t#{window_active}' 2>/dev/null; "
    "echo '---DELIM---'; "
    "tmux list-panes -a -F '#{session_name}\t#{window_index}\t#{window_name}\t#{pane_index}\t#{pane_title}\t#{pane_current_command}\t#{pane_active}' 2>/dev/null"
)


def snapshot_response(sessions: str = "", windows: str = "", panes: str = "") -> dict:
    """Build a combined snapshot response from individual parts."""
    stdout = f"{sessions}\n---DELIM---\n{windows}\n---DELIM---\n{panes}"
    return command_result(0, stdout)


class DummyResult:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class DummyHandler:
    def __init__(self, path: str = "/", auth: str | None = None, header_token: str | None = None):
        self.path = path
        self.headers = {}
        if auth is not None:
            self.headers["Authorization"] = auth
        if header_token is not None:
            self.headers["X-ClawDone-Token"] = header_token
        self.rfile = io.BytesIO()


class FakeSSHExecutor:
    def __init__(self, responses: dict[tuple[str, str], dict] | None = None, failures: dict[str, str] | None = None):
        self.responses = responses or {}
        self.failures = failures or {}
        self.commands: list[tuple[str, str]] = []

    def run(self, profile: dict, command: str) -> dict:
        profile_name = str(profile.get("name", ""))
        self.commands.append((profile_name, command))
        if profile_name in self.failures:
            raise RuntimeError(self.failures[profile_name])
        return self.responses.get((profile_name, command), command_result(0, ""))


class FakeSupervisorTransport:
    def __init__(self, responses: list[dict] | None = None):
        self.responses = responses or []
        self.calls: list[dict[str, object]] = []

    def post_json(self, url: str, headers: dict[str, str], payload: dict[str, object], timeout: float) -> dict[str, object]:
        self.calls.append({"url": url, "headers": headers, "payload": payload, "timeout": timeout})
        if self.responses:
            return self.responses.pop(0)
        return {"choices": [{"message": {"content": "{}"}}]}


class TmuxClientTests(unittest.TestCase):
    def test_list_sessions_parses_output(self) -> None:
        calls: list[list[str]] = []

        def runner(command: list[str], **_: object) -> DummyResult:
            calls.append(command)
            return DummyResult(stdout="codex\nbackend\n")

        client = TmuxClient(runner=runner)
        self.assertEqual(client.list_sessions(), ["codex", "backend"])
        self.assertEqual(calls[0], ["tmux", "list-sessions", "-F", "#{session_name}"])

    def test_send_keys_issues_literal_then_enter(self) -> None:
        calls: list[list[str]] = []

        def runner(command: list[str], **_: object) -> DummyResult:
            calls.append(command)
            return DummyResult()

        client = TmuxClient(runner=runner)
        client.send_keys("codex", "run tests", press_enter=True)
        self.assertEqual(
            calls,
            [
                ["tmux", "send-keys", "-t", "codex", "-l", "run tests"],
                ["tmux", "send-keys", "-t", "codex", "Enter"],
            ],
        )

    def test_list_sessions_handles_missing_server(self) -> None:
        def runner(command: list[str], **_: object) -> DummyResult:
            _ = command
            return DummyResult(returncode=1, stderr="no server running on /tmp/tmux-1000/default")

        client = TmuxClient(runner=runner)
        self.assertEqual(client.list_sessions(), [])

    def test_send_keys_requires_command(self) -> None:
        client = TmuxClient(runner=lambda *args, **kwargs: DummyResult())
        with self.assertRaises(ValueError):
            client.send_keys("codex", "")


class RenderIndexHtmlTests(unittest.TestCase):
    def test_render_index_html_marks_requested_view_on_buttons(self) -> None:
        html = render_index_html('todo')
        self.assertIn('<div class="page-view active" id="view-todo">', html)
        self.assertIn('<button class="tab-button active" type="button" data-view-button="todo">', html)
        self.assertNotIn('href="/?view=todo"', html)


class HtmlTests(unittest.TestCase):
    def test_tabbar_uses_buttons_without_navigation_href(self) -> None:
        self.assertIn('<button class="tab-button active" type="button" data-view-button="dashboard">Home</button>', INDEX_HTML)
        self.assertNotIn('href="/?view=dashboard"', INDEX_HTML)

    def test_chat_view_uses_chatbot_ui_style_layout(self) -> None:
        self.assertIn('<section class="chatbot-layout">', INDEX_HTML)
        self.assertIn('<aside class="chat-sidebar">', INDEX_HTML)
        self.assertIn('<section class="chat-main">', INDEX_HTML)
        self.assertIn('<h2>Work</h2>', INDEX_HTML)
        self.assertNotIn('Chatbot UI Inspired', INDEX_HTML)
        self.assertIn('data-fold-key="dashboard-targets"', INDEX_HTML)
        self.assertIn('data-fold-key="settings-access"', INDEX_HTML)
        self.assertIn('data-fold-key="delivery-summary"', INDEX_HTML)
        self.assertIn('<div class="chatbot-sidebar-title">Agents</div>', INDEX_HTML)
        self.assertIn('class="worker-avatar"', INDEX_HTML)
        self.assertIn('id="todoBoard" class="todo-board"', INDEX_HTML)
        self.assertIn('id="clearCompletedTodos"', INDEX_HTML)
        self.assertIn('Checklist', INDEX_HTML)
        self.assertNotIn('Choose profile → session → window → pane first.', INDEX_HTML)

    def test_runtime_js_keeps_escaped_newline_sequences(self) -> None:
        self.assertIn("split(/\\n+/)", INDEX_HTML)
        self.assertIn("join('\\n')", INDEX_HTML)
        self.assertIn("split('\\n')", INDEX_HTML)
        self.assertIn("endsWith('\\n')", INDEX_HTML)


class ProfileStoreTests(unittest.TestCase):
    def test_save_list_and_alias_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            profile = {"name": "office", "host": "10.0.0.1", "username": "ubuntu", "password": "secret", "group": "work", "tags": "gpu, research", "favorite": True}
            saved = store.save_profile(profile)
            store.set_alias("office", "codex:1.0", "backend-agent")

            self.assertEqual(saved["group"], "work")
            self.assertEqual(saved["tags"], ["gpu", "research"])
            self.assertTrue(saved["favorite"])
            self.assertEqual(store.aliases_for("office"), {"codex:1.0": "backend-agent"})

    def test_save_profile_preserves_existing_password_when_blank(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu", "password": "secret"})
            store.save_profile({"name": "office", "host": "10.0.0.2", "username": "ubuntu", "password": ""})
            saved = store.get_profile("office")
            self.assertEqual(saved["host"], "10.0.0.2")
            self.assertEqual(saved["password"], "secret")

    def test_templates_and_history_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})
            template = store.save_template({"name": "Quick Fix", "command": "fix bug and run tests", "profile": "office"})
            store.record_history({"profile": "office", "target": "codex:0.0", "alias": "backend", "command": "fix auth"})

            self.assertEqual(store.list_templates("office")[0]["id"], template["id"])
            self.assertEqual(store.list_history("office", limit=10)[0]["alias"], "backend")
            store.delete_template(template["id"])
            self.assertEqual(store.list_templates("office"), [])
            store.clear_history("office")
            self.assertEqual(store.list_history("office", limit=10), [])

    def test_delete_profile_removes_related_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})
            template = store.save_template({"name": "Quick Fix", "command": "fix bug", "profile": "office"})
            store.record_history({"profile": "office", "target": "codex:0.0", "command": "fix auth"})
            store.set_alias("office", "codex:1.0", "backend-agent")
            store.delete_profile("office")

            self.assertEqual(store.list_profiles(), [])
            self.assertEqual(store.aliases_for("office"), {})
            self.assertEqual(store.list_templates("office"), [])
            self.assertEqual(store.list_history("office", limit=10), [])
            self.assertTrue(template["id"])

    def test_save_profile_rejects_invalid_host_key_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            with self.assertRaises(ValueError):
                store.save_profile(
                    {"name": "office", "host": "10.0.0.1", "username": "ubuntu", "host_key_policy": "invalid"}
                )

    def test_todo_crud_status_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})
            created = store.save_todo(
                {
                    "title": "Fix flaky auth test",
                    "detail": "stabilize retries and assert token refresh",
                    "profile": "office",
                    "target": "codex:0.0",
                    "alias": "backend",
                    "priority": "high",
                    "assignee": "backend-agent",
                }
            )

            listed = store.list_todos(profile_name="office", target="codex:0.0")
            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0]["id"], created["id"])

            updated = store.update_todo_status(
                todo_id=created["id"],
                status="in_progress",
                progress_note="started reproducing locally",
                actor="agent",
            )
            self.assertEqual(updated["status"], "in_progress")
            self.assertEqual(updated["progress_note"], "started reproducing locally")
            self.assertEqual(updated["events"][0]["type"], "status")

            evidenced = store.append_todo_evidence(
                todo_id=created["id"],
                evidence={"type": "pane_output", "content": "pytest tests/test_auth.py passed", "source": "capture-pane"},
                actor="agent",
            )
            self.assertEqual(evidenced["evidence"][0]["type"], "pane_output")
            self.assertIn("pytest", evidenced["evidence"][0]["content"])

            store.delete_todo(created["id"])
            self.assertEqual(store.list_todos(profile_name="office"), [])

    def test_todo_validation_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})
            with self.assertRaises(ValueError):
                store.save_todo({"title": "", "profile": "office", "target": "codex:0.0"})
            with self.assertRaises(ValueError):
                store.save_todo({"title": "x", "profile": "office", "target": "codex:0.0", "status": "bad"})
            todo = store.save_todo({"title": "ok", "profile": "office", "target": "codex:0.0"})
            with self.assertRaises(ValueError):
                store.update_todo_status(todo["id"], "invalid")
            with self.assertRaises(ValueError):
                store.append_todo_evidence(todo["id"], "")

    def test_todo_summary_templates_and_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})
            created = store.save_todo(
                {
                    "title": "Implement retries",
                    "profile": "office",
                    "target": "codex:0.0",
                    "alias": "backend",
                    "status": "in_progress",
                }
            )
            store.record_audit(
                {
                    "action": "todo.create",
                    "profile": "office",
                    "target": "codex:0.0",
                    "todo_id": created["id"],
                    "actor": "mobile-user",
                }
            )
            template = store.save_todo_template(
                {
                    "name": "Bugfix",
                    "title": "Fix production bug",
                    "detail": "include tests and summary",
                    "priority": "high",
                    "profile": "office",
                    "target": "codex:0.0",
                }
            )

            summary = store.todo_summary(profile_name="office")
            self.assertEqual(summary[0]["in_progress_count"], 1)
            self.assertEqual(summary[0]["target"], "codex:0.0")
            self.assertEqual(store.list_todo_templates("office", "codex:0.0")[0]["id"], template["id"])
            self.assertEqual(store.list_audit_logs(profile_name="office", target="codex:0.0", limit=10)[0]["action"], "todo.create")

    def test_todo_done_and_verified_require_evidence_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})
            todo = store.save_todo({"title": "Evidence contract", "profile": "office", "target": "codex:0.0"})
            with self.assertRaises(ValueError):
                store.update_todo_status(todo["id"], "done", actor="agent")

            store.append_todo_evidence(todo["id"], {"type": "pane_output", "content": "tests passed"}, actor="agent")
            done = store.update_todo_status(todo["id"], "done", progress_note="ready for review", actor="agent")
            self.assertEqual(done["status"], "done")
            verified = store.update_todo_status(todo["id"], "verified", actor="reviewer")
            self.assertEqual(verified["status"], "verified")
            self.assertEqual(verified["verified_by"], "reviewer")
            self.assertTrue(verified["verified_at"])

    def test_clear_completed_todos_scopes_to_profile_and_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})
            store.save_profile({"name": "lab", "host": "10.0.0.2", "username": "ubuntu"})

            todo_keep_profile = store.save_todo({"title": "Keep other profile", "profile": "lab", "target": "codex:0.0"})
            todo_keep_target = store.save_todo({"title": "Keep other target", "profile": "office", "target": "codex:0.1"})
            todo_todo = store.save_todo({"title": "Keep open", "profile": "office", "target": "codex:0.0"})
            todo_done = store.save_todo({"title": "Done task", "profile": "office", "target": "codex:0.0"})
            todo_verified = store.save_todo({"title": "Verified task", "profile": "office", "target": "codex:0.0"})

            store.append_todo_evidence(todo_done["id"], {"type": "summary", "content": "done"}, actor="agent")
            store.update_todo_status(todo_done["id"], "done", actor="agent")
            store.append_todo_evidence(todo_verified["id"], {"type": "summary", "content": "verified"}, actor="agent")
            store.update_todo_status(todo_verified["id"], "done", actor="agent")
            store.update_todo_status(todo_verified["id"], "verified", actor="reviewer")

            removed = store.clear_completed_todos(profile_name="office", target="codex:0.0", keep_recent=0, min_age_days=0)
            self.assertEqual({item["id"] for item in removed}, {todo_done["id"], todo_verified["id"]})
            remaining_ids = {item["id"] for item in store.list_todos()}
            self.assertIn(todo_keep_profile["id"], remaining_ids)
            self.assertIn(todo_keep_target["id"], remaining_ids)
            self.assertIn(todo_todo["id"], remaining_ids)
            self.assertNotIn(todo_done["id"], remaining_ids)
            self.assertNotIn(todo_verified["id"], remaining_ids)

    def test_clear_completed_todos_keeps_recent_items_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})

            completed_ids: list[str] = []
            for index in range(7):
                todo = store.save_todo({"title": f"Completed {index}", "profile": "office", "target": "codex:0.0"})
                store.append_todo_evidence(todo["id"], {"type": "summary", "content": f"done {index}"}, actor="agent")
                updated = store.update_todo_status(todo["id"], "done", actor="agent")
                completed_ids.append(updated["id"])

            removed = store.clear_completed_todos(profile_name="office", target="codex:0.0")
            self.assertEqual(len(removed), 2)
            remaining_completed = [todo for todo in store.list_todos(profile_name="office", target="codex:0.0") if todo["status"] in {"done", "verified"}]
            self.assertEqual(len(remaining_completed), 5)

    def test_save_and_mask_supervisor_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})
            saved = store.save_supervisor_config(
                {
                    "name": "Project Supervisor",
                    "profile": "office",
                    "base_url": "https://api.openai.com/v1",
                    "model": "gpt-4.1-mini",
                    "api_key": "secret-key",
                    "permissions": ["dispatch", "review", "accept"],
                }
            )
            self.assertEqual(saved["profile"], "office")
            masked = store.get_supervisor_config(profile_name="office")
            self.assertEqual(masked["api_key"], "secret-key")
            updated = store.save_supervisor_config({"id": saved["id"], "name": "Project Supervisor", "profile": "office", "api_key": ""})
            self.assertEqual(updated["api_key"], "secret-key")
            store.delete_supervisor_config(saved["id"])
            self.assertEqual(store.list_supervisor_configs("office"), [])

    def test_triplet_workflow_events_metrics_and_share_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})

            workflow = store.create_workflow_triplet(
                {
                    "title": "Fix release blocker",
                    "detail": "triage, patch, verify",
                    "profile": "office",
                    "target": "codex:0.0",
                    "handoff_packet": {
                        "context": "auth regression",
                        "constraints": "keep API shape",
                        "acceptance": "tests green",
                        "rollback": "revert patch",
                    },
                }
            )
            todos = store.list_workflow_todos(workflow["workflow_id"])
            self.assertEqual([todo["role"] for todo in todos], ["planner", "executor", "reviewer"])

            first = todos[0]
            store.append_todo_evidence(first["id"], {"type": "summary", "content": "investigation done"}, actor="planner")
            store.update_todo_status(first["id"], "in_progress", actor="planner")
            store.update_todo_status(first["id"], "done", actor="planner")
            store.update_todo_status(first["id"], "verified", actor="reviewer")

            events = store.list_events(profile_name="office", target="codex:0.0", limit=50)
            self.assertTrue(any(event["source"] == "todo" for event in events))

            metrics = store.workflow_metrics(profile_name="office", target="codex:0.0", window_days=30)
            self.assertIn("misroute_pct", metrics)
            self.assertIn("trend", metrics)

            share = store.create_session_share({"profile": "office", "target": "codex:0.0", "permission": "read"})
            resolved = store.resolve_session_share(share["token"])
            self.assertEqual(resolved["target"], "codex:0.0")

            workspace = store.save_workspace_template(
                {
                    "name": "python-workspace",
                    "profile": "office",
                    "target": "codex:0.0",
                    "bootstrap_command": "uv sync",
                }
            )
            self.assertEqual(store.list_workspace_templates("office", "codex:0.0")[0]["id"], workspace["id"])

    def test_app_auto_dispatches_and_ingests_agent_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})
            executor = FakeSSHExecutor()
            app = ClawDoneApp(
                {"store_path": str(Path(temp_dir) / "profiles.json"), "todo_autopilot": False},
                store=store,
                remote_tmux=RemoteTmuxClient(executor=executor),
            )
            todo = store.save_todo({"title": "Fix auth flaky test", "detail": "run tests and summarize", "profile": "office", "target": "codex:0.0"})

            dispatch = app.auto_dispatch_todo(todo)
            self.assertTrue(dispatch["dispatched"])
            self.assertEqual(dispatch["todo"]["status"], "in_progress")
            self.assertTrue(any("tmux send-keys -t codex:0.0 -l" in command for _, command in executor.commands))
            self.assertTrue(any(command.endswith(" Enter") for _, command in executor.commands))

            report = json.dumps(
                {
                    "todo_id": todo["id"],
                    "status": "done",
                    "progress_note": "implemented fix and tests passed",
                    "evidence": [{"type": "summary", "content": "patched auth retry logic and verified the flaky test"}],
                }
            )
            applied = app.process_pane_reports("office", "codex:0.0", f"ready\nCLAWDONE_REPORT {report}\n")
            self.assertEqual(len(applied), 1)
            updated = store.get_todo(todo["id"])
            self.assertEqual(updated["status"], "done")
            self.assertEqual(updated["evidence"][0]["type"], "summary")

            app.process_pane_reports("office", "codex:0.0", f"ready\nCLAWDONE_REPORT {report}\n")
            deduped = store.get_todo(todo["id"])
            self.assertEqual(len(deduped["evidence"]), 1)

    def test_app_ingests_wrapped_agent_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})
            app = ClawDoneApp(
                {"store_path": str(Path(temp_dir) / "profiles.json"), "todo_autopilot": False},
                store=store,
                remote_tmux=RemoteTmuxClient(executor=FakeSSHExecutor()),
            )
            todo = store.save_todo({"title": "Wrap report", "profile": "office", "target": "codex:0.0"})
            store.update_todo_status(todo["id"], "in_progress", actor="autopilot")

            wrapped_report = """CLAWDONE_REPORT {
  "todo_id": "%s",
  "status": "done",
  "progress_note": "wrapped report applied",
  "evidence": [{"type": "summary", "content": "verified from wrapped output"}]
}
""" % todo["id"]
            applied = app.process_pane_reports("office", "codex:0.0", wrapped_report)
            self.assertEqual(len(applied), 1)
            updated = store.get_todo(todo["id"])
            self.assertEqual(updated["status"], "done")
            self.assertEqual(updated["progress_note"], "wrapped report applied")

    def test_auto_dispatch_todo_does_not_double_send_under_race(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})

            class SlowExecutor(FakeSSHExecutor):
                def run(self, profile: dict, command: str) -> dict:
                    if "send-keys" in command and " -l " in command:
                        time.sleep(0.1)
                    return super().run(profile, command)

            executor = SlowExecutor()
            app = ClawDoneApp(
                {"store_path": str(Path(temp_dir) / "profiles.json"), "todo_autopilot": False},
                store=store,
                remote_tmux=RemoteTmuxClient(executor=executor),
            )
            todo = store.save_todo({"title": "Race dispatch", "profile": "office", "target": "codex:0.0"})
            threads = [threading.Thread(target=app.auto_dispatch_todo, args=(todo["id"],)) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            sent = [command for _, command in executor.commands if "send-keys" in command and " -l " in command]
            self.assertEqual(len(sent), 1)
            self.assertEqual(store.get_todo(todo["id"])["status"], "in_progress")

    def test_app_auto_dispatches_next_workflow_agent_when_unblocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})
            executor = FakeSSHExecutor()
            app = ClawDoneApp(
                {"store_path": str(Path(temp_dir) / "profiles.json"), "todo_autopilot": False},
                store=store,
                remote_tmux=RemoteTmuxClient(executor=executor),
            )
            workflow = store.create_workflow_triplet(
                {
                    "title": "Release blocker",
                    "detail": "plan, fix, verify",
                    "profile": "office",
                    "target": "codex:0.0",
                    "planner_target": "codex:0.0",
                    "executor_target": "codex:0.1",
                    "reviewer_target": "codex:0.2",
                }
            )
            todos = store.list_workflow_todos(workflow["workflow_id"])
            planner = todos[0]
            executor_todo = todos[1]

            dispatched = app.auto_dispatch_ready_todos(profile_name="office")
            self.assertEqual(len(dispatched), 1)
            self.assertEqual(dispatched[0]["todo"]["id"], planner["id"])
            self.assertEqual(store.get_todo(planner["id"])["status"], "in_progress")
            self.assertEqual(store.get_todo(executor_todo["id"])["status"], "todo")

            planner_report = json.dumps(
                {
                    "todo_id": planner["id"],
                    "status": "done",
                    "progress_note": "plan complete",
                    "evidence": [{"type": "summary", "content": "implementation plan prepared"}],
                }
            )
            app.process_pane_reports("office", "codex:0.0", f"CLAWDONE_REPORT {planner_report}\n")
            self.assertEqual(store.get_todo(executor_todo["id"])["status"], "in_progress")
            self.assertTrue(any("codex:0.1" in command for _, command in executor.commands))


class SupervisorModuleTests(unittest.TestCase):
    def test_normalize_supervisor_config_defaults(self) -> None:
        config = normalize_supervisor_config({"name": "Supervisor"})
        self.assertEqual(config["provider"], "openai_compatible")
        self.assertIn("dispatch", config["permissions"])
        self.assertTrue(config["auto_dispatch"])
        self.assertTrue(config["auto_review"])
        self.assertTrue(config["auto_accept"])

    def test_supervisor_dispatch_parses_openai_compatible_response(self) -> None:
        transport = FakeSupervisorTransport(
            responses=[
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "target": "codex:0.1",
                                        "alias": "backend",
                                        "reason": "backend agent matches the bugfix scope",
                                        "confidence": 0.92,
                                    }
                                )
                            }
                        }
                    ]
                }
            ]
        )
        client = SupervisorClient(transport=transport)
        config = normalize_supervisor_config({"api_key": "sk-test"})
        decision = client.dispatch(
            config=config,
            todo={"title": "Fix flaky auth test", "detail": "patch retries and rerun tests", "role": "general", "priority": "high"},
            candidates=[
                {"target": "codex:0.0", "alias": "frontend", "session": "codex", "window_name": "ui", "command": "node"},
                {"target": "codex:0.1", "alias": "backend", "session": "codex", "window_name": "api", "command": "python"},
            ],
        )
        self.assertEqual(decision["target"], "codex:0.1")
        self.assertEqual(decision["alias"], "backend")
        self.assertGreater(decision["confidence"], 0.9)

    def test_supervisor_review_parses_verdict(self) -> None:
        transport = FakeSupervisorTransport(
            responses=[
                {
                    "choices": [
                        {
                            "message": {
                                "content": json.dumps(
                                    {
                                        "verdict": "accept",
                                        "summary": "Tests passed and evidence is sufficient.",
                                        "required_fixes": [],
                                        "evidence": [{"type": "summary", "content": "validated by supervisor"}],
                                    }
                                )
                            }
                        }
                    ]
                }
            ]
        )
        client = SupervisorClient(transport=transport)
        config = normalize_supervisor_config({"api_key": "sk-test"})
        review = client.review(
            config=config,
            todo={"title": "Ship patch", "detail": "", "status": "done", "progress_note": "all green", "evidence": [{"type": "summary", "content": "tests passed"}]},
            pane_output="pytest passed",
        )
        self.assertEqual(review["verdict"], "accept")
        self.assertEqual(review["evidence"][0]["type"], "summary")


    def test_app_supervisor_auto_routes_pending_todo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})
            store.save_supervisor_config(
                {
                    "name": "Supervisor",
                    "profile": "office",
                    "api_key": "sk-test",
                    "auto_dispatch": True,
                    "auto_review": False,
                    "auto_accept": False,
                }
            )
            executor = FakeSSHExecutor()
            app = ClawDoneApp(
                {"store_path": str(Path(temp_dir) / "profiles.json"), "todo_autopilot": False},
                store=store,
                remote_tmux=RemoteTmuxClient(executor=executor),
            )
            app.supervisor_client = SupervisorClient(
                transport=FakeSupervisorTransport(
                    responses=[
                        {
                            "choices": [
                                {
                                    "message": {
                                        "content": json.dumps(
                                            {
                                                "target": "codex:0.1",
                                                "alias": "backend",
                                                "reason": "best match",
                                                "confidence": 0.95,
                                            }
                                        )
                                    }
                                }
                            ]
                        }
                    ]
                )
            )
            app.list_supervisor_candidates = lambda profile_name: [
                {"target": "codex:0.0", "alias": "frontend", "session": "codex", "window_name": "ui", "command": "node"},
                {"target": "codex:0.1", "alias": "backend", "session": "codex", "window_name": "api", "command": "python"},
            ]
            todo = store.save_todo({"title": "Fix flaky auth", "detail": "backend work", "profile": "office", "target": "codex:0.0"})
            dispatched = app.auto_dispatch_ready_todos(profile_name="office")
            self.assertEqual(len(dispatched), 1)
            updated = store.get_todo(todo["id"])
            self.assertEqual(updated["target"], "codex:0.1")
            self.assertEqual(updated["status"], "in_progress")
            self.assertTrue(any("codex:0.1" in command for _, command in executor.commands))

    def test_app_supervisor_auto_reviews_and_accepts_done_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})
            store.save_supervisor_config(
                {
                    "name": "Supervisor",
                    "profile": "office",
                    "api_key": "sk-test",
                    "auto_dispatch": False,
                    "auto_review": True,
                    "auto_accept": True,
                }
            )
            executor = FakeSSHExecutor()
            app = ClawDoneApp(
                {"store_path": str(Path(temp_dir) / "profiles.json"), "todo_autopilot": False},
                store=store,
                remote_tmux=RemoteTmuxClient(executor=executor),
            )
            app.supervisor_client = SupervisorClient(
                transport=FakeSupervisorTransport(
                    responses=[
                        {
                            "choices": [
                                {
                                    "message": {
                                        "content": json.dumps(
                                            {
                                                "verdict": "accept",
                                                "summary": "delivery verified by supervisor",
                                                "required_fixes": [],
                                                "evidence": [{"type": "summary", "content": "supervisor accepted the delivery"}],
                                            }
                                        )
                                    }
                                }
                            ]
                        }
                    ]
                )
            )
            todo = store.save_todo({"title": "Ship patch", "profile": "office", "target": "codex:0.0"})
            store.append_todo_evidence(todo["id"], {"type": "summary", "content": "tests passed"}, actor="agent")
            updated = app.apply_todo_report(todo_id=todo["id"], status="done", progress_note="delivery complete", evidence=None, actor="agent")
            self.assertEqual(updated["status"], "verified")
            logs = store.list_audit_logs(profile_name="office", target="codex:0.0", limit=20)
            actions = {entry["action"] for entry in logs if entry.get("todo_id") == todo["id"]}
            self.assertIn("supervisor.auto_review", actions)
            self.assertIn("supervisor.auto_accept", actions)



class RemoteTmuxClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = {"name": "office", "host": "10.0.0.1", "username": "ubuntu", "port": 22, "tmux_bin": "tmux", "group": "work", "favorite": True, "tags": ["gpu"]}

    def test_snapshot_builds_nested_sessions_windows_and_panes(self) -> None:
        executor = FakeSSHExecutor(
            responses={
                ("office", SNAPSHOT_CMD): snapshot_response(
                    sessions="codex\t2\t1",
                    windows="codex\t0\tmain\t1\ncodex\t1\tlogs\t0",
                    panes="codex\t0\tmain\t0\t\tcodex\t1\ncodex\t1\tlogs\t0\t\tbash\t1",
                ),
            }
        )
        client = RemoteTmuxClient(executor=executor)

        snapshot = client.snapshot(self.profile, aliases={"codex:0.0": "frontend-agent"})
        self.assertEqual(snapshot["profile"], "office")
        self.assertEqual(len(snapshot["sessions"]), 1)
        self.assertEqual(snapshot["sessions"][0]["name"], "codex")
        self.assertEqual(snapshot["sessions"][0]["windows"][0]["panes"][0]["alias"], "frontend-agent")
        self.assertEqual(snapshot["sessions"][0]["windows"][0]["panes"][0]["target"], "codex:0.0")

    def test_send_keys_quotes_target_and_command(self) -> None:
        executor = FakeSSHExecutor(
            responses={
                ("office", "tmux send-keys -t codex:0.0 -l 'run tests && summarize'"): command_result(0),
                ("office", "tmux send-keys -t codex:0.0 Enter"): command_result(0),
            }
        )
        client = RemoteTmuxClient(executor=executor)
        client.send_keys(self.profile, "codex:0.0", "run tests && summarize")
        self.assertEqual(
            executor.commands,
            [
                ("office", "tmux send-keys -t codex:0.0 -l 'run tests && summarize'"),
                ("office", "tmux send-keys -t codex:0.0 Enter"),
            ],
        )

    def test_inspect_profile_handles_online_and_offline(self) -> None:
        online_executor = FakeSSHExecutor(
            responses={
                ("office", SNAPSHOT_CMD): snapshot_response(
                    sessions="codex\t1\t1",
                    windows="codex\t0\tmain\t1",
                    panes="codex\t0\tmain\t0\t\tcodex\t1",
                ),
            }
        )
        offline_executor = FakeSSHExecutor(failures={"office": "network down"})

        self.assertTrue(RemoteTmuxClient(executor=online_executor).inspect_profile(self.profile)["online"])
        offline = RemoteTmuxClient(executor=offline_executor).inspect_profile(self.profile)
        self.assertFalse(offline["online"])
        self.assertIn("network down", offline["error"])

    def test_dashboard_aggregates_multiple_targets(self) -> None:
        executor = FakeSSHExecutor(
            responses={
                ("office", SNAPSHOT_CMD): snapshot_response(
                    sessions="codex\t1\t1",
                    windows="codex\t0\tmain\t1",
                    panes="codex\t0\tmain\t0\t\tcodex\t1",
                ),
            },
            failures={"lab": "offline"},
        )
        client = RemoteTmuxClient(executor=executor)
        dashboard = client.dashboard([self.profile, {"name": "lab", "host": "10.0.0.2", "username": "root", "port": 22, "tmux_bin": "tmux", "group": "lab", "favorite": False, "tags": []}])
        self.assertEqual(len(dashboard["targets"]), 2)
        self.assertEqual(sorted(dashboard["groups"]), ["lab", "work"])

    def test_dashboard_preserves_profile_order_with_parallel_workers(self) -> None:
        class SlowRemoteTmuxClient(RemoteTmuxClient):
            def inspect_profile(self, profile: dict[str, Any], aliases: dict[str, str] | None = None) -> dict[str, Any]:
                _ = aliases
                time.sleep(float(profile.get("delay", 0)))
                return {
                    "name": profile["name"],
                    "group": profile.get("group", "General"),
                    "tags": [],
                    "favorite": False,
                    "description": "",
                    "host": profile.get("host", ""),
                    "online": True,
                    "error": "",
                    "latency_ms": 0.0,
                    "session_count": 0,
                    "window_count": 0,
                    "pane_count": 0,
                    "sessions": [],
                }

        client = SlowRemoteTmuxClient(executor=FakeSSHExecutor(), dashboard_workers=4)
        profiles = [
            {"name": "alpha", "group": "g1", "delay": 0.12},
            {"name": "beta", "group": "g2", "delay": 0.01},
            {"name": "gamma", "group": "g3", "delay": 0.05},
        ]
        dashboard = client.dashboard(profiles)
        self.assertEqual([target["name"] for target in dashboard["targets"]], ["alpha", "beta", "gamma"])
        self.assertEqual(dashboard["groups"], ["g1", "g2", "g3"])


class AuthTests(unittest.TestCase):
    def test_extract_token_from_bearer_header(self) -> None:
        handler = DummyHandler(auth="Bearer secret")
        self.assertEqual(extract_token(handler), "secret")

    def test_extract_token_from_query_string(self) -> None:
        handler = DummyHandler(path="/api/sessions?token=query-secret")
        self.assertEqual(extract_token(handler), "query-secret")

class NormalizationTests(unittest.TestCase):
    def test_normalize_profile_and_mask_profile(self) -> None:
        profile = normalize_profile({"name": "office", "host": "1.1.1.1", "username": "ubuntu", "tags": "gpu, gpu, work", "favorite": 1, "password": "secret"})
        self.assertEqual(profile["tags"], ["gpu", "work"])
        masked = mask_profile(profile)
        self.assertEqual(masked["password"], "")
        self.assertTrue(masked["has_password"])

    def test_normalize_profile_supports_optional_ssh_overrides(self) -> None:
        profile = normalize_profile(
            {
                "name": "office",
                "host": "1.1.1.1",
                "username": "ubuntu",
                "host_key_policy": "ACCEPT-NEW",
                "ssh_timeout": "12",
                "ssh_command_timeout": "19",
                "ssh_retries": "2",
                "ssh_retry_backoff_ms": "350",
            }
        )
        self.assertEqual(profile["host_key_policy"], "accept-new")
        self.assertEqual(profile["ssh_timeout"], 12)
        self.assertEqual(profile["ssh_command_timeout"], 19)
        self.assertEqual(profile["ssh_retries"], 2)
        self.assertEqual(profile["ssh_retry_backoff_ms"], 350)

    def test_normalize_profile_rejects_negative_retry(self) -> None:
        with self.assertRaises(ValueError):
            normalize_profile({"name": "office", "host": "1.1.1.1", "username": "ubuntu", "ssh_retries": -1})


class ConfigTests(unittest.TestCase):
    def test_normalize_config_defaults_and_validation(self) -> None:
        config = normalize_config({})
        self.assertEqual(config["host_key_policy"], "strict")
        self.assertEqual(config["dashboard_workers"], 6)

        with self.assertRaises(ValueError):
            normalize_config({"host_key_policy": "invalid"})
        with self.assertRaises(ValueError):
            normalize_config({"ssh_timeout": 0})
        with self.assertRaises(ValueError):
            normalize_config({"ssh_retries": -1})


class SSHExecutorTests(unittest.TestCase):
    def test_ssh_executor_rejects_invalid_policy(self) -> None:
        with self.assertRaises(ValueError):
            SSHExecutor(host_key_policy="invalid")

    def test_ssh_executor_treats_zero_timeout_override_as_inherit(self) -> None:
        executor = SSHExecutor(connect_timeout=9, command_timeout=14)
        self.assertEqual(executor._resolve_positive_float(0, fallback=executor.connect_timeout, field_name="ssh_timeout"), 9)
        self.assertEqual(executor._resolve_positive_float("0", fallback=executor.command_timeout, field_name="ssh_command_timeout"), 14)

    def test_ssh_executor_resolves_password_ref_from_env(self) -> None:
        executor = SSHExecutor()
        with patch.dict(os.environ, {"CLAWDONE_TEST_PWD": "secret-from-env"}, clear=False):
            password = executor._resolve_profile_password({"password_ref": "env:CLAWDONE_TEST_PWD"})
        self.assertEqual(password, "secret-from-env")


class ParserTests(unittest.TestCase):
    def test_send_parser_keeps_subcommand_and_command_text(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["send", "--session", "codex", "--command", "hello world"])
        self.assertEqual(args.subcommand, "send")
        self.assertEqual(args.command_text, "hello world")


class WebIntegrationTests(unittest.TestCase):
    def _request_json(
        self,
        url: str,
        token: str | None,
        method: str = "GET",
        body: dict | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict:
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if extra_headers:
            headers.update(extra_headers)
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        request = Request(url, headers=headers, method=method, data=data)
        return json.loads(urlopen(request, timeout=2).read().decode("utf-8"))

    def _request_error_status(
        self,
        url: str,
        token: str | None,
        method: str = "GET",
        body: dict | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> int:
        headers: dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if extra_headers:
            headers.update(extra_headers)
        data = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode("utf-8")
        request = Request(url, headers=headers, method=method, data=data)
        try:
            urlopen(request, timeout=2)
        except HTTPError as exc:
            return int(exc.code)
        return 0

    def test_dashboard_profiles_templates_and_history_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "profiles.json"
            store = ProfileStore(store_path)
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu", "password": "secret", "favorite": True, "group": "work"})
            store.save_profile({"name": "lab", "host": "10.0.0.2", "username": "root", "group": "lab"})
            store.set_alias("office", "codex:0.0", "backend")
            store.save_template({"name": "Summarize", "command": "summarize latest changes", "profile": "office"})
            executor = FakeSSHExecutor(
                responses={
                    ("office", SNAPSHOT_CMD): snapshot_response(
                        sessions="codex\t1\t1",
                        windows="codex\t0\tmain\t1",
                        panes="codex\t0\tmain\t0\t\tcodex\t1",
                    ),
                    ("office", "tmux capture-pane -p -t codex:0.0 -S -120"): command_result(0, "ready"),
                    ("office", "tmux send-keys -t codex:0.0 -l 'fix auth and run tests'"): command_result(0),
                    ("office", "tmux send-keys -t codex:0.0 Enter"): command_result(0),
                },
                failures={"lab": "offline"},
            )
            server = create_server(
                {"host": "127.0.0.1", "port": 8893, "token": "secret", "store_path": str(store_path)},
                store=store,
                remote_tmux=RemoteTmuxClient(executor=executor),
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            time.sleep(0.2)
            try:
                profiles = self._request_json("http://127.0.0.1:8893/api/profiles", "secret")
                self.assertEqual(len(profiles["profiles"]), 2)
                self.assertEqual(profiles["profiles"][0]["password"], "")
                self.assertTrue(profiles["profiles"][0]["has_password"])

                dashboard = self._request_json("http://127.0.0.1:8893/api/dashboard", "secret")
                self.assertEqual(dashboard["profile_count"], 2)
                self.assertEqual(dashboard["online_count"], 1)

                templates = self._request_json("http://127.0.0.1:8893/api/templates?profile=office", "secret")
                self.assertEqual(templates["templates"][0]["name"], "Summarize")

                send = self._request_json(
                    "http://127.0.0.1:8893/api/send",
                    "secret",
                    method="POST",
                    body={"profile": "office", "target": "codex:0.0", "command": "fix auth and run tests", "press_enter": True},
                )
                self.assertEqual(send["alias"], "backend")
                self.assertEqual(
                    self._request_error_status(
                        "http://127.0.0.1:8893/api/send",
                        "secret",
                        method="POST",
                        body={"profile": "office", "target": "codex:0.0", "command": "   ", "press_enter": True},
                    ),
                    400,
                )

                history = self._request_json("http://127.0.0.1:8893/api/history?profile=office&limit=5", "secret")
                self.assertEqual(history["history"][0]["command"], "fix auth and run tests")

                pane = self._request_json("http://127.0.0.1:8893/api/pane?profile=office&target=codex%3A0.0", "secret")
                self.assertEqual(pane["output"], "ready")

                created_todo = self._request_json(
                    "http://127.0.0.1:8893/api/todos",
                    "secret",
                    method="POST",
                    body={
                        "title": "Fix auth flaky test",
                        "detail": "collect evidence and summarize",
                        "profile": "office",
                        "target": "codex:0.0",
                        "alias": "backend",
                        "priority": "high",
                        "assignee": "backend-agent",
                    },
                )
                todo_id = created_todo["todo"]["id"]
                todos = self._request_json(
                    "http://127.0.0.1:8893/api/todos?profile=office&target=codex%3A0.0",
                    "secret",
                )
                self.assertEqual(todos["todos"][0]["id"], todo_id)

                status_update = self._request_json(
                    "http://127.0.0.1:8893/api/todos/status",
                    "secret",
                    method="POST",
                    body={"todo_id": todo_id, "status": "in_progress", "progress_note": "running tests", "actor": "agent"},
                )
                self.assertEqual(status_update["todo"]["status"], "in_progress")

                evidence_update = self._request_json(
                    "http://127.0.0.1:8893/api/todos/evidence",
                    "secret",
                    method="POST",
                    body={"todo_id": todo_id, "evidence": {"type": "pane_output", "content": "tests passed"}, "actor": "agent"},
                )
                self.assertEqual(evidence_update["todo"]["evidence"][0]["type"], "pane_output")

                report_update = self._request_json(
                    "http://127.0.0.1:8893/api/todos/report",
                    "secret",
                    method="POST",
                    body={
                        "todo_id": todo_id,
                        "status": "done",
                        "progress_note": "all checks green",
                        "evidence": {"type": "summary", "content": "implemented and verified"},
                        "actor": "agent",
                    },
                )
                self.assertEqual(report_update["todo"]["status"], "done")
                self.assertGreaterEqual(len(report_update["todo"]["evidence"]), 2)

                refreshed_dashboard = self._request_json("http://127.0.0.1:8893/api/dashboard", "secret")
                office_target = next(item for item in refreshed_dashboard["targets"] if item["name"] == "office")
                self.assertIn("todo_summary", office_target)
                self.assertEqual(office_target["todo_summary"]["agent_count"], 1)

                summaries = self._request_json(
                    "http://127.0.0.1:8893/api/todos/summary?profile=office&target=codex%3A0.0",
                    "secret",
                )
                self.assertEqual(summaries["summaries"][0]["target"], "codex:0.0")

                saved_todo_template = self._request_json(
                    "http://127.0.0.1:8893/api/todo-templates/save",
                    "secret",
                    method="POST",
                    body={
                        "name": "Bugfix",
                        "title": "Fix auth bug",
                        "detail": "write tests and summarize",
                        "priority": "high",
                        "profile": "office",
                        "target": "codex:0.0",
                    },
                )
                template_id = saved_todo_template["template"]["id"]
                listed_todo_templates = self._request_json(
                    "http://127.0.0.1:8893/api/todo-templates?profile=office&target=codex%3A0.0",
                    "secret",
                )
                self.assertEqual(listed_todo_templates["templates"][0]["id"], template_id)
                self._request_json(
                    "http://127.0.0.1:8893/api/todo-templates/delete",
                    "secret",
                    method="POST",
                    body={"id": template_id},
                )

                audit = self._request_json("http://127.0.0.1:8893/api/audit?profile=office&target=codex%3A0.0&limit=20", "secret")
                actions = {item["action"] for item in audit["logs"]}
                self.assertIn("todo.create", actions)
                self.assertIn("agent.send", actions)
            finally:
                server.shutdown()
                server.server_close()

    def test_workflow_quicktask_rbac_risk_and_share_scope_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store_path = Path(temp_dir) / "profiles.json"
            store = ProfileStore(store_path)
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})
            store.set_alias("office", "codex:0.0", "backend")
            executor = FakeSSHExecutor(
                responses={
                    ("office", "tmux capture-pane -p -t codex:0.0 -S -120"): command_result(0, "ready"),
                }
            )
            server = create_server(
                {
                    "host": "127.0.0.1",
                    "port": 8894,
                    "store_path": str(store_path),
                    "rbac_tokens": {
                        "admin-token": "admin",
                        "op-token": "operator",
                        "view-token": "viewer",
                    },
                    "risk_policy": "confirm",
                },
                store=store,
                remote_tmux=RemoteTmuxClient(executor=executor),
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            time.sleep(0.2)
            try:
                # viewer can read but cannot mutate
                _ = self._request_json("http://127.0.0.1:8894/api/dashboard", "view-token")
                forbidden = self._request_error_status(
                    "http://127.0.0.1:8894/api/profiles/save",
                    "view-token",
                    method="POST",
                    body={"name": "new", "host": "1.1.1.1", "username": "root"},
                )
                self.assertEqual(forbidden, 403)

                # quick task endpoint
                quick = self._request_json(
                    "http://127.0.0.1:8894/api/todos/quick",
                    "op-token",
                    method="POST",
                    body={"title": "quick fix", "profile": "office", "target": "codex:0.0"},
                )
                todo_id = quick["todo"]["id"]
                self.assertTrue(todo_id)

                # risk gate requires explicit confirmation for dangerous command
                blocked = self._request_error_status(
                    "http://127.0.0.1:8894/api/send",
                    "op-token",
                    method="POST",
                    body={"profile": "office", "target": "codex:0.0", "command": "rm -rf /tmp/demo", "press_enter": True},
                )
                self.assertEqual(blocked, 400)
                allowed = self._request_json(
                    "http://127.0.0.1:8894/api/send",
                    "op-token",
                    method="POST",
                    body={
                        "profile": "office",
                        "target": "codex:0.0",
                        "command": "rm -rf /tmp/demo",
                        "press_enter": True,
                        "confirm_risk": True,
                    },
                )
                self.assertEqual(allowed["risk"]["level"], "high")

                workflow = self._request_json(
                    "http://127.0.0.1:8894/api/workflows/triplet",
                    "op-token",
                    method="POST",
                    body={
                        "title": "workflow demo",
                        "detail": "planner/executor/reviewer",
                        "profile": "office",
                        "target": "codex:0.0",
                        "handoff_packet": {
                            "context": "issue context",
                            "constraints": "keep compatibility",
                            "acceptance": "tests pass",
                            "rollback": "revert patch",
                        },
                    },
                )
                self.assertEqual(len(workflow["todos"]), 3)

                metrics = self._request_json(
                    "http://127.0.0.1:8894/api/workflow/metrics?profile=office&target=codex%3A0.0&days=30",
                    "op-token",
                )
                self.assertIn("misroute_pct", metrics["metrics"])

                events = self._request_json(
                    "http://127.0.0.1:8894/api/events?profile=office&target=codex%3A0.0&limit=20",
                    "op-token",
                )
                self.assertTrue(events["events"])

                workspace = self._request_json(
                    "http://127.0.0.1:8894/api/workspace-templates/save",
                    "op-token",
                    method="POST",
                    body={
                        "name": "workspace-a",
                        "profile": "office",
                        "target": "codex:0.0",
                        "bootstrap_command": "uv sync",
                    },
                )
                self.assertEqual(workspace["template"]["name"], "workspace-a")

                share = self._request_json(
                    "http://127.0.0.1:8894/api/session-shares/create",
                    "admin-token",
                    method="POST",
                    body={"profile": "office", "target": "codex:0.0", "permission": "read", "expires_in_minutes": 30},
                )
                share_token = share["share"]["token"]
                pane = self._request_json(
                    "http://127.0.0.1:8894/api/pane?profile=office&target=codex%3A0.0",
                    token=None,
                    extra_headers={"X-ClawDone-Share-Token": share_token},
                )
                self.assertEqual(pane["output"], "ready")

                share_forbidden = self._request_error_status(
                    "http://127.0.0.1:8894/api/send",
                    token=None,
                    method="POST",
                    body={"profile": "office", "target": "codex:0.0", "command": "echo hi", "press_enter": True},
                    extra_headers={"X-ClawDone-Share-Token": share_token},
                )
                self.assertEqual(share_forbidden, 403)
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
