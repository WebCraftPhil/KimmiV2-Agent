"""FastAPI entrypoint exposing the Kimmi V2 orchestrator."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent_core import AgentConfig, Orchestrator
from agent_core.memory import FileMemoryStore, MemoryConfig
from agent_core.orchestrator import AgentMessage
from agent_core.registry import MCPRegistry, RegistryConfig

from .openrouter_api import OpenRouterClient, OpenRouterSettings


class AgentRequest(BaseModel):
    prompt: str


class AgentResponse(BaseModel):
    message: AgentMessage
    tool_results: List[Dict[str, Any]]
    raw: Dict[str, Any]


def build_orchestrator() -> Orchestrator:
    settings = OpenRouterSettings()  # raises if API key missing
    base_path = Path(__file__).resolve().parent.parent

    memory = FileMemoryStore(
        MemoryConfig(path=base_path / "data" / "memory_store.json")
    )
    registry = MCPRegistry.load(
        RegistryConfig(path=base_path / "config" / "mcp_servers.json")
    )
    lm_client = OpenRouterClient(settings=settings)

    agent_config = AgentConfig(
        system_prompt=(
            "You are Kimmi V2, an autonomous marketing strategist. "
            "Respond with JSON-friendly structures and cite tool usage."
        ),
        model=settings.default_model,
    )

    return Orchestrator(
        config=agent_config,
        memory=memory,
        registry=registry,
        lm_client=lm_client,
    )


@lru_cache(maxsize=1)
def orchestrator_singleton() -> Orchestrator:
    return build_orchestrator()


app = FastAPI(title="Kimmi V2 Agent API", version="0.1.0")


@app.post("/run_agent", response_model=AgentResponse)
async def run_agent(request: AgentRequest) -> AgentResponse:
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt must not be empty")

    orchestrator = orchestrator_singleton()
    turn = await orchestrator.run(request.prompt)
    return AgentResponse(
        message=turn.assistant_message,
        tool_results=turn.tool_results,
        raw=turn.raw_model_reply,
    )


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


