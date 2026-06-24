"""Manual verification: pings both deployed MCP servers (COP_MCP_URL /
THIEF_MCP_URL in .env) over real HTTPS, with the matching bearer token,
and reports whether each is publicly reachable.

Run: python scripts/check_cloud_reachability.py
"""

import asyncio
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os  # noqa: E402

from fastmcp import Client  # noqa: E402


async def _check(name: str, url: str, token: str) -> None:
    if not url or not token:
        print(f"{name}: SKIPPED — URL or token not set in .env")
        return
    start = time.monotonic()
    try:
        async with Client(url, auth=token, timeout=60.0) as client:
            result = await client.call_tool("ping")
        elapsed = time.monotonic() - start
        print(f"{name}: OK -> {result.data} ({elapsed:.1f}s, url={url})")
    except Exception as exc:
        elapsed = time.monotonic() - start
        print(f"{name}: FAILED after {elapsed:.1f}s -> {type(exc).__name__}: {exc} (url={url})")


async def main() -> None:
    load_dotenv()
    await _check("Cop server", os.environ.get("COP_MCP_URL", ""), os.environ.get("COP_MCP_AUTH_TOKEN", ""))
    await _check("Thief server", os.environ.get("THIEF_MCP_URL", ""), os.environ.get("THIEF_MCP_AUTH_TOKEN", ""))


if __name__ == "__main__":
    asyncio.run(main())
