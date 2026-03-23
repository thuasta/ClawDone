"""Decoupled supervisor agent module for routing, review, and acceptance."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from .utils import extract_json_object

SUPERVISOR_PROVIDERS = {"openai_compatible"}
SUPERVISOR_PERMISSIONS = {"dispatch", "review", "accept"}
DEFAULT_SUPERVISOR_BASE_URL = "https://api.openai.com/v1"
DEFAULT_SUPERVISOR_MODEL = "gpt-4.1-mini"
DEFAULT_SUPERVISOR_PROMPT = (
    "You are the project supervisor for a multi-agent engineering system. "
    "Route tasks to the best agent, review delivery evidence, and decide whether work is ready for acceptance. "
    "Always respond with valid JSON only."
)


def normalize_supervisor_permissions(value: Any) -> list[str]:
    if isinstance(value, str):
        raw = [item.strip().lower() for item in value.split(",")]
    elif isinstance(value, list):
        raw = [str(item).strip().lower() for item in value]
    else:
        raw = []
    permissions: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if not item or item in seen:
            continue
        if item not in SUPERVISOR_PERMISSIONS:
            allowed = ", ".join(sorted(SUPERVISOR_PERMISSIONS))
            raise ValueError(f"supervisor permission must be one of: {allowed}")
        permissions.append(item)
        seen.add(item)
    return permissions



def normalize_supervisor_config(payload: dict[str, Any]) -> dict[str, Any]:
    provider = str(payload.get("provider", "openai_compatible") or "openai_compatible").strip().lower()
    if provider not in SUPERVISOR_PROVIDERS:
        allowed = ", ".join(sorted(SUPERVISOR_PROVIDERS))
        raise ValueError(f"supervisor provider must be one of: {allowed}")
    permissions = normalize_supervisor_permissions(payload.get("permissions", ["dispatch", "review", "accept"]))
    if not permissions:
        permissions = ["dispatch", "review", "accept"]
    return {
        "id": str(payload.get("id", "")).strip() or uuid4().hex,
        "name": str(payload.get("name", "Supervisor")).strip() or "Supervisor",
        "profile": str(payload.get("profile", "")).strip(),
        "provider": provider,
        "base_url": str(payload.get("base_url", DEFAULT_SUPERVISOR_BASE_URL)).strip() or DEFAULT_SUPERVISOR_BASE_URL,
        "model": str(payload.get("model", DEFAULT_SUPERVISOR_MODEL)).strip() or DEFAULT_SUPERVISOR_MODEL,
        "api_key": str(payload.get("api_key", "")),
        "api_key_ref": str(payload.get("api_key_ref", "")).strip(),
        "enabled": bool(payload.get("enabled", True)),
        "permissions": permissions,
        "auto_dispatch": bool(payload.get("auto_dispatch", True)),
        "auto_review": bool(payload.get("auto_review", True)),
        "auto_accept": bool(payload.get("auto_accept", True)),
        "system_prompt": str(payload.get("system_prompt", DEFAULT_SUPERVISOR_PROMPT)).strip() or DEFAULT_SUPERVISOR_PROMPT,
        "created_at": str(payload.get("created_at", "")).strip(),
        "updated_at": str(payload.get("updated_at", "")).strip(),
    }



def mask_supervisor_config(config: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_supervisor_config(config)
    return {
        **normalized,
        "api_key": "",
        "has_api_key": bool(normalized.get("api_key")) or bool(normalized.get("api_key_ref")),
    }


class SupervisorTransport:
    def post_json(self, url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        raise NotImplementedError


class OpenAICompatibleTransport(SupervisorTransport):
    def post_json(self, url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", **headers},
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                data = response.read().decode("utf-8")
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"supervisor API HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise RuntimeError(f"supervisor API connection failed: {exc}") from exc
        try:
            decoded = json.loads(data)
        except json.JSONDecodeError as exc:
            raise RuntimeError("supervisor API returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise RuntimeError("supervisor API returned non-object JSON")
        return decoded


class SupervisorClient:
    def __init__(self, transport: SupervisorTransport | None = None, timeout: float = 25.0):
        self.transport = transport or OpenAICompatibleTransport()
        self.timeout = max(1.0, float(timeout))

    def resolve_api_key(self, config: dict[str, Any]) -> str:
        direct = str(config.get("api_key", ""))
        if direct:
            return direct
        ref = str(config.get("api_key_ref", "")).strip()
        if not ref:
            return ""
        if ref.startswith("env:"):
            env_key = ref[4:].strip()
            if not env_key:
                raise ValueError("supervisor api_key_ref env key is required")
            return str(os.getenv(env_key, ""))
        if ref.startswith("file:"):
            file_path = os.path.expanduser(ref[5:].strip())
            if not file_path:
                raise ValueError("supervisor api_key_ref file path is required")
            try:
                return Path(file_path).read_text(encoding="utf-8").strip()
            except OSError as exc:
                raise RuntimeError(f"failed to read supervisor api key file: {file_path}") from exc
        raise ValueError("supervisor api_key_ref must start with env: or file:")

    def _endpoint(self, config: dict[str, Any]) -> str:
        base_url = str(config.get("base_url", DEFAULT_SUPERVISOR_BASE_URL)).strip().rstrip("/")
        if not base_url:
            raise ValueError("supervisor base_url is required")
        if base_url.endswith("/chat/completions"):
            return base_url
        return f"{base_url}/chat/completions"

    def _chat(self, config: dict[str, Any], messages: list[dict[str, str]], temperature: float = 0.1) -> str:
        api_key = self.resolve_api_key(config)
        if not api_key:
            raise ValueError("supervisor api key is required")
        response = self.transport.post_json(
            self._endpoint(config),
            headers={"Authorization": f"Bearer {api_key}"},
            payload={
                "model": str(config.get("model", DEFAULT_SUPERVISOR_MODEL)).strip() or DEFAULT_SUPERVISOR_MODEL,
                "messages": messages,
                "temperature": temperature,
                "response_format": {"type": "json_object"},
            },
            timeout=self.timeout,
        )
        choices = response.get("choices", [])
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("supervisor API returned no choices")
        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        content = message.get("content", "")
        if isinstance(content, list):
            flattened = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    flattened.append(str(item.get("text", "")))
            content = "\n".join(flattened)
        text = str(content).strip()
        if not text:
            raise RuntimeError("supervisor API returned empty content")
        return text

    def _parse_json_object(self, content: str) -> dict[str, Any]:
        text = str(content).strip()
        if text.startswith("```"):
            lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
            text = "\n".join(lines).strip()
        try:
            decoded = json.loads(text)
            if isinstance(decoded, dict):
                return decoded
        except json.JSONDecodeError:
            pass
        result = extract_json_object(text)
        if result is not None:
            snippet, _ = result
            decoded = json.loads(snippet)
            if isinstance(decoded, dict):
                return decoded
        raise RuntimeError("supervisor output did not contain valid JSON object")

    def dispatch(self, config: dict[str, Any], todo: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
        if not candidates:
            raise ValueError("supervisor dispatch requires at least one candidate")
        system_prompt = str(config.get("system_prompt", DEFAULT_SUPERVISOR_PROMPT)).strip() or DEFAULT_SUPERVISOR_PROMPT
        candidate_lines = [
            f"- target={item.get('target','')} alias={item.get('alias','')} session={item.get('session','')} window={item.get('window_name','')} command={item.get('command','')}"
            for item in candidates
        ]
        user_prompt = "\n".join(
            [
                "Route this task to the best agent and return JSON only.",
                f"Task title: {todo.get('title','')}",
                f"Task detail: {todo.get('detail','')}",
                f"Task role: {todo.get('role','general')}",
                f"Task priority: {todo.get('priority','medium')}",
                "Available agents:",
                *candidate_lines,
                'Return: {"target":"...","alias":"...","reason":"...","confidence":0.0}',
            ]
        )
        payload = self._parse_json_object(self._chat(config, [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]))
        target = str(payload.get("target", "")).strip()
        candidate = next((item for item in candidates if str(item.get("target", "")).strip() == target), None)
        if candidate is None:
            raise RuntimeError("supervisor selected a target that is not in the available candidates")
        confidence = payload.get("confidence", 0)
        try:
            confidence_value = float(confidence)
        except (TypeError, ValueError):
            confidence_value = 0.0
        return {
            "target": candidate["target"],
            "alias": str(payload.get("alias", "")).strip() or str(candidate.get("alias", "")).strip(),
            "reason": str(payload.get("reason", "")).strip(),
            "confidence": max(0.0, min(confidence_value, 1.0)),
        }

    def review(self, config: dict[str, Any], todo: dict[str, Any], pane_output: str = "") -> dict[str, Any]:
        system_prompt = str(config.get("system_prompt", DEFAULT_SUPERVISOR_PROMPT)).strip() or DEFAULT_SUPERVISOR_PROMPT
        evidence_lines = [f"- {item.get('type','text')}: {item.get('content','')}" for item in (todo.get("evidence", []) or [])[:12]]
        user_prompt = "\n".join(
            [
                "Review this task and decide if it is acceptable. Return JSON only.",
                f"Task title: {todo.get('title','')}",
                f"Task detail: {todo.get('detail','')}",
                f"Current status: {todo.get('status','')}",
                f"Progress note: {todo.get('progress_note','')}",
                "Evidence:",
                *(evidence_lines or ["- none"]),
                f"Recent pane output: {pane_output[:4000]}",
                'Return: {"verdict":"accept|needs_work|blocked","summary":"...","required_fixes":["..."],"evidence":[{"type":"summary","content":"..."}]}',
            ]
        )
        payload = self._parse_json_object(self._chat(config, [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]))
        verdict = str(payload.get("verdict", "needs_work")).strip().lower() or "needs_work"
        if verdict not in {"accept", "needs_work", "blocked"}:
            verdict = "needs_work"
        evidence = payload.get("evidence", [])
        if not isinstance(evidence, list):
            evidence = []
        normalized_evidence: list[dict[str, Any]] = []
        for item in evidence:
            if not isinstance(item, dict):
                continue
            content = str(item.get("content", "")).strip()
            if not content:
                continue
            normalized_evidence.append({"type": str(item.get("type", "summary")).strip() or "summary", "content": content})
        return {
            "verdict": verdict,
            "summary": str(payload.get("summary", "")).strip(),
            "required_fixes": [str(item).strip() for item in (payload.get("required_fixes", []) or []) if str(item).strip()],
            "evidence": normalized_evidence,
        }
