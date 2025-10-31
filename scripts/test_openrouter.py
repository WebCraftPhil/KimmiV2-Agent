"""CLI utility to run a smoke test against OpenRouter."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import List

from pydantic import ValidationError

from agent_core.models import AgentMessage
from api.openrouter_api import OpenRouterClient, OpenRouterSettings


async def _run(prompt: str, system_prompt: str) -> None:
    try:
        settings = OpenRouterSettings()
    except ValidationError as exc:  # pragma: no cover - CLI helper
        print("Failed to load OpenRouter settings:", exc, file=sys.stderr)
        print(
            "Ensure OPENROUTER_API_KEY is set in your environment or .env file.",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc

    client = OpenRouterClient(settings=settings)
    try:
        conversation: List[AgentMessage] = [
            AgentMessage(role="system", content=system_prompt),
            AgentMessage(role="user", content=prompt),
        ]
        reply = await client.generate(conversation)
    finally:
        await client.aclose()

    print(json.dumps(reply.raw, indent=2))


def main() -> None:  # pragma: no cover - CLI entrypoint
    parser = argparse.ArgumentParser(description="OpenRouter smoke test")
    parser.add_argument(
        "prompt",
        help="User prompt to send to the model",
    )
    parser.add_argument(
        "--system",
        dest="system_prompt",
        default="You are Kimmi V2, a marketing strategy assistant.",
        help="System prompt to seed the conversation (default: %(default)s)",
    )

    args = parser.parse_args()
    asyncio.run(_run(args.prompt, args.system_prompt))


if __name__ == "__main__":  # pragma: no cover
    main()

