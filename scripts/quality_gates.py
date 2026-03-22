#!/usr/bin/env python3
"""Minimal quality gates for ClawDone workflow safety checks."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "clawdone" / "web.py"
STORE = ROOT / "clawdone" / "store.py"


def require_contains(path: Path, needle: str) -> None:
    text = path.read_text(encoding="utf-8")
    if needle not in text:
        raise SystemExit(f"[quality-gates] missing required marker in {path.name}: {needle}")


def main() -> int:
    require_contains(WEB, "invalid or missing token")
    require_contains(WEB, "dangerous command requires confirm_risk=true")
    require_contains(WEB, "insufficient role, requires")
    require_contains(STORE, "cannot set done/verified without evidence")
    require_contains(STORE, "handoff packet is incomplete")
    print("[quality-gates] all static checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
