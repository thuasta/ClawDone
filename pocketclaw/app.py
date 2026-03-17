"""Backward-compatible facade for PocketClaw public APIs."""

from .cli import build_parser, main
from .local_tmux import Runner, TmuxClient
from .remote import PARAMIKO_AVAILABLE, RemoteTmuxClient, SSHExecutor, command_result, paramiko
from .store import ProfileStore, normalize_profile
from .web import PocketClawApp, build_handler, create_server, extract_token, is_authorized, normalize_config

__all__ = [
    "PARAMIKO_AVAILABLE",
    "PocketClawApp",
    "ProfileStore",
    "RemoteTmuxClient",
    "Runner",
    "SSHExecutor",
    "TmuxClient",
    "build_handler",
    "build_parser",
    "command_result",
    "create_server",
    "extract_token",
    "is_authorized",
    "main",
    "normalize_config",
    "normalize_profile",
    "paramiko",
]
