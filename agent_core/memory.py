"""Conversation memory utilities for Kimmi V2."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from .orchestrator import AgentMessage


@dataclass
class MemoryConfig:
    path: Path


class FileMemoryStore:
    """Simple JSON-backed memory suitable for local development."""

    def __init__(self, config: MemoryConfig) -> None:
        self._path = config.path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write({"messages": [], "tool_history": []})

    async def load_context(self) -> Iterable[AgentMessage]:
        data = await asyncio.to_thread(self._read)
        messages = data.get("messages", [])
        return [AgentMessage.model_validate(msg) for msg in messages]

    async def append(self, message: AgentMessage) -> None:
        await asyncio.to_thread(self._append_message, message.model_dump())

    async def record_tool_call(self, tool_name: str, arguments: dict, result: object) -> None:
        payload = {
            "tool": tool_name,
            "arguments": arguments,
            "result": result,
        }
        await asyncio.to_thread(self._append_tool_record, payload)

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _append_message(self, message: dict) -> None:
        data = self._read()
        data.setdefault("messages", []).append(message)
        self._write(data)

    def _append_tool_record(self, record: dict) -> None:
        data = self._read()
        data.setdefault("tool_history", []).append(record)
        self._write(data)

    def _read(self) -> dict:
        raw = self._path.read_text(encoding="utf-8")
        return json.loads(raw) if raw else {"messages": [], "tool_history": []}

    def _write(self, data: dict) -> None:
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")


__all__ = ["FileMemoryStore", "MemoryConfig"]

