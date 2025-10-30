"""Async OpenRouter client wrapper."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx
from pydantic_settings import BaseSettings

from agent_core.orchestrator import AgentMessage, ModelReply, ToolCall

logger = logging.getLogger(__name__)


class OpenRouterSettings(BaseSettings):
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    default_model: str = "moonshotai/kimi-dev-72b:free"
    request_timeout: float = 60.0

    class Config:
        env_prefix = "OPENROUTER_"


class OpenRouterClient:
    """Handles chat completions against OpenRouter."""

    def __init__(self, settings: Optional[OpenRouterSettings] = None) -> None:
        self._settings = settings or OpenRouterSettings()
        self._client = httpx.AsyncClient(timeout=self._settings.request_timeout)

    async def generate(self, messages: List[AgentMessage]) -> ModelReply:
        payload = {
            "model": self._settings.default_model,
            "messages": [msg.model_dump() for msg in messages],
        }

        logger.debug("OpenRouter payload: %s", payload)

        response = await self._client.post(
            self._settings.base_url,
            json=payload,
            headers={"Authorization": f"Bearer {self._settings.api_key}"},
        )
        response.raise_for_status()
        data = response.json()

        message_data: Dict[str, Any] = data["choices"][0]["message"]
        tool_calls = _parse_tool_calls(message_data.get("tool_calls") or [])
        message = AgentMessage.model_validate(message_data)

        return ModelReply(message=message, tool_calls=tool_calls, raw=data)

    async def aclose(self) -> None:
        await self._client.aclose()


def _parse_tool_calls(raw_calls: List[Dict[str, Any]]) -> List[ToolCall]:
    parsed = []
    for item in raw_calls:
        function = item.get("function", {})
        arguments: Dict[str, Any]
        if isinstance(function.get("arguments"), str):
            import json

            try:
                arguments = json.loads(function["arguments"])
            except json.JSONDecodeError:
                logger.warning("Failed to parse function arguments: %s", function["arguments"])
                arguments = {}
        else:
            arguments = function.get("arguments") or {}

        parsed.append(
            ToolCall(
                name=function.get("name", item.get("name", "")),
                arguments=arguments,
            )
        )
    return parsed


__all__ = ["OpenRouterClient", "OpenRouterSettings"]


