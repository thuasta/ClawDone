from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path

from pocketclaw.app import (
    ProfileStore,
    RemoteTmuxClient,
    TmuxClient,
    build_parser,
    command_result,
    extract_token,
    is_authorized,
)


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
            self.headers["X-PocketClaw-Token"] = header_token
        self.rfile = io.BytesIO()


class FakeSSHExecutor:
    def __init__(self, responses: dict[str, dict] | None = None):
        self.responses = responses or {}
        self.commands: list[str] = []

    def run(self, profile: dict, command: str) -> dict:
        _ = profile
        self.commands.append(command)
        return self.responses.get(command, command_result(0, ""))


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


class ProfileStoreTests(unittest.TestCase):
    def test_save_list_and_alias_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            profile = {"name": "office", "host": "10.0.0.1", "username": "ubuntu", "password": "secret"}
            store.save_profile(profile)
            store.set_alias("office", "codex:1.0", "backend-agent")

            saved = store.get_profile("office")
            self.assertEqual(saved["host"], "10.0.0.1")
            self.assertEqual(store.aliases_for("office"), {"codex:1.0": "backend-agent"})

    def test_delete_profile_removes_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProfileStore(Path(temp_dir) / "profiles.json")
            store.save_profile({"name": "office", "host": "10.0.0.1", "username": "ubuntu"})
            store.set_alias("office", "codex:1.0", "backend-agent")
            store.delete_profile("office")

            self.assertEqual(store.list_profiles(), [])
            self.assertEqual(store.aliases_for("office"), {})


class RemoteTmuxClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = {"name": "office", "host": "10.0.0.1", "username": "ubuntu", "port": 22, "tmux_bin": "tmux"}

    def test_snapshot_builds_nested_sessions_windows_and_panes(self) -> None:
        executor = FakeSSHExecutor(
            responses={
                "tmux list-sessions -F '#{session_name}\t#{session_windows}\t#{session_attached}'": command_result(0, "codex\t2\t1\n"),
                "tmux list-windows -a -F '#{session_name}\t#{window_index}\t#{window_name}\t#{window_active}'": command_result(0, "codex\t0\tmain\t1\ncodex\t1\tlogs\t0\n"),
                "tmux list-panes -a -F '#{session_name}\t#{window_index}\t#{window_name}\t#{pane_index}\t#{pane_title}\t#{pane_current_command}\t#{pane_active}'": command_result(0, "codex\t0\tmain\t0\t\tcodex\t1\ncodex\t1\tlogs\t0\t\tbash\t1\n"),
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
                "tmux send-keys -t codex:0.0 -l 'run tests && summarize'": command_result(0),
                "tmux send-keys -t codex:0.0 Enter": command_result(0),
            }
        )
        client = RemoteTmuxClient(executor=executor)
        client.send_keys(self.profile, "codex:0.0", "run tests && summarize")
        self.assertEqual(
            executor.commands,
            [
                "tmux send-keys -t codex:0.0 -l 'run tests && summarize'",
                "tmux send-keys -t codex:0.0 Enter",
            ],
        )


class AuthTests(unittest.TestCase):
    def test_extract_token_from_bearer_header(self) -> None:
        handler = DummyHandler(auth="Bearer secret")
        self.assertEqual(extract_token(handler), "secret")

    def test_extract_token_from_query_string(self) -> None:
        handler = DummyHandler(path="/api/sessions?token=query-secret")
        self.assertEqual(extract_token(handler), "query-secret")

    def test_authorized_when_tokens_match(self) -> None:
        handler = DummyHandler(auth="Bearer secret")
        self.assertTrue(is_authorized(handler, {"token": "secret"}))

    def test_unauthorized_when_tokens_do_not_match(self) -> None:
        handler = DummyHandler(header_token="wrong")
        self.assertFalse(is_authorized(handler, {"token": "secret"}))


class ParserTests(unittest.TestCase):
    def test_send_parser_keeps_subcommand_and_command_text(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["send", "--session", "codex", "--command", "hello world"])
        self.assertEqual(args.subcommand, "send")
        self.assertEqual(args.command_text, "hello world")


if __name__ == "__main__":
    unittest.main()
