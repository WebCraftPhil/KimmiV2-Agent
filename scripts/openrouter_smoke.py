"""Run a quick prompt against OpenRouter to verify credentials and model access."""

from __future__ import annotations

import asyncio
import json

from api.openrouter_api import OpenRouterClient, OpenRouterSettings
from agent_core.orchestrator import AgentMessage


async def run_smoke_test() -> None:
    settings = OpenRouterSettings()
    client = OpenRouterClient(settings=settings)

    try:
        messages = [
            AgentMessage(
                role="system",
                content="You are a diagnostics assistant. Respond with compact JSON only.",
            ),
            AgentMessage(
                role="user",
                content="Return a JSON object with keys status and model, confirming you received this message.",
            ),
        ]

        reply = await client.generate(messages)

        print("=== OpenRouter Smoke Test ===")
        print(f"Model: {settings.default_model}")
        print("Assistant Reply:")
        print(_pretty_json_or_raw(reply.message.content))
        if reply.tool_calls:
            print(f"Tool calls requested: {len(reply.tool_calls)}")
    finally:
        await client.aclose()


def _pretty_json_or_raw(content: str) -> str:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return content
    return json.dumps(parsed, indent=2)


if __name__ == "__main__":
    asyncio.run(run_smoke_test())


