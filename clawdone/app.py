"""Backward-compatible facade for ClawDone public APIs."""

from .cli import build_parser, main
from .local_tmux import Runner, TmuxClient
from .remote import PARAMIKO_AVAILABLE, RemoteTmuxClient, SSHExecutor, command_result, paramiko
from .store import ProfileStore, mask_profile, mask_supervisor_config, normalize_profile, normalize_tags, normalize_template, utc_now
from .supervisor import SupervisorClient, normalize_supervisor_config
from .web import ClawDoneApp, build_handler, create_server, extract_token, normalize_config

__all__ = [
    "PARAMIKO_AVAILABLE",
    "ClawDoneApp",
    "ProfileStore",
    "SupervisorClient",
    "RemoteTmuxClient",
    "Runner",
    "SSHExecutor",
    "TmuxClient",
    "build_handler",
    "build_parser",
    "command_result",
    "create_server",
    "extract_token",
    "main",
    "mask_profile",
    "mask_supervisor_config",
    "normalize_config",
    "normalize_profile",
    "normalize_supervisor_config",
    "normalize_tags",
    "normalize_template",
    "paramiko",
    "utc_now",
]
