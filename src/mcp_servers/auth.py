"""Bearer-token auth for the MCP servers, per docs/API.md.

Tokens live in `.env` (`COP_MCP_AUTH_TOKEN` / `THIEF_MCP_AUTH_TOKEN`), never
in code. Revocation (Phase 5) does *not* require restarting the server:
`RevocableTokenVerifier` re-reads the revocation list from disk on every
`verify_token` call, so writing a token into that file is enough to make
the very next request fail.
"""

import json
import os
import time
from pathlib import Path
from typing import Any

from fastmcp.server.auth.auth import AccessToken, TokenVerifier

DEFAULT_REVOCATION_PATH = Path("data/revoked_tokens.json")


def _revocation_path() -> Path:
    return Path(os.environ.get("REVOKED_TOKENS_PATH", DEFAULT_REVOCATION_PATH))


def _read_revoked(path: Path) -> set[str]:
    """Re-read the revocation list fresh every call — no in-memory caching,
    so a revocation written by another process takes effect immediately."""
    if not path.exists():
        return set()
    return set(json.loads(path.read_text() or "[]"))


def revoke_token(token: str, path: Path | None = None) -> None:
    """Add `token` to the on-disk revocation list. Idempotent."""
    path = path or _revocation_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    revoked = _read_revoked(path)
    revoked.add(token)
    path.write_text(json.dumps(sorted(revoked)))


class RevocableTokenVerifier(TokenVerifier):
    """Static token verifier that also checks a revocation list on every
    request, per docs/prd/mcp-servers.md's "revoked token is provably
    rejected" success criterion.
    """

    def __init__(self, tokens: dict[str, dict[str, Any]], revocation_path: Path):
        super().__init__()
        self.tokens = tokens
        self.revocation_path = revocation_path

    async def verify_token(self, token: str) -> AccessToken | None:
        if token in _read_revoked(self.revocation_path):
            return None
        token_data = self.tokens.get(token)
        if not token_data:
            return None
        expires_at = token_data.get("expires_at")
        if expires_at is not None and expires_at < time.time():
            return None
        return AccessToken(
            token=token,
            client_id=token_data.get("client_id", "unknown"),
            scopes=token_data.get("scopes", []),
            expires_at=expires_at,
        )


def build_verifier(env_var: str, client_id: str) -> RevocableTokenVerifier:
    """Build a single-token, revocation-aware verifier for one server from
    an env var.

    Raises if the env var is unset/empty — fail fast rather than silently
    running an unauthenticated server.
    """
    token = os.environ.get(env_var, "")
    if not token:
        raise RuntimeError(
            f"{env_var} is not set — populate it in .env before starting the server"
        )
    return RevocableTokenVerifier(
        tokens={token: {"client_id": client_id, "scopes": []}},
        revocation_path=_revocation_path(),
    )
