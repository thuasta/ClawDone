"""Composed web app implementation."""

from __future__ import annotations

from .support import *  # noqa: F401,F403
from .support import _is_client_disconnect
from .base import ClawDoneBaseMixin
from .supervisor import ClawDoneSupervisorMixin
from .todos import ClawDoneTodoMixin
from .http import ClawDoneHttpMixin

class ClawDoneApp(ClawDoneHttpMixin, ClawDoneTodoMixin, ClawDoneSupervisorMixin, ClawDoneBaseMixin):
    pass

class ClawDoneServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler_cls: type[BaseHTTPRequestHandler], app: ClawDoneApp):
        self.app = app
        super().__init__(server_address, handler_cls)

    def shutdown(self) -> None:
        if hasattr(self, "app"):
            self.app.stop_background_tasks()
        super().shutdown()

    def server_close(self) -> None:
        if hasattr(self, "app"):
            self.app.stop_background_tasks()
        super().server_close()


def build_handler(app: ClawDoneApp) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            try:
                app.handle_get(self)
            except (ValueError, RuntimeError) as exc:
                try:
                    app.json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                except OSError as write_exc:
                    if not _is_client_disconnect(write_exc):
                        raise
            except Exception as exc:  # pragma: no cover
                if _is_client_disconnect(exc):
                    return
                try:
                    app.json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
                except OSError as write_exc:
                    if not _is_client_disconnect(write_exc):
                        raise

        def do_POST(self) -> None:
            try:
                app.handle_post(self)
            except (ValueError, RuntimeError) as exc:
                try:
                    app.json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                except OSError as write_exc:
                    if not _is_client_disconnect(write_exc):
                        raise
            except Exception as exc:  # pragma: no cover
                if _is_client_disconnect(exc):
                    return
                try:
                    app.json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
                except OSError as write_exc:
                    if not _is_client_disconnect(write_exc):
                        raise

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def create_server(
    config: dict[str, Any],
    tmux_client: TmuxClient | None = None,
    store: ProfileStore | None = None,
    remote_tmux: RemoteTmuxClient | None = None,
) -> ThreadingHTTPServer:
    app = ClawDoneApp(config=config, tmux_client=tmux_client, store=store, remote_tmux=remote_tmux)
    server = ClawDoneServer((app.config["host"], app.config["port"]), build_handler(app), app)
    app.start_background_tasks()
    return server
