"""MCP helper for recording sequential thinking checkpoints."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


BASE_PATH = Path(__file__).resolve().parents[3]
DEFAULT_STATE_FILE = BASE_PATH / "data" / "mcp_tool_state.json"


def _resolve_state_file(file_path: Optional[str]) -> Path:
    if not file_path:
        return DEFAULT_STATE_FILE
    candidate = Path(file_path)
    if not candidate.is_absolute():
        candidate = BASE_PATH / candidate
    return candidate


def _read_state(path: Path) -> Dict[str, Dict[str, object]]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {}


def _write_state(path: Path, state: Dict[str, Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def invoke(
    step: Optional[str] = None,
    summary: Optional[str] = None,
    reset: bool = False,
    enabled: bool = True,
    file_path: Optional[str] = None,
) -> Dict[str, object]:
    """Update the sequential thinking ledger used for observability."""

    path = _resolve_state_file(file_path)
    state = _read_state(path)
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
    _write_state(path, state)
    return record


