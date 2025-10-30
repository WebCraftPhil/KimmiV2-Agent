"""Minimal example MCP server shim for local testing."""

from __future__ import annotations

from datetime import datetime
from typing import Optional


async def get_status(category: Optional[str] = None) -> dict:
    """Return a simple payload demonstrating tool execution."""

    return {
        "category": category or "general",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "message": "custom_mcp_example is online",
    }


def invoke(**kwargs):
    """Synchronous fallback used by the registry by default."""

    import asyncio

    return asyncio.run(get_status(**kwargs))


