"""Workflow metrics and event queries mixin."""

from __future__ import annotations

from .normalize import *  # noqa: F401,F403

class ProfileStoreMetricsMixin:
    def list_events(self, profile_name: str = "", target: str = "", limit: int = 200) -> list[dict[str, Any]]:
        with self._lock:
            result: list[dict[str, Any]] = []
            for entry in self._list_audit_logs_unlocked(profile_name=profile_name, target=target, limit=max(1, limit * 2)):
                result.append(
                    {
                        "id": entry["id"],
                        "source": "audit",
                        "action": entry["action"],
                        "profile": entry["profile"],
                        "target": entry["target"],
                        "todo_id": entry.get("todo_id", ""),
                        "status": entry.get("status", ""),
                        "actor": entry.get("actor", ""),
                        "note": entry.get("note", ""),
                        "created_at": entry["created_at"],
                    }
                )
            for todo in self._list_todos_unlocked(profile_name=profile_name, target=target):
                for event in todo.get("events", []) or []:
                    if not isinstance(event, dict):
                        continue
                    normalized_event = normalize_todo_event(event)
                    result.append(
                        {
                            "id": normalized_event["id"],
                            "source": "todo",
                            "action": normalized_event["type"],
                            "profile": todo["profile"],
                            "target": todo["target"],
                            "todo_id": todo["id"],
                            "status": normalized_event.get("status", ""),
                            "actor": normalized_event.get("actor", ""),
                            "note": normalized_event.get("note", ""),
                            "created_at": normalized_event["created_at"],
                        }
                    )
            sorted_events = sorted(
                result,
                key=lambda item: (str(item.get("created_at", "")), str(item.get("id", ""))),
                reverse=True,
            )
            return sorted_events[: max(1, limit)]

    def workflow_metrics(self, profile_name: str = "", target: str = "", window_days: int = 30) -> dict[str, Any]:
        with self._lock:
            days = max(1, min(int(window_days), 365))
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)
            todos = self._list_todos_unlocked(profile_name=profile_name, target=target)
            dispatch_samples: list[float] = []
            done_samples: list[float] = []
            verify_samples: list[float] = []
            trend: dict[str, dict[str, Any]] = {}

            for todo in todos:
                created_at = parse_utc(todo.get("created_at"))
                if not created_at or created_at < cutoff:
                    continue
                in_progress_at: datetime | None = None
                done_at: datetime | None = None
                verified_at: datetime | None = parse_utc(todo.get("verified_at"))
                for event in (todo.get("events", []) or []):
                    if not isinstance(event, dict):
                        continue
                    event_status = str(event.get("status", "")).strip().lower()
                    event_time = parse_utc(event.get("created_at"))
                    if event_time is None:
                        continue
                    if event_status == "in_progress":
                        in_progress_at = event_time if in_progress_at is None else min(in_progress_at, event_time)
                    if event_status == "done":
                        done_at = event_time if done_at is None else min(done_at, event_time)
                    if event_status == "verified":
                        verified_at = event_time if verified_at is None else min(verified_at, event_time)
                if in_progress_at and in_progress_at >= created_at:
                    dispatch_samples.append((in_progress_at - created_at).total_seconds())
                if done_at and done_at >= created_at:
                    done_samples.append((done_at - created_at).total_seconds())
                if verified_at and done_at and verified_at >= done_at:
                    verify_samples.append((verified_at - done_at).total_seconds())

                week_key = created_at.strftime("%G-W%V")
                bucket = trend.setdefault(
                    week_key,
                    {"week": week_key, "dispatch_seconds": [], "done_seconds": [], "verify_seconds": [], "count": 0},
                )
                bucket["count"] += 1
                if in_progress_at and in_progress_at >= created_at:
                    bucket["dispatch_seconds"].append((in_progress_at - created_at).total_seconds())
                if done_at and done_at >= created_at:
                    bucket["done_seconds"].append((done_at - created_at).total_seconds())
                if verified_at and done_at and verified_at >= done_at:
                    bucket["verify_seconds"].append((verified_at - done_at).total_seconds())

            sends = self._list_audit_logs_unlocked(profile_name=profile_name, target=target, limit=5000)
            send_events = [entry for entry in sends if entry.get("action") == "agent.send"]
            misrouted = 0
            for entry in send_events:
                payload = entry.get("payload", {})
                if isinstance(payload, dict) and bool(payload.get("misroute")):
                    misrouted += 1

            trend_rows = []
            for week in sorted(trend.keys()):
                row = trend[week]
                dispatch_avg = sum(row["dispatch_seconds"]) / len(row["dispatch_seconds"]) if row["dispatch_seconds"] else None
                done_avg = sum(row["done_seconds"]) / len(row["done_seconds"]) if row["done_seconds"] else None
                verify_avg = sum(row["verify_seconds"]) / len(row["verify_seconds"]) if row["verify_seconds"] else None
                trend_rows.append(
                    {
                        "week": week,
                        "todo_count": row["count"],
                        "t_dispatch_avg_sec": round(dispatch_avg, 1) if dispatch_avg is not None else None,
                        "t_done_avg_sec": round(done_avg, 1) if done_avg is not None else None,
                        "t_verify_avg_sec": round(verify_avg, 1) if verify_avg is not None else None,
                    }
                )

        dispatch_avg = sum(dispatch_samples) / len(dispatch_samples) if dispatch_samples else None
        done_avg = sum(done_samples) / len(done_samples) if done_samples else None
        verify_avg = sum(verify_samples) / len(verify_samples) if verify_samples else None
        misroute_rate = (misrouted / len(send_events) * 100.0) if send_events else 0.0
        return {
            "window_days": days,
            "sample_todo_count": len(dispatch_samples) if dispatch_samples else len([todo for todo in todos if parse_utc(todo.get("created_at")) and parse_utc(todo.get("created_at")) >= cutoff]),
            "t_dispatch_avg_sec": round(dispatch_avg, 1) if dispatch_avg is not None else None,
            "t_done_avg_sec": round(done_avg, 1) if done_avg is not None else None,
            "t_verify_avg_sec": round(verify_avg, 1) if verify_avg is not None else None,
            "misroute_pct": round(misroute_rate, 2),
            "trend": trend_rows,
        }

    def bulk_workflow_metrics(self, profile_names: list[str], window_days: int = 30) -> dict[str, dict[str, Any]]:
        """Compute workflow metrics for multiple profiles in a single pass over todos and audit logs."""
        days = max(1, min(int(window_days), 365))
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        data = self._read()

        # Load all todos once
        all_todos = []
        for item in data.get("todos", []):
            if isinstance(item, dict):
                all_todos.append(normalize_todo(item))

        # Load all audit logs once
        all_audit = []
        for item in data.get("audit_logs", []):
            if isinstance(item, dict):
                all_audit.append(normalize_audit_entry(item))

        # Group todos by profile
        todos_by_profile: dict[str, list[dict[str, Any]]] = {name: [] for name in profile_names}
        todos_by_profile[""] = []  # global bucket
        for todo in all_todos:
            profile = todo.get("profile", "")
            if profile in todos_by_profile:
                todos_by_profile[profile].append(todo)
            todos_by_profile[""].append(todo)

        # Group send events by profile
        audit_by_profile: dict[str, list[dict[str, Any]]] = {name: [] for name in profile_names}
        audit_by_profile[""] = []
        for entry in all_audit:
            if entry.get("action") != "agent.send":
                continue
            profile = entry.get("profile", "")
            if profile in audit_by_profile:
                audit_by_profile[profile].append(entry)
            audit_by_profile[""].append(entry)

        def _compute(todos: list[dict[str, Any]], send_events: list[dict[str, Any]]) -> dict[str, Any]:
            dispatch_samples: list[float] = []
            done_samples: list[float] = []
            verify_samples: list[float] = []
            trend: dict[str, dict[str, Any]] = {}

            for todo in todos:
                created_at = parse_utc(todo.get("created_at"))
                if not created_at or created_at < cutoff:
                    continue
                in_progress_at: datetime | None = None
                done_at: datetime | None = None
                verified_at: datetime | None = parse_utc(todo.get("verified_at"))
                for event in (todo.get("events", []) or []):
                    if not isinstance(event, dict):
                        continue
                    event_status = str(event.get("status", "")).strip().lower()
                    event_time = parse_utc(event.get("created_at"))
                    if event_time is None:
                        continue
                    if event_status == "in_progress":
                        in_progress_at = event_time if in_progress_at is None else min(in_progress_at, event_time)
                    if event_status == "done":
                        done_at = event_time if done_at is None else min(done_at, event_time)
                    if event_status == "verified":
                        verified_at = event_time if verified_at is None else min(verified_at, event_time)
                if in_progress_at and in_progress_at >= created_at:
                    dispatch_samples.append((in_progress_at - created_at).total_seconds())
                if done_at and done_at >= created_at:
                    done_samples.append((done_at - created_at).total_seconds())
                if verified_at and done_at and verified_at >= done_at:
                    verify_samples.append((verified_at - done_at).total_seconds())

                week_key = created_at.strftime("%G-W%V")
                bucket = trend.setdefault(
                    week_key,
                    {"week": week_key, "dispatch_seconds": [], "done_seconds": [], "verify_seconds": [], "count": 0},
                )
                bucket["count"] += 1
                if in_progress_at and in_progress_at >= created_at:
                    bucket["dispatch_seconds"].append((in_progress_at - created_at).total_seconds())
                if done_at and done_at >= created_at:
                    bucket["done_seconds"].append((done_at - created_at).total_seconds())
                if verified_at and done_at and verified_at >= done_at:
                    bucket["verify_seconds"].append((verified_at - done_at).total_seconds())

            misrouted = 0
            for entry in send_events:
                payload = entry.get("payload", {})
                if isinstance(payload, dict) and bool(payload.get("misroute")):
                    misrouted += 1

            trend_rows = []
            for week in sorted(trend.keys()):
                row = trend[week]
                dispatch_avg = sum(row["dispatch_seconds"]) / len(row["dispatch_seconds"]) if row["dispatch_seconds"] else None
                done_avg = sum(row["done_seconds"]) / len(row["done_seconds"]) if row["done_seconds"] else None
                verify_avg = sum(row["verify_seconds"]) / len(row["verify_seconds"]) if row["verify_seconds"] else None
                trend_rows.append({
                    "week": week,
                    "todo_count": row["count"],
                    "t_dispatch_avg_sec": round(dispatch_avg, 1) if dispatch_avg is not None else None,
                    "t_done_avg_sec": round(done_avg, 1) if done_avg is not None else None,
                    "t_verify_avg_sec": round(verify_avg, 1) if verify_avg is not None else None,
                })

            dispatch_avg = sum(dispatch_samples) / len(dispatch_samples) if dispatch_samples else None
            done_avg = sum(done_samples) / len(done_samples) if done_samples else None
            verify_avg = sum(verify_samples) / len(verify_samples) if verify_samples else None
            misroute_rate = (misrouted / len(send_events) * 100.0) if send_events else 0.0
            return {
                "window_days": days,
                "sample_todo_count": len(dispatch_samples) if dispatch_samples else len([t for t in todos if parse_utc(t.get("created_at")) and parse_utc(t.get("created_at")) >= cutoff]),
                "t_dispatch_avg_sec": round(dispatch_avg, 1) if dispatch_avg is not None else None,
                "t_done_avg_sec": round(done_avg, 1) if done_avg is not None else None,
                "t_verify_avg_sec": round(verify_avg, 1) if verify_avg is not None else None,
                "misroute_pct": round(misroute_rate, 2),
                "trend": trend_rows,
            }

        result: dict[str, dict[str, Any]] = {}
        for name in profile_names:
            result[name] = _compute(todos_by_profile.get(name, []), audit_by_profile.get(name, []))
        # Also compute global metrics (empty profile_name)
        result[""] = _compute(todos_by_profile[""], audit_by_profile[""])
        return result
