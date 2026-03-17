"""HTTP app and request handlers."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from .html import INDEX_HTML
from .local_tmux import TmuxClient
from .remote import PARAMIKO_AVAILABLE, RemoteTmuxClient
from .store import ProfileStore, normalize_profile


def normalize_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "host": str(config.get("host", "127.0.0.1")),
        "port": int(config.get("port", 8787)),
        "token": config.get("token") or None,
        "tmux_bin": str(config.get("tmux_bin", "tmux")),
        "store_path": str(config.get("store_path", "~/.pocketclaw/profiles.json")),
    }


def extract_token(handler: BaseHTTPRequestHandler) -> str | None:
    auth = handler.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    query = parse_qs(urlparse(handler.path).query)
    query_token = query.get("token", [None])[0]
    if query_token:
        return query_token
    header_token = handler.headers.get("X-PocketClaw-Token")
    if header_token:
        return header_token.strip()
    return None


def is_authorized(handler: BaseHTTPRequestHandler, config: dict[str, Any]) -> bool:
    token = config.get("token")
    if not token:
        return True
    return extract_token(handler) == token


class PocketClawApp:
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
        self.remote_tmux = remote_tmux or RemoteTmuxClient()

    def json_response(self, handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(data)))
        handler.end_headers()
        handler.wfile.write(data)

    def html_response(self, handler: BaseHTTPRequestHandler, html: str) -> None:
        data = html.encode("utf-8")
        handler.send_response(HTTPStatus.OK)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.send_header("Content-Length", str(len(data)))
        handler.end_headers()
        handler.wfile.write(data)

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

    def require_auth(self, handler: BaseHTTPRequestHandler) -> bool:
        if is_authorized(handler, self.config):
            return True
        self.json_response(handler, HTTPStatus.UNAUTHORIZED, {"error": "invalid or missing token"})
        return False

    def profile_from_body(self, body: dict[str, Any]) -> dict[str, Any]:
        return normalize_profile(body)

    def get_profile(self, name: str) -> dict[str, Any]:
        return self.store.get_profile(name)

    def list_profiles_payload(self) -> list[dict[str, Any]]:
        return self.store.list_profiles()

    def handle_get(self, handler: BaseHTTPRequestHandler) -> None:
        parsed = urlparse(handler.path)
        if parsed.path == "/":
            self.html_response(handler, INDEX_HTML)
            return
        if not self.require_auth(handler):
            return

        query = parse_qs(parsed.query)

        if parsed.path == "/api/health":
            self.json_response(handler, HTTPStatus.OK, {
                "ok": True,
                "ssh_backend_available": PARAMIKO_AVAILABLE,
                "profile_count": len(self.store.list_profiles()),
            })
            return

        if parsed.path == "/api/profiles":
            self.json_response(handler, HTTPStatus.OK, {"profiles": self.list_profiles_payload()})
            return

        if parsed.path == "/api/remote/state":
            profile_name = str(query.get("profile", [""])[0]).strip()
            profile = self.get_profile(profile_name)
            payload = self.remote_tmux.snapshot(profile, aliases=self.store.aliases_for(profile_name))
            self.json_response(handler, HTTPStatus.OK, payload)
            return

        if parsed.path == "/api/pane":
            profile_name = str(query.get("profile", [""])[0]).strip()
            target = str(query.get("target", [""])[0]).strip()
            lines_text = str(query.get("lines", ["120"])[0]).strip() or "120"
            try:
                lines = int(lines_text)
            except ValueError as exc:
                raise ValueError("lines must be an integer") from exc
            profile = self.get_profile(profile_name)
            output = self.remote_tmux.capture_pane(profile, target=target, lines=lines)
            self.json_response(handler, HTTPStatus.OK, {"profile": profile_name, "target": target, "output": output})
            return

        self.json_response(handler, HTTPStatus.NOT_FOUND, {"error": "not found"})

    def handle_post(self, handler: BaseHTTPRequestHandler) -> None:
        parsed = urlparse(handler.path)
        if not self.require_auth(handler):
            return
        body = self.read_json(handler)

        if parsed.path == "/api/profiles/save":
            profile = self.profile_from_body(body)
            self.store.save_profile(profile)
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "profile": profile})
            return

        if parsed.path == "/api/profiles/delete":
            name = str(body.get("name", "")).strip()
            self.store.delete_profile(name)
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "name": name})
            return

        if parsed.path == "/api/profiles/test":
            profile = self.profile_from_body(body)
            self.json_response(handler, HTTPStatus.OK, self.remote_tmux.test_connection(profile))
            return

        if parsed.path == "/api/alias/save":
            profile_name = str(body.get("profile", "")).strip()
            target = str(body.get("target", "")).strip()
            alias = str(body.get("alias", ""))
            self.store.set_alias(profile_name, target, alias)
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "profile": profile_name, "target": target, "alias": alias.strip()})
            return

        if parsed.path == "/api/send":
            profile_name = str(body.get("profile", "")).strip()
            target = str(body.get("target", "")).strip()
            command = str(body.get("command", ""))
            press_enter = bool(body.get("press_enter", True))
            profile = self.get_profile(profile_name)
            self.remote_tmux.send_keys(profile, target=target, command=command, press_enter=press_enter)
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "profile": profile_name, "target": target})
            return

        if parsed.path == "/api/interrupt":
            profile_name = str(body.get("profile", "")).strip()
            target = str(body.get("target", "")).strip()
            profile = self.get_profile(profile_name)
            self.remote_tmux.interrupt(profile, target=target)
            self.json_response(handler, HTTPStatus.OK, {"ok": True, "profile": profile_name, "target": target})
            return

        self.json_response(handler, HTTPStatus.NOT_FOUND, {"error": "not found"})


def build_handler(app: PocketClawApp) -> type[BaseHTTPRequestHandler]:
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


def create_server(
    config: dict[str, Any],
    tmux_client: TmuxClient | None = None,
    store: ProfileStore | None = None,
    remote_tmux: RemoteTmuxClient | None = None,
) -> ThreadingHTTPServer:
    app = PocketClawApp(config=config, tmux_client=tmux_client, store=store, remote_tmux=remote_tmux)
    return ThreadingHTTPServer((app.config["host"], app.config["port"]), build_handler(app))
