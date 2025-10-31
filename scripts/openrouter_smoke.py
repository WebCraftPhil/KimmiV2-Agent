"""Run a quick prompt against OpenRouter to verify credentials and model access."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.openrouter_api import OpenRouterClient, OpenRouterSettings
from agent_core.models import AgentMessage


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

        try:
            reply = await client.generate(messages)
        except Exception as exc:  # pylint: disable=broad-except
            print("=== OpenRouter Smoke Test FAILED ===")
            print(f"Error: {exc}")
            if hasattr(exc, 'response'):
                resp = getattr(exc, 'response')
                print(f"Status: {resp.status_code}")
                try:
                    print(resp.text)
                except Exception:  # pylint: disable=broad-except
                    pass
            raise

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


