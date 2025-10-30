"""Utility helpers for persisting agent turn logs."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .orchestrator import AgentTurn


def write_turn_log(turn: AgentTurn, logs_dir: Path) -> Path:
    """Serialize a turn to disk and return the written path.

    Each log file is named `<timestamp>_<uuid>.json` to make chronological
    inspection simple while avoiding collisions.
    """

    logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S")
    unique_suffix = _unique_suffix()
    log_path = logs_dir / f"{timestamp}_{unique_suffix}.json"

    payload: Dict[str, Any] = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "user": {
            "role": turn.user_message.role,
            "content": turn.user_message.content,
        },
        "assistant": {
            "role": turn.assistant_message.role,
            "content": turn.assistant_message.content,
        },
        "tool_results": turn.tool_results,
        "raw_model_reply": turn.raw_model_reply,
    }

    log_path.write_text(
        json.dumps(payload, indent=2, default=_json_fallback),
        encoding="utf-8",
    )

    return log_path


def _json_fallback(obj: Any) -> Any:
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return repr(obj)


def _unique_suffix() -> str:
    import uuid

    return uuid.uuid4().hex[:12]


__all__ = ["write_turn_log"]


