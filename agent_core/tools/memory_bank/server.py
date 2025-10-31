"""Local MCP memory bank implementation."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


BASE_PATH = Path(__file__).resolve().parents[3]
BANK_FILE = BASE_PATH / "data" / "mcp_memory_bank.json"


def _read_bank() -> Dict[str, object]:
    if BANK_FILE.exists():
        try:
            return json.loads(BANK_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"enabled": True, "entries": []}


def _write_bank(data: Dict[str, object]) -> None:
    BANK_FILE.parent.mkdir(parents=True, exist_ok=True)
    BANK_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def invoke(
    action: str = "status",
    entry: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 20,
) -> Dict[str, object]:
    """Perform simple operations against the MCP memory bank."""

    data = _read_bank()
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

    _write_bank(data)

    recent = entries[-limit:] if limit > 0 else entries
    return {
        "enabled": data["enabled"],
        "count": len(entries),
        "recent": recent,
        "updatedAt": data["updatedAt"],
    }


