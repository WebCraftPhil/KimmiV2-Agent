"""Lightweight registry used to discover and execute MCP-style tools."""

from __future__ import annotations

import asyncio
import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import pydantic


class ToolDescriptor(pydantic.BaseModel):
    """Configuration describing how to invoke a tool implementation."""

    name: str
    module: str
    function: str = "invoke"


@dataclass
class RegistryConfig:
    path: Path


class MCPRegistry:
    """Minimal registry capable of loading local tool callables."""

    def __init__(self, tools: Dict[str, ToolDescriptor], features: Dict[str, Any] | None = None) -> None:
        self._tools = tools
        self._features = features or {}

    @classmethod
    def load(cls, config: RegistryConfig) -> "MCPRegistry":
        config.path.parent.mkdir(parents=True, exist_ok=True)
        if not config.path.exists():
            config.path.write_text(json.dumps({"tools": []}, indent=2), encoding="utf-8")

        content = json.loads(config.path.read_text(encoding="utf-8"))
        descriptors = {
            item["name"]: ToolDescriptor.model_validate(item)
            for item in content.get("tools", [])
        }
        features = content.get("features", {})
        return cls(descriptors, features)

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        descriptor = self._tools.get(tool_name)
        if descriptor is None:
            raise KeyError(f"Tool '{tool_name}' not registered")

        module = importlib.import_module(descriptor.module)
        handler = getattr(module, descriptor.function)

        if asyncio.iscoroutinefunction(handler):
            return await handler(**arguments)

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: handler(**arguments))

    @property
    def features(self) -> Dict[str, Any]:
        return self._features


__all__ = ["MCPRegistry", "RegistryConfig", "ToolDescriptor"]

