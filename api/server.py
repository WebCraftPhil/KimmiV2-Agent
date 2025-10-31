"""FastAPI entrypoint exposing the Kimmi V2 orchestrator."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, cast

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent_core import (
    AgentConfig,
    ContentChainInput,
    ContentIdeationChain,
    Orchestrator,
)
from agent_core.logging import write_turn_log
from agent_core.memory import FileMemoryStore, MemoryConfig
from agent_core.orchestrator import AgentMessage
from agent_core.registry import MCPRegistry, RegistryConfig

from .openrouter_api import OpenRouterClient, OpenRouterSettings


class AgentRequest(BaseModel):
    prompt: Optional[str] = None
    niche: Optional[str] = None
    trendSource: Optional[str] = None
    notes: Optional[str] = None
    style: Optional[str] = None
    platform: Optional[str] = None


class AgentResponse(BaseModel):
    message: AgentMessage
    tool_results: List[Dict[str, Any]]
    raw: Dict[str, Any]


BASE_PATH = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_PATH / "data" / "logs"


def build_orchestrator() -> Orchestrator:
    settings = OpenRouterSettings()  # raises if API key missing

    memory = FileMemoryStore(
        MemoryConfig(path=BASE_PATH / "data" / "memory_store.json")
    )
    registry = MCPRegistry.load(
        RegistryConfig(path=BASE_PATH / "config" / "mcp_servers.json")
    )
    lm_client = OpenRouterClient(settings=settings)
    content_chain = ContentIdeationChain(lm_client)

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
        content_chain=content_chain,
    )


@lru_cache(maxsize=1)
def orchestrator_singleton() -> Orchestrator:
    return build_orchestrator()


app = FastAPI(title="Kimmi V2 Agent API", version="0.1.0")


@app.post("/run_agent", response_model=AgentResponse)
async def run_agent(request: AgentRequest) -> AgentResponse:
    orchestrator = orchestrator_singleton()
    if request.niche and request.notes:
        style = (request.style or "AIDA").upper()
        if style not in {"AIDA", "PAS"}:
            style = "AIDA"
        payload = ContentChainInput(
            niche=request.niche,
            trend_source=request.trendSource or "unspecified",
            notes=request.notes,
            style=cast(Literal["AIDA", "PAS"], style),
            platform=(request.platform or "TikTok"),
        )
        turn = await orchestrator.run_content_pipeline(payload)
    else:
        prompt = (request.prompt or "").strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt must not be empty")
        turn = await orchestrator.run(prompt)
    write_turn_log(turn, LOGS_DIR)
    return AgentResponse(
        message=turn.assistant_message,
        tool_results=turn.tool_results,
        raw=turn.raw_model_reply,
    )


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


