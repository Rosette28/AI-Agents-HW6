"""Entrypoint for both manual local verification AND real cloud deployment.

Each server owns its own independent `AgentSession` (no object shared
between Cop and Thief — see src/mcp_servers/session.py) so this script
works two ways:

- **Local dev** (no `MCP_SERVER_ROLE` set): starts both servers in one
  process on their configured ports (`config.yaml: mcp.*`), bound to
  127.0.0.1, for a quick ping/echo check by hand. A real game still needs
  `src/agents/orchestrator.py` to drive both — these two servers don't
  talk to each other on their own.

- **Cloud deployment**: set `MCP_SERVER_ROLE=cop` or `MCP_SERVER_ROLE=thief`
  to start only that one server, bound to `0.0.0.0` on `$PORT` (the
  platform-provided port — Render/Railway/Fly.io convention) or this
  server's configured port as a fallback. Deploy this script twice, once
  per role, as two separate services — that's what gives you two genuinely
  independent public URLs.

Run locally: python scripts/run_mcp_servers.py
Then from another shell, point a FastMCP Client at
http://127.0.0.1:<port>/mcp with the matching bearer token to ping/echo by
hand.
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.loader import load_config  # noqa: E402
from src.engine.start_positions import random_start_positions  # noqa: E402
from src.mcp_servers.cop_server import build_cop_server  # noqa: E402
from src.mcp_servers.session import AgentSession  # noqa: E402
from src.mcp_servers.thief_server import build_thief_server  # noqa: E402

_BUILDERS = {"cop": build_cop_server, "thief": build_thief_server}


async def _run_one_role(role: str, config: dict, grid_size: tuple, start_pos: tuple) -> None:
    session = AgentSession(
        role, grid_size, config["game"]["max_moves"],
        max_barriers=config["game"]["max_barriers"] if role == "cop" else 0,
        visibility_radius=config["observation"]["visibility_radius"],
    )
    session.start(start_pos)
    server = _BUILDERS[role](session)

    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", config["mcp"][f"{role}_server_port"]))
    print(f"{role.capitalize()} server -> listening on {host}:{port} (start={start_pos})")
    await server.run_http_async(host=host, port=port, show_banner=False)


async def _run_both_locally(config: dict, grid_size: tuple, cop_pos: tuple, thief_pos: tuple) -> None:
    cop_session = AgentSession("cop", grid_size, config["game"]["max_moves"],
                                config["game"]["max_barriers"], config["observation"]["visibility_radius"])
    cop_session.start(cop_pos)
    thief_session = AgentSession("thief", grid_size, config["game"]["max_moves"],
                                  0, config["observation"]["visibility_radius"])
    thief_session.start(thief_pos)

    cop_server = build_cop_server(cop_session)
    thief_server = build_thief_server(thief_session)
    cop_port = config["mcp"]["cop_server_port"]
    thief_port = config["mcp"]["thief_server_port"]

    print(f"Cop server   -> http://127.0.0.1:{cop_port}/mcp   (start={cop_pos})")
    print(f"Thief server -> http://127.0.0.1:{thief_port}/mcp (start={thief_pos})")

    await asyncio.gather(
        cop_server.run_http_async(host="127.0.0.1", port=cop_port, show_banner=False),
        thief_server.run_http_async(host="127.0.0.1", port=thief_port, show_banner=False),
    )


async def main() -> None:
    load_dotenv()
    config = load_config()
    grid_size = tuple(config["board"]["grid_size"])
    cop_pos, thief_pos = random_start_positions(grid_size)

    role = os.environ.get("MCP_SERVER_ROLE")
    if role:
        if role not in _BUILDERS:
            raise ValueError(f"MCP_SERVER_ROLE must be 'cop' or 'thief', got {role!r}")
        await _run_one_role(role, config, grid_size, cop_pos if role == "cop" else thief_pos)
    else:
        await _run_both_locally(config, grid_size, cop_pos, thief_pos)


if __name__ == "__main__":
    asyncio.run(main())
