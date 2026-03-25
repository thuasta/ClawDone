"""Todo runtime and autopilot mixin."""

from __future__ import annotations

from .support import *  # noqa: F401,F403

class ClawDoneTodoMixin:
    def start_background_tasks(self) -> None:
        if not self.todo_autopilot_enabled:
            return
        for token_hash in self._all_configured_token_hashes():
            self._start_user_autopilot(token_hash)

    def _start_user_autopilot(self, token_hash: str) -> None:
        state = self._get_or_create_user_async_state(token_hash)
        if state["thread"] and state["thread"].is_alive():
            return
        state["loop_ready"].clear()
        t = threading.Thread(
            target=self._run_user_async_loop, args=(token_hash,),
            name=f"clawdone-autopilot-{token_hash}", daemon=True,
        )
        state["thread"] = t
        t.start()
        state["loop_ready"].wait(timeout=5.0)

    def _run_user_async_loop(self, token_hash: str) -> None:
        state = self._get_or_create_user_async_state(token_hash)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        state["loop"] = loop
        state["dispatch_lock"] = asyncio.Lock()
        state["sweep_lock"] = asyncio.Lock()
        state["semaphore"] = asyncio.Semaphore(self._dispatch_concurrency)
        stop = asyncio.Event()
        state["stop"] = stop
        # bind this user's store to the autopilot thread's thread-local
        self._thread_local.store = state["store"]
        state["loop_ready"].set()
        try:
            loop.run_until_complete(self._todo_autopilot_loop_for_user_async(token_hash))
        finally:
            loop.close()
            state["loop"] = None

    def stop_background_tasks(self) -> None:
        with self._user_async_state_lock:
            states = list(self._user_async_state.values())
        for state in states:
            loop, stop = state.get("loop"), state.get("stop")
            if loop and loop.is_running() and stop is not None:
                loop.call_soon_threadsafe(stop.set)
        for state in states:
            t = state.get("thread")
            if t and t.is_alive():
                t.join(timeout=5.0)

    def _run_async(self, coro: Any, timeout: float = 30.0) -> Any:
        state = self._current_user_state()
        loop = state["loop"] if state else None
        if loop is not None and loop.is_running():
            return asyncio.run_coroutine_threadsafe(coro, loop).result(timeout=timeout)
        return asyncio.run(coro)

    async def _todo_autopilot_loop_for_user_async(self, token_hash: str) -> None:
        state = self._get_or_create_user_async_state(token_hash)
        stop = state["stop"]
        assert stop is not None
        while not stop.is_set():
            try:
                await self._run_todo_autopilot_cycle_async()
            except Exception:
                logger.exception("autopilot cycle failed")
            try:
                await asyncio.wait_for(asyncio.shield(stop.wait()), timeout=self.todo_autopilot_interval_sec)
            except asyncio.TimeoutError:
                pass

    async def _run_todo_autopilot_cycle_async(self) -> None:
        await self._auto_dispatch_ready_todos_async()
        await self._process_active_todo_reports_async()
        await self._process_supervisor_review_queue_async()

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

    def dispatch_via_mcp(self, mcp_url: str, session: str, command: str) -> None:
        """Send a command to a remote agent via its MCP agent server."""
        url = mcp_url.rstrip("/")
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "send_command",
                "arguments": {"session": session, "command": command, "press_enter": True},
            },
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"MCP agent HTTP {exc.code}") from exc
        if "error" in result:
            raise RuntimeError(f"MCP agent error: {result['error']}")
        content = result.get("result", {}).get("content", [])
        if content and content[0].get("isError"):
            raise RuntimeError(f"MCP agent tool error: {content[0].get('text', '')}")

    def auto_dispatch_todo(self, todo: dict[str, Any] | str, actor: str = "autopilot") -> dict[str, Any]:
        # Phase 1: check eligibility and reserve the todo under lock (fast, no I/O)
        with self._todo_dispatch_lock:
            current = self.store.get_todo(todo) if isinstance(todo, str) else self.store.get_todo(str(todo.get("id", "")))
            alias = current.get("alias", "") or self.store.aliases_for(current["profile"]).get(current["target"], "")
            if str(current.get("status", "")).strip().lower() != "todo":
                return {"dispatched": False, "todo": current, "target": current["target"], "alias": alias, "reason": "status"}
            todos_by_id = {item["id"]: item for item in self.store.list_todos(profile_name=current["profile"])}
            if not self._todo_is_unblocked(current, todos_by_id=todos_by_id):
                return {"dispatched": False, "todo": current, "target": current["target"], "alias": alias, "reason": "blocked"}
            command = self.compose_todo_dispatch_command(current)
            profile = self.get_profile(current["profile"])
            mcp_url = str(profile.get("mcp_url", "")).strip()
            # Reserve: mark in_progress before releasing lock so no other thread double-dispatches
            reserved = self.store.update_todo_status(
                todo_id=current["id"],
                status="in_progress",
                progress_note="Dispatching to agent...",
                actor=actor,
            )

        # Phase 2: blocking I/O outside the lock — SSH or MCP send
        try:
            if mcp_url:
                self.dispatch_via_mcp(mcp_url, session=current["target"], command=command)
            else:
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
                    "payload": {"role": updated.get("role", "general"), "via_mcp": bool(mcp_url)},
                }
            )
            return {"dispatched": True, "todo": updated, "target": updated["target"], "alias": alias, "command": command}
        except Exception as exc:
            # Revert reservation so the todo can be retried
            try:
                self.store.update_todo_status(
                    todo_id=current["id"],
                    status="todo",
                    progress_note=f"Dispatch failed: {str(exc)[:200]}",
                    actor=actor,
                )
            except Exception:
                pass
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
        return self._run_async(self._auto_dispatch_ready_todos_async(profile_name))

    async def _auto_dispatch_ready_todos_async(self, profile_name: str = "") -> list[dict[str, Any]]:
        state = self._current_user_state()
        sweep_lock = state["sweep_lock"] if state else None
        if sweep_lock is None:
            # fallback: no async loop yet, run synchronously
            return self._auto_dispatch_ready_todos_sync(profile_name)
        if sweep_lock.locked():
            return []
        async with sweep_lock:
            todos = await asyncio.to_thread(self.store.list_todos, profile_name)
            todos_by_id = {item["id"]: item for item in todos}
            ordered = sorted(todos, key=lambda item: (str(item.get("created_at", "")), str(item.get("id", ""))))
            eligible = [
                t for t in ordered
                if str(t.get("status", "")).strip().lower() == "todo"
                and self._todo_is_unblocked(t, todos_by_id=todos_by_id)
            ]
            tasks = [self._dispatch_one_async(todo) for todo in eligible]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            dispatched: list[dict[str, Any]] = []
            for result in results:
                if isinstance(result, dict) and result.get("dispatch", {}).get("dispatched"):
                    dispatched.append({**result["dispatch"], "supervisor": result.get("decision")})
            return dispatched

    async def _dispatch_one_async(self, todo: dict[str, Any]) -> dict[str, Any]:
        state = self._current_user_state()
        sem = state["semaphore"] if state else None
        if sem is not None:
            async with sem:
                return await asyncio.to_thread(self.supervisor_route_todo, todo, "supervisor", True)
        return await asyncio.to_thread(self.supervisor_route_todo, todo, "supervisor", True)

    def _auto_dispatch_ready_todos_sync(self, profile_name: str = "") -> list[dict[str, Any]]:
        # Used only when async loop is not yet running (e.g. during tests with autopilot disabled)
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

    def _escape_control_chars_in_json_strings(self, raw_json: str) -> str:
        repaired: list[str] = []
        in_string = False
        escape = False
        for char in raw_json:
            if in_string:
                if escape:
                    repaired.append(char)
                    escape = False
                    continue
                if char == "\\":
                    repaired.append(char)
                    escape = True
                    continue
                if char == '"':
                    repaired.append(char)
                    in_string = False
                    continue
                if char == "\n":
                    repaired.append("\\n")
                    continue
                if char == "\r":
                    repaired.append("\\r")
                    continue
                if char == "\t":
                    repaired.append("\\t")
                    continue
                repaired.append(char)
                continue
            repaired.append(char)
            if char == '"':
                in_string = True
        return "".join(repaired)

    def _decode_todo_report_payload(self, raw_json: str) -> dict[str, Any] | None:
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            repaired = self._escape_control_chars_in_json_strings(raw_json)
            if repaired == raw_json:
                return None
            try:
                payload = json.loads(repaired)
            except json.JSONDecodeError:
                return None
        if not isinstance(payload, dict):
            return None
        normalized: dict[str, Any] = {}
        for key, value in payload.items():
            key_text = str(key)
            collapsed = re.sub(r"\s+", "", key_text).lower()
            normalized_key = REPORT_PAYLOAD_KEY_ALIASES.get(collapsed, key_text)
            normalized[normalized_key] = value
        return normalized

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
            payload = self._decode_todo_report_payload(raw)
            if payload is None:
                cursor = marker_index + len(marker)
                continue
            canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            reports.append({"raw": raw, "payload": payload, "key": canonical})
            cursor = next_index
        return reports

    def _match_inferred_todo(self, line_key: str, candidates: list[tuple[str, dict[str, Any]]], used_ids: set[str]) -> dict[str, Any] | None:
        best: tuple[int, int, dict[str, Any]] | None = None
        for todo_key, todo in candidates:
            todo_id = str(todo.get("id", "")).strip()
            if not todo_key or not todo_id or todo_id in used_ids:
                continue
            if line_key == todo_key:
                score = 4
            elif line_key.startswith(todo_key) or todo_key.startswith(line_key):
                score = 3
            elif line_key in todo_key or todo_key in line_key:
                score = 2
            else:
                continue
            candidate = (score, len(todo_key), todo)
            if best is None or candidate > best:
                best = candidate
        return best[2] if best is not None else None

    def infer_todo_reports(self, profile_name: str, target: str, output: str, skip_todo_ids: set[str] | None = None) -> list[dict[str, Any]]:
        text = str(output or "")
        if not text.strip():
            return []
        candidates = [
            (self._normalize_checklist_item_key(todo.get("title", "")), todo)
            for todo in self.store.list_todos(profile_name=profile_name, target=target)
            if str(todo.get("status", "")).strip().lower() in {"in_progress", "blocked"}
        ]
        candidates = [(key, todo) for key, todo in candidates if key]
        if not candidates:
            return []
        used_ids = {str(item).strip() for item in (skip_todo_ids or set()) if str(item).strip()}
        checked_line = re.compile(r"^\s*(?:[-*•]\s*)?\[(?:x|X)\]\s+(?P<text>.+?)\s*$")
        checklist_line = re.compile(r"^\s*(?:[-*•]\s*)?\[(?: |x|X)?\]\s+")
        reports: list[dict[str, Any]] = []
        lines = text.splitlines()
        for index, raw_line in enumerate(lines):
            match = checked_line.match(raw_line)
            if not match:
                continue
            line_key = self._normalize_checklist_item_key(match.group("text"))
            if not line_key:
                continue
            todo = self._match_inferred_todo(line_key, candidates, used_ids)
            if todo is None:
                continue
            note_lines: list[str] = []
            for follow in lines[index + 1:]:
                stripped = str(follow or "").strip()
                if not stripped:
                    if note_lines:
                        break
                    continue
                if "CLAWDONE_REPORT" in stripped or checklist_line.match(str(follow or "")):
                    break
                note_lines.append(stripped)
                if len(note_lines) >= 6 or len(" ".join(note_lines)) >= 280:
                    break
            note = " ".join(note_lines).strip() or f"Completed {todo.get('title', 'task')}."
            snippet = "\n".join(line for line in [str(raw_line).strip(), *note_lines] if line).strip()
            payload = {
                "todo_id": todo["id"],
                "status": "done",
                "progress_note": note,
                "evidence": {"type": "pane_output", "content": snippet or note},
            }
            key = f"inferred:{todo['id']}:{hashlib.sha1((snippet or note).encode('utf-8')).hexdigest()[:16]}"
            reports.append({"raw": snippet or note, "payload": payload, "key": key})
            used_ids.add(str(todo["id"]))
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
        seen_todo_ids: set[str] = set()
        reports = self.extract_todo_reports(output)
        reports.extend(self.infer_todo_reports(profile_name, target, output))
        for report in reports:
            key = f"{profile_name}:{target}:{report.get('key', report['raw'])}"
            if key in self._report_keys_for_store(self.store):
                continue
            payload = report["payload"]
            todo_id = str(payload.get("todo_id", "")).strip()
            if not todo_id:
                continue
            if todo_id in seen_todo_ids:
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
                self._report_keys_for_store(self.store).add(key)
                continue
            status = str(payload.get("status", "")).strip().lower()
            progress_note = str(payload.get("progress_note", ""))
            evidence = payload.get("evidence")
            if status in FINAL_TODO_STATUSES and evidence in (None, "", []):
                summary = progress_note.strip() or str(payload.get("delivery", "")).strip() or report["raw"]
                evidence = {"type": "summary", "content": summary}
            updated = self.apply_todo_report(todo_id=todo_id, status=status, progress_note=progress_note, evidence=evidence, actor="agent")
            applied.append(updated)
            seen_todo_ids.add(todo_id)
            self._report_keys_for_store(self.store).add(key)
        return applied

    def process_active_todo_reports(self) -> list[dict[str, Any]]:
        return self._run_async(self._process_active_todo_reports_async())

    async def _process_active_todo_reports_async(self) -> list[dict[str, Any]]:
        todos = await asyncio.to_thread(self.store.list_todos)
        active_targets: set[tuple[str, str]] = set()
        for todo in todos:
            status = str(todo.get("status", "")).strip().lower()
            if status not in {"in_progress", "done"}:
                continue
            profile_name = str(todo.get("profile", "")).strip()
            target = str(todo.get("target", "")).strip()
            if profile_name and target:
                active_targets.add((profile_name, target))
        tasks = [self._capture_and_process_async(p, t) for p, t in sorted(active_targets)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [item for r in results if isinstance(r, list) for item in r]

    async def _capture_and_process_async(self, profile_name: str, target: str) -> list[dict[str, Any]]:
        try:
            profile = self.get_profile(profile_name)
            output = await asyncio.to_thread(
                self.remote_tmux.capture_pane, profile, target=target, lines=self.todo_autopilot_lines
            )
        except Exception:
            return []
        # Run in thread to avoid blocking the event loop and to allow apply_todo_report
        # to call auto_dispatch_ready_todos safely (which uses _run_async internally).
        return await asyncio.to_thread(self.process_pane_reports, profile_name, target, output)

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
        _ = self.get_profile(profile_name)
        interval = max(1.0, min(interval_sec, 10.0))
        max_lines = self.parse_pane_lines(lines, default=PANE_CAPTURE_DEFAULT_LINES)

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
