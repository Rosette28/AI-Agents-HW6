"""Test-only MCP auth tokens — never read from the real .env."""

import pytest


@pytest.fixture(autouse=True)
def mcp_auth_tokens(monkeypatch):
    monkeypatch.setenv("COP_MCP_AUTH_TOKEN", "test-cop-token")
    monkeypatch.setenv("THIEF_MCP_AUTH_TOKEN", "test-thief-token")
