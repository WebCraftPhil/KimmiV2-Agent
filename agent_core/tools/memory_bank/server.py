"""Local MCP memory bank implementation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


BASE_PATH = Path(__file__).resolve().parents[3]
DEFAULT_BANK_FILE = BASE_PATH / "data" / "mcp_memory_bank.json"


def _resolve_bank_file(file_path: Optional[str]) -> Path:
    if not file_path:
        return DEFAULT_BANK_FILE
    candidate = Path(file_path)
    if not candidate.is_absolute():
        candidate = BASE_PATH / candidate
    return candidate


def _read_bank(path: Path) -> Dict[str, object]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"enabled": True, "entries": []}


def _write_bank(path: Path, data: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def invoke(
    action: str = "status",
    entry: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 20,
    file_path: Optional[str] = None,
) -> Dict[str, object]:
    """Perform simple operations against the MCP memory bank."""

    path = _resolve_bank_file(file_path)
    data = _read_bank(path)
    entries = data.setdefault("entries", [])

    normalized_action = action.lower()
    if normalized_action == "append" and entry:
        payload = {
            "entry": entry,
            "tags": tags or [],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        entries.append(payload)
        data["enabled"] = True
    elif normalized_action == "clear":
        entries.clear()
    elif normalized_action == "disable":
        data["enabled"] = False
    elif normalized_action == "enable":
        data["enabled"] = True

    data.setdefault("enabled", True)
    data["updatedAt"] = datetime.utcnow().isoformat() + "Z"

    _write_bank(path, data)

    recent = entries[-limit:] if limit > 0 else entries
    return {
        "enabled": data["enabled"],
        "count": len(entries),
        "recent": recent,
        "updatedAt": data["updatedAt"],
    }


