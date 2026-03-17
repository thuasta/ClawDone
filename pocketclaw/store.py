"""Persistence for SSH profiles and pane aliases."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


def normalize_profile(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(payload.get("name", "")).strip(),
        "host": str(payload.get("host", "")).strip(),
        "username": str(payload.get("username", "")).strip(),
        "port": int(payload.get("port", 22) or 22),
        "password": str(payload.get("password", "")),
        "key_filename": str(payload.get("key_filename", "")).strip(),
        "tmux_bin": str(payload.get("tmux_bin", "tmux") or "tmux").strip(),
    }


class ProfileStore:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()

    def _empty(self) -> dict[str, Any]:
        return {"profiles": [], "aliases": {}}

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        content = self.path.read_text(encoding="utf-8").strip()
        if not content:
            return self._empty()
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"invalid profile store JSON: {self.path}") from exc
        if not isinstance(data, dict):
            raise RuntimeError("profile store content must be a JSON object")
        data.setdefault("profiles", [])
        data.setdefault("aliases", {})
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.path.parent) as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temp_name = handle.name
        Path(temp_name).replace(self.path)

    def list_profiles(self) -> list[dict[str, Any]]:
        raw_profiles = self._read().get("profiles", [])
        profiles: list[dict[str, Any]] = []
        for item in raw_profiles:
            if isinstance(item, dict):
                profiles.append(normalize_profile(item))
        return sorted(profiles, key=lambda profile: str(profile["name"]).lower())

    def get_profile(self, name: str) -> dict[str, Any]:
        if not name.strip():
            raise ValueError("profile name is required")
        for profile in self.list_profiles():
            if profile["name"] == name:
                return profile
        raise RuntimeError(f"profile not found: {name}")

    def save_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        normalized = normalize_profile(profile)
        if not normalized["name"]:
            raise ValueError("profile name is required")
        if not normalized["host"]:
            raise ValueError("profile host is required")
        if not normalized["username"]:
            raise ValueError("profile username is required")
        if normalized["port"] <= 0:
            raise ValueError("profile port must be positive")

        data = self._read()
        profiles = [
            item
            for item in data.get("profiles", [])
            if isinstance(item, dict) and item.get("name") != normalized["name"]
        ]
        profiles.append(normalized)
        data["profiles"] = sorted(profiles, key=lambda item: str(item.get("name", "")).lower())
        self._write(data)
        return normalized

    def delete_profile(self, name: str) -> None:
        data = self._read()
        profiles = [
            item
            for item in data.get("profiles", [])
            if isinstance(item, dict) and item.get("name") != name
        ]
        if len(profiles) == len(data.get("profiles", [])):
            raise RuntimeError(f"profile not found: {name}")
        data["profiles"] = profiles
        aliases = data.get("aliases", {})
        if isinstance(aliases, dict):
            aliases.pop(name, None)
        data["aliases"] = aliases
        self._write(data)

    def aliases_for(self, profile_name: str) -> dict[str, str]:
        aliases = self._read().get("aliases", {})
        if not isinstance(aliases, dict):
            return {}
        profile_aliases = aliases.get(profile_name, {})
        if not isinstance(profile_aliases, dict):
            return {}
        return {str(key): str(value) for key, value in profile_aliases.items()}

    def set_alias(self, profile_name: str, target: str, alias: str) -> None:
        if not profile_name.strip():
            raise ValueError("profile name is required")
        if not target.strip():
            raise ValueError("target is required")
        data = self._read()
        aliases = data.setdefault("aliases", {})
        if not isinstance(aliases, dict):
            aliases = {}
            data["aliases"] = aliases
        profile_aliases = aliases.setdefault(profile_name, {})
        if not isinstance(profile_aliases, dict):
            profile_aliases = {}
            aliases[profile_name] = profile_aliases
        cleaned_alias = alias.strip()
        if cleaned_alias:
            profile_aliases[target] = cleaned_alias
        else:
            profile_aliases.pop(target, None)
        self._write(data)
