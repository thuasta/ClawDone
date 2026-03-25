"""Profile and template storage mixin."""

from __future__ import annotations

from .normalize import *  # noqa: F401,F403

class ProfileStoreCoreMixin:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self._lock = threading.Lock()
        self._cache: dict | None = None
        self._cache_mtime: float = 0.0

    def _empty(self) -> dict[str, Any]:
        return {
            "profiles": [],
            "aliases": {},
            "templates": [],
            "history": [],
            "todos": [],
            "todo_templates": [],
            "audit_logs": [],
            "session_shares": [],
            "workspace_templates": [],
            "supervisor_configs": [],
            "ui_state": normalize_ui_state({}),
        }

    def _read(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._empty()
        current_mtime = self.path.stat().st_mtime_ns
        if self._cache is not None and current_mtime == self._cache_mtime:
            return copy.deepcopy(self._cache)
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
        data.setdefault("templates", [])
        data.setdefault("history", [])
        data.setdefault("todos", [])
        data.setdefault("todo_templates", [])
        data.setdefault("audit_logs", [])
        data.setdefault("session_shares", [])
        data.setdefault("workspace_templates", [])
        data.setdefault("supervisor_configs", [])
        self._cache = copy.deepcopy(data)
        self._cache_mtime = current_mtime
        data.setdefault("ui_state", normalize_ui_state({}))
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=self.path.parent) as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temp_name = handle.name
        Path(temp_name).replace(self.path)
        self._cache = copy.deepcopy(data)
        self._cache_mtime = self.path.stat().st_mtime_ns

    def _list_profiles_unlocked(self) -> list[dict[str, Any]]:
        raw_profiles = self._read().get("profiles", [])
        profiles: list[dict[str, Any]] = []
        for item in raw_profiles:
            if isinstance(item, dict):
                profiles.append(normalize_profile(item))
        return sorted(
            profiles,
            key=lambda profile: (
                not bool(profile.get("favorite")),
                str(profile.get("group", "")).lower(),
                str(profile["name"]).lower(),
            ),
        )

    def _get_profile_unlocked(self, name: str) -> dict[str, Any]:
        if not name.strip():
            raise ValueError("profile name is required")
        for profile in self._list_profiles_unlocked():
            if profile["name"] == name:
                return profile
        raise RuntimeError(f"profile not found: {name}")

    def _save_profile_unlocked(self, profile: dict[str, Any]) -> dict[str, Any]:
        normalized = normalize_profile(profile)
        existing: dict[str, Any] | None = None
        try:
            existing = self._get_profile_unlocked(normalized["name"])
        except RuntimeError:
            existing = None

        if existing and not normalized["password"] and not normalized["password_ref"]:
            normalized["password"] = str(existing.get("password", ""))
            normalized["password_ref"] = str(existing.get("password_ref", "")).strip()
        if normalized["password"] and normalized["password_ref"]:
            raise ValueError("profile password and password_ref cannot both be set")
        if not normalized["name"]:
            raise ValueError("profile name is required")
        if not normalized["host"]:
            raise ValueError("profile host is required")
        if not normalized["username"]:
            raise ValueError("profile username is required")
        if normalized["port"] <= 0:
            raise ValueError("profile port must be positive")
        if normalized["host_key_policy"] not in PROFILE_HOST_KEY_POLICIES:
            allowed = ", ".join(sorted(policy for policy in PROFILE_HOST_KEY_POLICIES if policy))
            raise ValueError(f"profile host_key_policy must be empty or one of: {allowed}")

        now = utc_now()
        normalized["created_at"] = existing.get("created_at", now) if existing else now
        normalized["updated_at"] = now

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

    def _delete_profile_unlocked(self, name: str) -> None:
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
        templates = data.get("templates", [])
        data["templates"] = [
            item for item in templates if not isinstance(item, dict) or str(item.get("profile", "")).strip() != name
        ]
        history = data.get("history", [])
        data["history"] = [
            item for item in history if not isinstance(item, dict) or str(item.get("profile", "")).strip() != name
        ]
        todos = data.get("todos", [])
        data["todos"] = [
            item for item in todos if not isinstance(item, dict) or str(item.get("profile", "")).strip() != name
        ]
        todo_templates = data.get("todo_templates", [])
        data["todo_templates"] = [
            item for item in todo_templates if not isinstance(item, dict) or str(item.get("profile", "")).strip() != name
        ]
        audit_logs = data.get("audit_logs", [])
        data["audit_logs"] = [
            item for item in audit_logs if not isinstance(item, dict) or str(item.get("profile", "")).strip() != name
        ]
        session_shares = data.get("session_shares", [])
        data["session_shares"] = [
            item for item in session_shares if not isinstance(item, dict) or str(item.get("profile", "")).strip() != name
        ]
        workspace_templates = data.get("workspace_templates", [])
        data["workspace_templates"] = [
            item
            for item in workspace_templates
            if not isinstance(item, dict) or str(item.get("profile", "")).strip() != name
        ]
        supervisor_configs = data.get("supervisor_configs", [])
        data["supervisor_configs"] = [
            item
            for item in supervisor_configs
            if not isinstance(item, dict) or str(item.get("profile", "")).strip() not in {name}
        ]
        self._write(data)

    def _aliases_for_unlocked(self, profile_name: str) -> dict[str, str]:
        aliases = self._read().get("aliases", {})
        if not isinstance(aliases, dict):
            return {}
        profile_aliases = aliases.get(profile_name, {})
        if not isinstance(profile_aliases, dict):
            return {}
        return {str(key): str(value) for key, value in profile_aliases.items()}

    def all_aliases(self) -> dict[str, dict[str, str]]:
        """Return all aliases grouped by profile name in a single read."""
        aliases = self._read().get("aliases", {})
        if not isinstance(aliases, dict):
            return {}
        result: dict[str, dict[str, str]] = {}
        for profile_name, profile_aliases in aliases.items():
            if not isinstance(profile_aliases, dict):
                continue
            result[str(profile_name)] = {str(key): str(value) for key, value in profile_aliases.items()}
        return result

    def _set_alias_unlocked(self, profile_name: str, target: str, alias: str) -> None:
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

    def get_ui_state(self) -> dict[str, Any]:
        data = self._read()
        return normalize_ui_state(data.get("ui_state", {}))

    def save_ui_state(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("ui_state payload must be an object")
        data = self._read()
        current = normalize_ui_state(data.get("ui_state", {}))

        if "ui_settings" in payload:
            current["ui_settings"] = normalize_ui_settings(payload.get("ui_settings", {}))
        if "current_view" in payload:
            requested_view = str(payload.get("current_view", "")).strip().lower()
            if requested_view in UI_VIEWS:
                current["current_view"] = requested_view
        if "selected_profile" in payload:
            current["selected_profile"] = str(payload.get("selected_profile", "")).strip()
        if "fold_states" in payload:
            current["fold_states"] = normalize_fold_states(payload.get("fold_states", {}))

        current["updated_at"] = utc_now()
        data["ui_state"] = current
        self._write(data)
        return current

    def _list_templates_unlocked(self, profile_name: str = "") -> list[dict[str, Any]]:
        templates = self._read().get("templates", [])
        result: list[dict[str, Any]] = []
        for item in templates:
            if not isinstance(item, dict):
                continue
            template = normalize_template(item)
            if profile_name and template["profile"] not in {"", profile_name}:
                continue
            result.append(template)
        return sorted(result, key=lambda item: (item["profile"] != "", item["name"].lower()))

    def _save_template_unlocked(self, payload: dict[str, Any]) -> dict[str, Any]:
        template = normalize_template(payload)
        if not template["name"]:
            raise ValueError("template name is required")
        if not template["command"]:
            raise ValueError("template command is required")
        data = self._read()
        now = utc_now()
        existing: dict[str, Any] | None = None
        for item in data.get("templates", []):
            if isinstance(item, dict) and str(item.get("id", "")) == template["id"]:
                existing = normalize_template(item)
                break
        template["created_at"] = existing.get("created_at", now) if existing else now
        template["updated_at"] = now
        templates = [
            item for item in data.get("templates", []) if not isinstance(item, dict) or str(item.get("id", "")) != template["id"]
        ]
        templates.append(template)
        data["templates"] = templates
        self._write(data)
        return template

    def _delete_template_unlocked(self, template_id: str) -> None:
        if not template_id.strip():
            raise ValueError("template id is required")
        data = self._read()
        templates = [
            item for item in data.get("templates", []) if not isinstance(item, dict) or str(item.get("id", "")) != template_id
        ]
        if len(templates) == len(data.get("templates", [])):
            raise RuntimeError(f"template not found: {template_id}")
        data["templates"] = templates
        self._write(data)

    def _record_history_unlocked(self, payload: dict[str, Any], limit: int = 200) -> dict[str, Any]:
        entry = {
            "id": uuid4().hex,
            "profile": str(payload.get("profile", "")).strip(),
            "target": str(payload.get("target", "")).strip(),
            "alias": str(payload.get("alias", "")).strip(),
            "command": str(payload.get("command", "")).strip(),
            "created_at": utc_now(),
        }
        if not entry["profile"]:
            raise ValueError("history profile is required")
        if not entry["target"]:
            raise ValueError("history target is required")
        if not entry["command"]:
            raise ValueError("history command is required")
        data = self._read()
        history = [entry]
        for item in data.get("history", []):
            if isinstance(item, dict):
                history.append(item)
        data["history"] = history[: max(1, limit)]
        self._write(data)
        return entry

    def _list_history_unlocked(self, profile_name: str = "", limit: int = 20) -> list[dict[str, Any]]:
        history = self._read().get("history", [])
        result: list[dict[str, Any]] = []
        for item in history:
            if not isinstance(item, dict):
                continue
            if profile_name and str(item.get("profile", "")).strip() != profile_name:
                continue
            result.append({
                "id": str(item.get("id", "")).strip(),
                "profile": str(item.get("profile", "")).strip(),
                "target": str(item.get("target", "")).strip(),
                "alias": str(item.get("alias", "")).strip(),
                "command": str(item.get("command", "")).strip(),
                "created_at": str(item.get("created_at", "")).strip(),
            })
            if len(result) >= max(1, limit):
                break
        return result

    def _clear_history_unlocked(self, profile_name: str = "") -> None:
        data = self._read()
        if not profile_name:
            data["history"] = []
        else:
            data["history"] = [
                item
                for item in data.get("history", [])
                if not isinstance(item, dict) or str(item.get("profile", "")).strip() != profile_name
            ]
        self._write(data)

    def list_profiles(self) -> list[dict[str, Any]]:
        with self._lock:
            return self._list_profiles_unlocked()

    def get_profile(self, name: str) -> dict[str, Any]:
        with self._lock:
            return self._get_profile_unlocked(name)

    def save_profile(self, profile: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            return self._save_profile_unlocked(profile)

    def delete_profile(self, name: str) -> None:
        with self._lock:
            self._delete_profile_unlocked(name)

    def aliases_for(self, profile_name: str) -> dict[str, str]:
        with self._lock:
            return self._aliases_for_unlocked(profile_name)

    def set_alias(self, profile_name: str, target: str, alias: str) -> None:
        with self._lock:
            self._set_alias_unlocked(profile_name, target, alias)

    def list_templates(self, profile_name: str = "") -> list[dict[str, Any]]:
        with self._lock:
            return self._list_templates_unlocked(profile_name)

    def save_template(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            return self._save_template_unlocked(payload)

    def delete_template(self, template_id: str) -> None:
        with self._lock:
            self._delete_template_unlocked(template_id)

    def record_history(self, payload: dict[str, Any], limit: int = 200) -> dict[str, Any]:
        with self._lock:
            return self._record_history_unlocked(payload, limit=limit)

    def list_history(self, profile_name: str = "", limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            return self._list_history_unlocked(profile_name, limit=limit)

    def clear_history(self, profile_name: str = "") -> None:
        with self._lock:
            self._clear_history_unlocked(profile_name)
