"""Manual verification entrypoint: starts the Cop and Thief MCP servers on
their own configured ports (per config.yaml: mcp.cop_server_port /
mcp.thief_server_port) inside one process, sharing one GameSession so a real
move/message exchanged on one port is visible through the other.

Run: python scripts/run_mcp_servers.py
Then from another shell, point a FastMCP Client at
http://127.0.0.1:<port>/mcp with the matching bearer token to ping/echo or
drive a sub-game by hand.
"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.loader import load_config  # noqa: E402
from src.engine.start_positions import random_start_positions  # noqa: E402
from src.mcp_servers.cop_server import build_cop_server  # noqa: E402
from src.mcp_servers.session import GameSession  # noqa: E402
from src.mcp_servers.thief_server import build_thief_server  # noqa: E402


async def main() -> None:
    load_dotenv()
    config = load_config()

    grid_size = tuple(config["board"]["grid_size"])
    session = GameSession(grid_size, config["game"]["max_moves"], config["game"]["max_barriers"])
    cop_pos, thief_pos = random_start_positions(grid_size)
    session.start(cop_pos, thief_pos)

    cop_server = build_cop_server(session)
    thief_server = build_thief_server(session)
    cop_port = config["mcp"]["cop_server_port"]
    thief_port = config["mcp"]["thief_server_port"]

    print(f"Cop server   -> http://127.0.0.1:{cop_port}/mcp   (start={cop_pos})")
    print(f"Thief server -> http://127.0.0.1:{thief_port}/mcp (start={thief_pos})")

    await asyncio.gather(
        cop_server.run_http_async(host="127.0.0.1", port=cop_port, show_banner=False),
        thief_server.run_http_async(host="127.0.0.1", port=thief_port, show_banner=False),
    )


if __name__ == "__main__":
    asyncio.run(main())
