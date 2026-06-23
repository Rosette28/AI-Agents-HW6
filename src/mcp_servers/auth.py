"""Bearer-token auth for the MCP servers, per docs/API.md.

Tokens live in `.env` (`COP_MCP_AUTH_TOKEN` / `THIEF_MCP_AUTH_TOKEN`), never
in code. Revocation (Phase 5) is just removing/rotating the env value and
restarting the server — `StaticTokenVerifier` re-reads it at construction.
"""

import os

from fastmcp.server.auth.providers.jwt import StaticTokenVerifier


def build_verifier(env_var: str, client_id: str) -> StaticTokenVerifier:
    """Build a single-token verifier for one server from an env var.

    Raises if the env var is unset/empty — fail fast rather than silently
    running an unauthenticated server.
    """
    token = os.environ.get(env_var, "")
    if not token:
        raise RuntimeError(
            f"{env_var} is not set — populate it in .env before starting the server"
        )
    return StaticTokenVerifier(tokens={token: {"client_id": client_id, "scopes": []}})
