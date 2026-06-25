# Architecture — Deployment Reference

## Cloud deployment (Phase 5)

| Item | Value |
|---|---|
| Cop MCP server URL | `https://cop-mcp-server.onrender.com/mcp` |
| Thief MCP server URL | `https://thief-mcp-server-u04c.onrender.com/mcp` |
| Hosting platform | Render (free tier), two independent web services |
| Auth scheme | Bearer token, per-server, revocable (see `.env.example`) |
| LLM deployment approach | Approach 1 — public cloud API (see `docs/PLAN.md` ADR-1) |

Verified end to end 2026-06-25: both URLs reachable over HTTPS from outside
the deployment network (`scripts/check_cloud_reachability.py`), and a real
6-sub-game LLM-driven series was played against them via
`src.agents.orchestrator`'s remote-endpoint mode (`cop_endpoint`/
`thief_endpoint`), confirming session isolation/reset between sub-games on
the live deployment. Render's free tier sleeps after ~15 min idle; expect
a ~30-50s cold-start delay on the first request after idle.

## Security notes

- Tokens are generated per deployment, stored only in `.env`, never
  committed. Revocation = rotate/remove the token server-side.
- Both MCP servers must be reachable over HTTPS from the public internet;
  do not test from a network that blocks non-standard ports.

## Bonus inter-group deployment (Phase 7, if pursued)

| Item | Value |
|---|---|
| Partner group | TBD |
| Partner Cop MCP URL | TBD |
| Partner Thief MCP URL | TBD |

For the full system/container diagrams, see `docs/PLAN.md`.
