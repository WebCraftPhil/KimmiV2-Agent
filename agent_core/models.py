"""Shared Pydantic models for Kimmi V2 agent messaging."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    """Structured chat message passed to / from the model."""

    role: str
    content: str
    name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    """Represents a single tool invocation requested by the model."""

    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ModelReply(BaseModel):
    """Normalized response from the language model."""

    message: AgentMessage
    tool_calls: List[ToolCall] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)


__all__ = ["AgentMessage", "ModelReply", "ToolCall"]


