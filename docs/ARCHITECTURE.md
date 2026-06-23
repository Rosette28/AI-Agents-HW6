# Architecture — Deployment Reference

## Cloud deployment (Phase 5)

| Item | Value |
|---|---|
| Cop MCP server URL | _not yet deployed_ |
| Thief MCP server URL | _not yet deployed_ |
| Hosting platform | TBD (e.g. Prefect Cloud or equivalent) |
| Auth scheme | Bearer token, per-server, revocable (see `.env.example`) |
| LLM deployment approach | Approach 1 — public cloud API (see `docs/PLAN.md` ADR-1) |

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
