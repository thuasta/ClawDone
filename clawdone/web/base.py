"""Core web app mixin."""

from __future__ import annotations

from .support import *  # noqa: F401,F403
from .support import _is_client_disconnect

class ClawDoneBaseMixin:
    def __init__(
        self,
        config: dict[str, Any],
        tmux_client: TmuxClient | None = None,
        store: ProfileStore | None = None,
        remote_tmux: RemoteTmuxClient | None = None,
    ):
        self.config = normalize_config(config)
        self.tmux = tmux_client or TmuxClient(tmux_bin=self.config["tmux_bin"])
        self._injected_store: ProfileStore | None = store
        self._user_stores: dict[str, ProfileStore] = {}
        self._user_stores_lock = threading.Lock()
        self._thread_local = threading.local()
        # per-user async state: token_hash -> {"loop", "thread", "loop_ready", "stop",
        #   "dispatch_lock", "sweep_lock", "semaphore", "store"}
        self._user_async_state: dict[str, dict[str, Any]] = {}
        self._user_async_state_lock = threading.Lock()
        self._processed_report_keys_by_user: dict[str, set[str]] = {}
        self._processed_report_keys_lock = threading.Lock()
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
        self._dispatch_concurrency = int(self.config.get("dispatch_concurrency", 8))
        self._todo_dispatch_lock = threading.Lock()
        if self.config["default_role"] not in ROLE_LEVELS:
            self.config["default_role"] = "admin"
        self._html_cache: dict[str, str] = {}
        self._html_cache_gzipped: dict[str, bytes] = {}
        for view in INDEX_VIEWS:
            html = render_index_html(view)
            self._html_cache[view] = html
            self._html_cache_gzipped[view] = gzip.compress(html.encode("utf-8"))
        self._migrate_store_if_needed()

    @property
    def store(self) -> ProfileStore:
        if self._injected_store is not None:
            return self._injected_store
        s = getattr(self._thread_local, "store", None)
        if s is not None:
            return s
        raise RuntimeError("no store bound to current thread")

    @staticmethod
    def _user_hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()[:8]

    def _user_store_path(self, token_hash: str) -> Path:
        base = Path(self.config["store_path"]).expanduser().parent
        return base / "users" / f"{token_hash}.json"

    def _get_or_create_user_store(self, token_hash: str) -> ProfileStore:
        with self._user_stores_lock:
            if token_hash not in self._user_stores:
                self._user_stores[token_hash] = ProfileStore(self._user_store_path(token_hash))
            return self._user_stores[token_hash]

    def _resolve_user_store(self, identity: dict[str, Any]) -> ProfileStore:
        if identity.get("auth") == "share":
            share = identity.get("share") or {}
            owner_hash = str(share.get("owner_hash", "")).strip()
            if owner_hash:
                return self._get_or_create_user_store(owner_hash)
            return self._find_store_for_share(str(share.get("token", "")))
        token = identity.get("token")
        if token:
            return self._get_or_create_user_store(self._user_hash(token))
        raise RuntimeError("cannot resolve store: no token in identity")

    def _find_store_for_share(self, share_token: str) -> ProfileStore:
        # Search cached stores first, then scan users/ dir
        if self._injected_store is not None:
            try:
                self._injected_store.resolve_session_share(share_token)
                return self._injected_store
            except (ValueError, RuntimeError):
                pass
        with self._user_stores_lock:
            stores = list(self._user_stores.values())
        for s in stores:
            try:
                s.resolve_session_share(share_token)
                return s
            except (ValueError, RuntimeError):
                continue
        users_dir = Path(self.config["store_path"]).expanduser().parent / "users"
        if users_dir.is_dir():
            for json_file in users_dir.glob("*.json"):
                s = self._get_or_create_user_store(json_file.stem)
                try:
                    s.resolve_session_share(share_token)
                    return s
                except (ValueError, RuntimeError):
                    continue
        raise RuntimeError("share link not found")

    def _report_keys_for_store(self, store: ProfileStore) -> set[str]:
        key = str(store.path)
        with self._processed_report_keys_lock:
            if key not in self._processed_report_keys_by_user:
                self._processed_report_keys_by_user[key] = set()
            return self._processed_report_keys_by_user[key]

    def _all_configured_token_hashes(self) -> list[str]:
        rbac_tokens = self.config.get("rbac_tokens", {}) or {}
        if rbac_tokens:
            return [self._user_hash(t) for t in rbac_tokens]
        token = self.config.get("token")
        return [self._user_hash(token)] if token else []

    def _migrate_store_if_needed(self) -> None:
        if self._injected_store is not None:
            return
        store_path = Path(self.config["store_path"]).expanduser()
        users_dir = store_path.parent / "users"
        if not store_path.exists() or users_dir.exists():
            return
        import shutil
        users_dir.mkdir(parents=True, exist_ok=True)
        for token_hash in self._all_configured_token_hashes():
            dest = self._user_store_path(token_hash)
            if not dest.exists():
                shutil.copy2(str(store_path), str(dest))

    def _get_or_create_user_async_state(self, token_hash: str) -> dict[str, Any]:
        with self._user_async_state_lock:
            if token_hash not in self._user_async_state:
                self._user_async_state[token_hash] = {
                    "loop": None, "thread": None,
                    "loop_ready": threading.Event(), "stop": None,
                    "dispatch_lock": None, "sweep_lock": None, "semaphore": None,
                    "store": self._get_or_create_user_store(token_hash),
                }
            return self._user_async_state[token_hash]

    def _current_user_state(self) -> dict[str, Any] | None:
        s = getattr(self._thread_local, "store", None)
        if s is None:
            return None
        store_path = str(s.path)
        with self._user_async_state_lock:
            for state in self._user_async_state.values():
                if str(state["store"].path) == store_path:
                    return state
        return None

    def parse_pane_lines(self, raw_value: Any, *, default: int = PANE_CAPTURE_DEFAULT_LINES) -> int:
        if raw_value is None:
            return default
        text = str(raw_value).strip()
        if not text:
            return default
        try:
            parsed = int(text)
        except (TypeError, ValueError) as exc:
            raise ValueError("lines must be an integer") from exc
        return max(PANE_CAPTURE_MIN_LINES, min(parsed, PANE_CAPTURE_MAX_LINES))

    def _accepts_gzip(self, handler: BaseHTTPRequestHandler) -> bool:
        return "gzip" in handler.headers.get("Accept-Encoding", "")

    def json_response(self, handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        use_gzip = len(data) > 1024 and self._accepts_gzip(handler)
        if use_gzip:
            data = gzip.compress(data)
        try:
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
        except OSError as exc:
            if _is_client_disconnect(exc):
                return
            raise

    def html_response(self, handler: BaseHTTPRequestHandler, html: str, gzipped: bytes | None = None) -> None:
        try:
            handler.send_response(HTTPStatus.OK)
            if gzipped is not None and self._accepts_gzip(handler):
                data = gzipped
                handler.send_header("Content-Type", "text/html; charset=utf-8")
                handler.send_header("Content-Length", str(len(data)))
                handler.send_header("Content-Encoding", "gzip")
            else:
                data = html.encode("utf-8")
                handler.send_header("Content-Type", "text/html; charset=utf-8")
                handler.send_header("Content-Length", str(len(data)))
            handler.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            handler.send_header("Pragma", "no-cache")
            handler.send_header("Expires", "0")
            handler.end_headers()
            handler.wfile.write(data)
        except OSError as exc:
            if _is_client_disconnect(exc):
                return
            raise

    def binary_response(self, handler: BaseHTTPRequestHandler, status: int, payload: bytes, content_type: str) -> None:
        try:
            handler.send_response(status)
            handler.send_header("Content-Type", content_type)
            handler.send_header("Content-Length", str(len(payload)))
            handler.send_header("Cache-Control", "public, max-age=3600")
            handler.end_headers()
            handler.wfile.write(payload)
        except OSError as exc:
            if _is_client_disconnect(exc):
                return
            raise

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
                # Open mode: no token configured — reject in multi-user mode.
                return {"auth": "open_rejected", "token": None, "role": "admin", "share": None}

        share_token = extract_share_token(handler)
        if share_token:
            try:
                share = self._find_store_for_share(share_token).resolve_session_share(share_token)
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
        if identity.get("auth") == "open_rejected":
            self.json_response(handler, HTTPStatus.UNAUTHORIZED, {"error": "token required for multi-user mode"})
            return False
        setattr(handler, "_clawdone_identity", identity)
        if self._injected_store is None:
            self._thread_local.store = self._resolve_user_store(identity)
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

    def require_agent_todo_actor(self, requested_actor: Any, default_actor: str = "") -> str:
        actor = str(requested_actor).strip() or str(default_actor).strip()
        if not actor:
            raise ValueError("todo updates must include an agent actor")
        if actor.lower() in {"mobile-user", "shared-user"}:
            raise ValueError("task editing, status updates, and evidence are handled by the agent")
        return actor

    @staticmethod
    def _normalize_checklist_item_key(value: Any) -> str:
        return " ".join(str(value or "").strip().lower().split())

    @staticmethod
    def _clean_checklist_line(raw_line: Any) -> tuple[str, bool]:
        original = str(raw_line or "").strip()
        if not original:
            return "", False
        cleaned = CHECKLIST_LINE_PREFIX.sub("", original).strip()
        return cleaned, cleaned != original

    def parse_checklist_text(self, raw_text: Any) -> list[dict[str, str]]:
        list_items: list[str] = []
        prose_lines: list[str] = []
        seen_list_keys: set[str] = set()

        for raw_line in str(raw_text or "").splitlines():
            cleaned, had_prefix = self._clean_checklist_line(raw_line)
            if not cleaned:
                continue
            key = self._normalize_checklist_item_key(cleaned)
            if not key or key in CHECKLIST_NOISE_KEYS:
                continue
            if had_prefix:
                if key in seen_list_keys:
                    continue
                seen_list_keys.add(key)
                list_items.append(cleaned)
                continue
            prose_lines.append(cleaned)

        if list_items:
            return [{"title": item[:140], "detail": ""} for item in list_items if item[:140].strip()]

        if not prose_lines:
            return []

        title = prose_lines[0]
        detail_parts = prose_lines[1:]
        if len(title) > 140:
            detail_parts = [title[140:], *detail_parts]
            title = title[:140]
        return [{"title": title.strip(), "detail": "\n".join(part for part in detail_parts if part).strip()}]

    @staticmethod
    def compose_checklist_dispatch_command(items: list[str]) -> str:
        cleaned = [str(item).strip() for item in items if str(item).strip()]
        return "\n".join(
            [
                "Work through this checklist. Mark items complete as you finish them and report progress when blocked.",
                "",
                *[f"- [ ] {item}" for item in cleaned],
            ]
        ).strip()

    def _perform_send_command(
        self,
        *,
        profile_name: str,
        target: str,
        command: str,
        press_enter: bool,
        actor: str,
        expected_target: str = "",
        risk: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cleaned_command = str(command).strip()
        if not cleaned_command:
            raise ValueError("command is required")
        profile = self.get_profile(profile_name)
        alias = self.store.aliases_for(profile_name).get(target, "")
        resolved_risk = risk or {"level": "low", "matched": []}
        self.store.record_history({"profile": profile_name, "target": target, "alias": alias, "command": cleaned_command})
        self.remote_tmux.send_keys(profile, target=target, command=cleaned_command, press_enter=press_enter)
        misroute = bool(expected_target and expected_target != target)
        self.record_audit_safe(
            {
                "action": "agent.send",
                "profile": profile_name,
                "target": target,
                "alias": alias,
                "note": cleaned_command[:200],
                "actor": actor,
                "payload": {"risk": resolved_risk, "misroute": misroute},
            }
        )
        return {
            "ok": True,
            "profile": profile_name,
            "target": target,
            "alias": alias,
            "risk": resolved_risk,
            "misroute": misroute,
        }

    def _send_command_worker(self, store: ProfileStore, payload: dict[str, Any]) -> None:
        self._thread_local.store = store
        try:
            self._perform_send_command(**payload)
        except Exception as exc:
            self.record_audit_safe(
                {
                    "action": "agent.send_error",
                    "profile": str(payload.get("profile_name", "")).strip(),
                    "target": str(payload.get("target", "")).strip(),
                    "note": str(exc)[:200],
                    "actor": str(payload.get("actor", "")).strip(),
                }
            )

    async def _queue_send_command_async(self, store: ProfileStore, payload: dict[str, Any]) -> None:
        await asyncio.to_thread(self._send_command_worker, store, payload)

    def queue_send_command(
        self,
        *,
        profile_name: str,
        target: str,
        command: str,
        press_enter: bool,
        actor: str,
        expected_target: str = "",
        risk: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        store = self.store
        payload = {
            "profile_name": profile_name,
            "target": target,
            "command": command,
            "press_enter": press_enter,
            "actor": actor,
            "expected_target": expected_target,
            "risk": risk,
        }
        state = self._current_user_state()
        loop = state["loop"] if state else None
        if loop is not None and loop.is_running():
            asyncio.run_coroutine_threadsafe(self._queue_send_command_async(store, payload), loop)
            return {"queued": True, "mode": "user-loop", "target": target}
        worker = threading.Thread(
            target=self._send_command_worker,
            args=(store, payload),
            name=f"clawdone-send-{profile_name}-{target}",
            daemon=True,
        )
        worker.start()
        return {"queued": True, "mode": "thread", "target": target}

    def push_checklist(self, payload: dict[str, Any], actor: str) -> dict[str, Any]:
        profile_name = str(payload.get("profile", "")).strip()
        target = str(payload.get("target", "")).strip()
        if not profile_name:
            raise ValueError("profile is required")
        if not target:
            raise ValueError("target is required")

        alias = str(payload.get("alias", "")).strip()
        priority = str(payload.get("priority", "medium")).strip() or "medium"
        assignee = str(payload.get("assignee", "")).strip()
        role = str(payload.get("role", "general")).strip() or "general"
        dispatch_requested = bool(payload.get("dispatch", False))

        parsed_items = self.parse_checklist_text(payload.get("raw_text", ""))
        todos = self.store.list_todos(profile_name=profile_name, target=target)
        open_todos = [
            todo for todo in todos if str(todo.get("status", "")).strip().lower() not in FINAL_TODO_STATUSES
        ]
        existing_by_key = {
            self._normalize_checklist_item_key(todo.get("title", "")): todo
            for todo in open_todos
            if self._normalize_checklist_item_key(todo.get("title", ""))
        }

        created: list[dict[str, Any]] = []
        skipped = 0
        dispatch_items: list[str] = []
        seen_dispatch_keys: set[str] = set()
        dispatch_candidates: list[dict[str, Any]] = []
        dispatch_candidate_ids: set[str] = set()

        for item in parsed_items:
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            key = self._normalize_checklist_item_key(title)
            if not key or key in seen_dispatch_keys:
                continue
            seen_dispatch_keys.add(key)
            dispatch_items.append(title)
            if key in existing_by_key:
                existing = existing_by_key[key]
                if dispatch_requested and str(existing.get("status", "")).strip().lower() == "todo" and existing.get("id") not in dispatch_candidate_ids:
                    dispatch_candidates.append(existing)
                    dispatch_candidate_ids.add(existing["id"])
                skipped += 1
                continue
            todo = self.store.quick_create_todo(
                {
                    "title": title,
                    "detail": str(item.get("detail", "")).strip(),
                    "profile": profile_name,
                    "target": target,
                    "alias": alias,
                    "priority": priority,
                    "assignee": assignee,
                    "role": role,
                }
            )
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
            created.append(todo)
            existing_by_key[key] = todo
            if dispatch_requested and todo.get("id") not in dispatch_candidate_ids:
                dispatch_candidates.append(todo)
                dispatch_candidate_ids.add(todo["id"])

        if dispatch_requested and not dispatch_items:
            dispatch_items = []
            for todo in open_todos:
                if str(todo.get("status", "")).strip().lower() != "todo":
                    continue
                title = str(todo.get("title", "")).strip()
                if not title:
                    continue
                dispatch_items.append(title)
                if todo.get("id") not in dispatch_candidate_ids:
                    dispatch_candidates.append(todo)
                    dispatch_candidate_ids.add(todo["id"])
            dispatch_items = list(dict.fromkeys(dispatch_items))

        dispatch_result: dict[str, Any] = {"queued": False, "target": target, "count": 0, "attempted_count": len(dispatch_candidates), "results": []}
        if dispatch_requested and dispatch_candidates:
            dispatches = [
                self.supervisor_route_todo(todo, actor="supervisor", auto_send=True).get("dispatch", {"dispatched": False, "todo": todo})
                for todo in dispatch_candidates
            ]
            dispatch_result = {
                "queued": any(bool(item.get("dispatched")) for item in dispatches),
                "target": target,
                "count": sum(1 for item in dispatches if bool(item.get("dispatched"))),
                "attempted_count": len(dispatch_candidates),
                "results": dispatches,
            }

        return {
            "ok": True,
            "created": created,
            "skipped": skipped,
            "dispatch": dispatch_result,
            "parsed_count": len(parsed_items),
            "dispatch_items": dispatch_items,
        }

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

    def capture_todo_output(self, todo: dict[str, Any], lines: int = 200) -> str:
        profile_name = str(todo.get("profile", "")).strip()
        target = str(todo.get("target", "")).strip()
        if not profile_name or not target:
            return ""
        try:
            return self.capture_pane_with_reports(profile_name=profile_name, target=target, lines=lines)
        except Exception:
            return ""
