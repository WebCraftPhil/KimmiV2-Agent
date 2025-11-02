"""Agent orchestration loop for Kimmi V2."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Protocol

from .chains.content_ideation import (
    ContentChainArtifacts,
    ContentChainError,
    ContentChainInput,
    ContentIdeationChain,
    FallbackString,
)
from .models import AgentMessage, ModelReply, ToolCall


class MemoryStore(Protocol):
    """Interface consumed by the orchestrator for memory operations."""

    async def load_context(self) -> Iterable[AgentMessage]:
        ...

    async def append(self, message: AgentMessage) -> None:
        ...

    async def record_tool_call(self, tool_name: str, arguments: Dict[str, Any], result: Any) -> None:
        ...


class ToolRegistry(Protocol):
    """Interface for resolving MCP tools."""

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        ...


class LanguageModelClient(Protocol):
    """Interface expected from the OpenRouter wrapper."""

    async def generate(self, messages: List[AgentMessage]) -> ModelReply:
        ...


@dataclass
class AgentConfig:
    """Configurable knobs for orchestrator behaviour."""

    system_prompt: str
    model: str
    max_tool_iterations: int = 3


@dataclass
class AgentTurn:
    """Outcome returned by the orchestrator for a single user input."""

    user_message: AgentMessage
    assistant_message: AgentMessage
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    raw_model_reply: Dict[str, Any] = field(default_factory=dict)


class Orchestrator:
    """Coordinates model calls, tool invocations, and memory updates."""

    def __init__(
        self,
        config: AgentConfig,
        memory: MemoryStore,
        registry: ToolRegistry,
        lm_client: LanguageModelClient,
        content_chain: Optional[ContentIdeationChain] = None,
    ) -> None:
        self._config = config
        self._memory = memory
        self._registry = registry
        self._lm = lm_client
        self._content_chain = content_chain
        self._logger = logging.getLogger(__name__)

    async def run(self, user_text: str) -> AgentTurn:
        """Run a full reasoning turn for the provided user text."""

        user_message = AgentMessage(role="user", content=user_text)

        conversation: List[AgentMessage] = [
            AgentMessage(role="system", content=self._config.system_prompt)
        ]
        conversation.extend(await self._load_transcript())
        conversation.append(user_message)

        assistant_reply, tool_results = await self._reason(conversation)

        await self._memory.append(user_message)
        await self._memory.append(assistant_reply.message)

        turn = AgentTurn(
            user_message=user_message,
            assistant_message=assistant_reply.message,
            tool_results=tool_results,
            raw_model_reply=assistant_reply.raw,
        )
        return turn

    async def run_content_pipeline(self, payload: ContentChainInput) -> AgentTurn:
        if self._content_chain is None:
            raise RuntimeError("Content chain not configured")

        user_message = AgentMessage(role="user", content=json.dumps(asdict(payload)))

        try:
            artifacts = await self._content_chain.run(payload)
        except ContentChainError as exc:
            assistant_message = AgentMessage(role="assistant", content=FallbackString)
            raw_model_reply: Dict[str, Any] = {
                "chain": "contentIdeation",
                "error": str(exc),
            }
            tool_results: List[Dict[str, Any]] = []
        else:
            assistant_message = AgentMessage(
                role="assistant",
                content=json.dumps(artifacts.result, indent=2),
            )
            raw_model_reply = {
                "chain": "contentIdeation",
                "steps": artifacts.raw_replies,
            }
            tool_results = [
                {"step": step, "output": output}
                for step, output in artifacts.step_outputs.items()
            ]

            await self._after_content_chain(payload, artifacts)

        await self._memory.append(user_message)
        await self._memory.append(assistant_message)

        return AgentTurn(
            user_message=user_message,
            assistant_message=assistant_message,
            tool_results=tool_results,
            raw_model_reply=raw_model_reply,
        )

    async def _load_transcript(self) -> List[AgentMessage]:
        messages = []
        async for message in _async_iterable(self._memory.load_context()):
            messages.append(message)
        return messages

    async def _reason(
        self, base_conversation: List[AgentMessage]
    ) -> tuple[ModelReply, List[Dict[str, Any]]]:
        conversation = list(base_conversation)
        tool_results: List[Dict[str, Any]] = []

        for iteration in range(self._config.max_tool_iterations):
            model_reply = await self._lm.generate(conversation)
            if not model_reply.tool_calls:
                return model_reply, tool_results

            # Execute tools sequentially for now.
            for call in model_reply.tool_calls:
                result = await self._registry.execute(call.name, call.arguments)
                await self._memory.record_tool_call(call.name, call.arguments, result)

                tool_message = AgentMessage(
                    role="tool",
                    name=call.name,
                    content=_stringify_tool_result(result),
                    metadata={"iteration": iteration},
                )
                conversation.append(model_reply.message)
                conversation.append(tool_message)
                tool_results.append(
                    {
                        "tool": call.name,
                        "arguments": call.arguments,
                        "result": result,
                    }
                )

        # Fallback: return last reply if tool loop exceeded.
        return model_reply, tool_results

    async def _after_content_chain(
        self, payload: ContentChainInput, artifacts: ContentChainArtifacts
    ) -> None:
        features = getattr(self._registry, "features", {})
        await self._emit_sequential_checkpoints(features, artifacts)
        await self._update_memory_bank(features, payload, artifacts)

    async def _emit_sequential_checkpoints(
        self, features: Dict[str, Any], artifacts: ContentChainArtifacts
    ) -> None:
        config = (features.get("sequentialThinking") or {})
        if not config.get("enabled"):
            return

        args: Dict[str, Any] = {"reset": True}
        file_path = config.get("path")
        if file_path:
            args["file_path"] = file_path

        try:
            await self._registry.execute("sequential_thinking", args)
            for step_name, output in artifacts.step_outputs.items():
                summary = json.dumps(output, ensure_ascii=False)
                if len(summary) > 400:
                    summary = summary[:397] + "..."
                step_args: Dict[str, Any] = {
                    "step": step_name,
                    "summary": summary,
                }
                if file_path:
                    step_args["file_path"] = file_path
                await self._registry.execute("sequential_thinking", step_args)
        except Exception:
            self._logger.exception("Failed to emit sequential thinking checkpoints")

    async def _update_memory_bank(
        self,
        features: Dict[str, Any],
        payload: ContentChainInput,
        artifacts: ContentChainArtifacts,
    ) -> None:
        config = (features.get("memoryBank") or {})
        if not config.get("enabled"):
            return

        entry = (
            f"{payload.niche} | {payload.trend_source} | {artifacts.result.get('summary', '')}"
        )
        tags = [payload.style, payload.platform, payload.trend_source]
        tags = [tag for tag in tags if tag]

        args: Dict[str, Any] = {
            "action": "append",
            "entry": entry,
            "tags": tags[:5],
        }
        file_path = config.get("path")
        if file_path:
            args["file_path"] = file_path

        try:
            await self._registry.execute("mcp_memory_bank", args)
        except Exception:
            self._logger.exception("Failed to append to MCP memory bank")


async def _async_iterable(iterable: Iterable[AgentMessage]) -> Iterable[AgentMessage]:
    """Utility to iterate over async or sync iterables uniformly."""

    if hasattr(iterable, "__aiter__"):
        async for item in iterable:  # type: ignore[assignment]
            yield item
    else:
        for item in iterable:
            yield item


def _stringify_tool_result(result: Any) -> str:
    if isinstance(result, str):
        return result
    return repr(result)

