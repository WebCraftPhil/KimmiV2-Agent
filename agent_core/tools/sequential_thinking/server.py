"""MCP helper for recording sequential thinking checkpoints."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


BASE_PATH = Path(__file__).resolve().parents[3]
STATE_FILE = BASE_PATH / "data" / "mcp_tool_state.json"


def _read_state() -> Dict[str, Dict[str, object]]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def _write_state(state: Dict[str, Dict[str, object]]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def invoke(
    step: Optional[str] = None,
    summary: Optional[str] = None,
    reset: bool = False,
    enabled: bool = True,
) -> Dict[str, object]:
    """Update the sequential thinking ledger used for observability."""

    state = _read_state()
    record = state.get("sequentialThinking", {})

    if reset or not isinstance(record.get("steps"), list):
        record["steps"] = []

    if step:
        entry = {
            "step": step,
            "summary": summary or "",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        record.setdefault("steps", []).append(entry)

    record["enabled"] = bool(enabled)
    record["updatedAt"] = datetime.utcnow().isoformat() + "Z"

    state["sequentialThinking"] = record
    _write_state(state)
    return record


