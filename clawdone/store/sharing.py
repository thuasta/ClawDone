"""Share, workspace, and supervisor storage mixin."""

from __future__ import annotations

from .normalize import *  # noqa: F401,F403

class ProfileStoreSharingMixin:
    def _list_audit_logs_unlocked(self, profile_name: str = "", target: str = "", limit: int = 100) -> list[dict[str, Any]]:
        logs = self._read().get("audit_logs", [])
        result: list[dict[str, Any]] = []
        for item in logs:
            if not isinstance(item, dict):
                continue
            entry = normalize_audit_entry(item)
            if profile_name and entry["profile"] != profile_name:
                continue
            if target and entry["target"] != target:
                continue
            result.append(entry)
            if len(result) >= max(1, limit):
                break
        return result

    def _list_supervisor_configs_unlocked(self, profile_name: str = "") -> list[dict[str, Any]]:
        configs = self._read().get("supervisor_configs", [])
        result: list[dict[str, Any]] = []
        for item in configs:
            if not isinstance(item, dict):
                continue
            config = normalize_supervisor_config(item)
            if profile_name and config["profile"] not in {"", profile_name}:
                continue
            result.append(config)
        return sorted(result, key=lambda item: (item["profile"] != "", item["name"].lower()))

    def _list_session_shares_unlocked(self, profile_name: str = "", target: str = "", include_expired: bool = False) -> list[dict[str, Any]]:
        shares = self._read().get("session_shares", [])
        result: list[dict[str, Any]] = []
        for item in shares:
            if not isinstance(item, dict):
                continue
            share = normalize_share_link(item)
            if profile_name and share["profile"] != profile_name:
                continue
            if target and share["target"] != target:
                continue
            if not include_expired and not self._share_is_active(share):
                continue
            result.append(share)
        return result

    def list_workflow_todos(self, workflow_id: str) -> list[dict[str, Any]]:
        with self._lock:
            cleaned = str(workflow_id).strip()
            if not cleaned:
                raise ValueError("workflow_id is required")
            role_order = {"planner": 0, "executor": 1, "reviewer": 2, "general": 3}
            todos = [todo for todo in self._list_todos_unlocked() if str(todo.get("workflow_id", "")).strip() == cleaned]
            return sorted(
                todos,
                key=lambda item: (role_order.get(str(item.get("role", "general")), 9), str(item.get("created_at", ""))),
            )

    def _share_is_active(self, share: dict[str, Any]) -> bool:
        if str(share.get("revoked_at", "")).strip():
            return False
        expires_at = parse_utc(share.get("expires_at"))
        if expires_at is None:
            return True
        return expires_at > datetime.now(timezone.utc)

    def list_session_shares(self, profile_name: str = "", target: str = "", include_expired: bool = False) -> list[dict[str, Any]]:
        with self._lock:
            return self._list_session_shares_unlocked(profile_name=profile_name, target=target, include_expired=include_expired)

    def create_session_share(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            share = normalize_share_link(payload)
            if not share["profile"]:
                raise ValueError("share profile is required")
            if not share["target"]:
                raise ValueError("share target is required")
            if not share["expires_at"]:
                expires_in_minutes = optional_non_negative_int(payload.get("expires_in_minutes", 60), "expires_in_minutes")
                if expires_in_minutes <= 0:
                    expires_in_minutes = 60
                share["expires_at"] = (
                    datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
                ).isoformat(timespec="seconds").replace("+00:00", "Z")
            now = utc_now()
            share["updated_at"] = now
            data = self._read()
            existing = None
            for item in data.get("session_shares", []):
                if isinstance(item, dict) and str(item.get("id", "")).strip() == share["id"]:
                    existing = normalize_share_link(item)
                    break
            share["created_at"] = existing.get("created_at", now) if existing else now
            shares = [
                item
                for item in data.get("session_shares", [])
                if not isinstance(item, dict) or str(item.get("id", "")).strip() != share["id"]
            ]
            shares.append(share)
            data["session_shares"] = shares
            self._write(data)
            return share

    def revoke_session_share(self, share_id: str = "", token: str = "") -> dict[str, Any]:
        with self._lock:
            cleaned_id = str(share_id).strip()
            cleaned_token = str(token).strip()
            if not cleaned_id and not cleaned_token:
                raise ValueError("share id or token is required")
            data = self._read()
            shares = data.get("session_shares", [])
            updated: dict[str, Any] | None = None
            next_shares: list[dict[str, Any]] = []
            for item in shares:
                if not isinstance(item, dict):
                    continue
                share = normalize_share_link(item)
                if (cleaned_id and share["id"] == cleaned_id) or (cleaned_token and share["token"] == cleaned_token):
                    share["revoked_at"] = utc_now()
                    share["updated_at"] = share["revoked_at"]
                    updated = share
                next_shares.append(share)
            if not updated:
                raise RuntimeError("share link not found")
            data["session_shares"] = next_shares
            self._write(data)
            return updated

    def resolve_session_share(self, token: str) -> dict[str, Any]:
        with self._lock:
            cleaned = str(token).strip()
            if not cleaned:
                raise ValueError("share token is required")
            for share in self._list_session_shares_unlocked(include_expired=True):
                if share["token"] != cleaned:
                    continue
                if not self._share_is_active(share):
                    raise RuntimeError("share link expired or revoked")
                return share
            raise RuntimeError("share link not found")

    def list_workspace_templates(self, profile_name: str = "", target: str = "") -> list[dict[str, Any]]:
        with self._lock:
            templates = self._read().get("workspace_templates", [])
            result: list[dict[str, Any]] = []
            for item in templates:
                if not isinstance(item, dict):
                    continue
                template = normalize_workspace_template(item)
                if profile_name and template["profile"] not in {"", profile_name}:
                    continue
                if target and template["target"] not in {"", target}:
                    continue
                result.append(template)
            return sorted(result, key=lambda item: (item["profile"] != "", item["target"] != "", item["name"].lower()))

    def save_workspace_template(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            template = normalize_workspace_template(payload)
            if not template["name"]:
                raise ValueError("workspace template name is required")
            data = self._read()
            now = utc_now()
            existing = None
            for item in data.get("workspace_templates", []):
                if isinstance(item, dict) and str(item.get("id", "")).strip() == template["id"]:
                    existing = normalize_workspace_template(item)
                    break
            template["created_at"] = existing.get("created_at", now) if existing else now
            template["updated_at"] = now
            templates = [
                item
                for item in data.get("workspace_templates", [])
                if not isinstance(item, dict) or str(item.get("id", "")).strip() != template["id"]
            ]
            templates.append(template)
            data["workspace_templates"] = templates
            self._write(data)
            return template

    def delete_workspace_template(self, template_id: str) -> None:
        with self._lock:
            cleaned = str(template_id).strip()
            if not cleaned:
                raise ValueError("workspace template id is required")
            data = self._read()
            templates = [
                item
                for item in data.get("workspace_templates", [])
                if not isinstance(item, dict) or str(item.get("id", "")).strip() != cleaned
            ]
            if len(templates) == len(data.get("workspace_templates", [])):
                raise RuntimeError(f"workspace template not found: {cleaned}")
            data["workspace_templates"] = templates
            self._write(data)

    def list_supervisor_configs(self, profile_name: str = "") -> list[dict[str, Any]]:
        with self._lock:
            return self._list_supervisor_configs_unlocked(profile_name=profile_name)

    def get_supervisor_config(self, config_id: str = "", profile_name: str = "") -> dict[str, Any]:
        with self._lock:
            cleaned_id = str(config_id).strip()
            configs = self._list_supervisor_configs_unlocked(profile_name=profile_name)
            if cleaned_id:
                for config in configs:
                    if config["id"] == cleaned_id:
                        return config
                raise RuntimeError(f"supervisor config not found: {cleaned_id}")
            if configs:
                return configs[0]
            raise RuntimeError("supervisor config not found")

    def save_supervisor_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            config = normalize_supervisor_config(payload)
            if not config["name"]:
                raise ValueError("supervisor config name is required")
            data = self._read()
            now = utc_now()
            existing = None
            for item in data.get("supervisor_configs", []):
                if isinstance(item, dict) and str(item.get("id", "")).strip() == config["id"]:
                    existing = normalize_supervisor_config(item)
                    break
            if existing and not config["api_key"] and not config["api_key_ref"]:
                config["api_key"] = str(existing.get("api_key", ""))
                config["api_key_ref"] = str(existing.get("api_key_ref", "")).strip()
            config["created_at"] = existing.get("created_at", now) if existing else now
            config["updated_at"] = now
            configs = [
                item
                for item in data.get("supervisor_configs", [])
                if not isinstance(item, dict) or str(item.get("id", "")).strip() != config["id"]
            ]
            configs.append(config)
            data["supervisor_configs"] = configs
            self._write(data)
            return config

    def delete_supervisor_config(self, config_id: str) -> None:
        with self._lock:
            cleaned = str(config_id).strip()
            if not cleaned:
                raise ValueError("supervisor config id is required")
            data = self._read()
            configs = [
                item
                for item in data.get("supervisor_configs", [])
                if not isinstance(item, dict) or str(item.get("id", "")).strip() != cleaned
            ]
            if len(configs) == len(data.get("supervisor_configs", [])):
                raise RuntimeError(f"supervisor config not found: {cleaned}")
            data["supervisor_configs"] = configs
            self._write(data)
