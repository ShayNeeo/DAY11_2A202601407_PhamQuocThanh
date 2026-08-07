"""
Assignment 11 — Audit Log starter (TODO).

Records every interaction for forensics. Never blocks by itself —
other layers catch attacks; this layer makes them reviewable.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone


class AuditLogPlugin:
    """Framework-agnostic audit logger (wire into ADK callbacks or your pipeline)."""

    def __init__(self):
        self.name = "audit_log"
        self.logs: list[dict] = []
        self._open: dict[str, float] = {}

    def record_input(self, *, user_id: str, text: str, request_id: str | None = None) -> str:
        req_id = request_id or f"req_{len(self.logs)+1}"
        self._open[req_id] = datetime.now(timezone.utc).timestamp()
        return req_id

    def record_output(
        self,
        *,
        user_id: str,
        text: str,
        blocked: bool = False,
        layer: str | None = None,
        request_id: str | None = None,
    ):
        req_id = request_id or f"req_{len(self.logs)+1}"
        start_t = self._open.pop(req_id, datetime.now(timezone.utc).timestamp())
        end_t = datetime.now(timezone.utc).timestamp()
        latency = end_t - start_t
        log_entry = {
            "request_id": req_id,
            "timestamp": utc_now_iso(),
            "user_id": user_id,
            "output_text": text,
            "blocked": blocked,
            "layer": layer,
            "latency_seconds": round(latency, 4),
        }
        self.logs.append(log_entry)

    def export_json(self, filepath: str = "outputs/audit_log.json"):
        """Write logs to disk (JSON array)."""
        from pathlib import Path
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.logs, indent=2, ensure_ascii=False), encoding="utf-8")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
