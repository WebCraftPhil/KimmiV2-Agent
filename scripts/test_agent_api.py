"""CLI utility to run a smoke test against the local agent API server."""

from __future__ import annotations

import argparse
import asyncio
import json

import aiohttp


async def _run(prompt: str, url: str, is_json_input: bool) -> None:
    """Send a request to the agent server and print the response."""
    headers = {"Content-Type": "application/json"}

    if is_json_input:
        try:
            payload = json.loads(prompt)
        except json.JSONDecodeError:
            print("Error: --json-input flag was used, but the prompt is not valid JSON.")
            return
    else:
        payload = {"prompt": prompt}

    print(f"▶️  Sending request to {url} with payload:")
    print(json.dumps(payload, indent=2))

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, headers=headers) as response:
                response_json = await response.json()
                print("\n✅ Server Response:")
                print(json.dumps(response_json, indent=2))
                response.raise_for_status()
        except aiohttp.ClientError as e:
            print(f"\n❌ Error connecting to agent server: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent API Smoke Test")
    parser.add_argument("prompt", help="User prompt or a JSON string for structured input.")
    parser.add_argument(
        "--url",
        default="http://localhost:8000/run_agent",
        help="URL of the agent endpoint (default: %(default)s)",
    )
    parser.add_argument(
        "--json-input",
        action="store_true",
        help="Treat the prompt argument as a raw JSON string payload.",
    )
    args = parser.parse_args()
    asyncio.run(_run(args.prompt, args.url, args.json_input))


if __name__ == "__main__":
    main()