# Mini-PRD — MCP Servers

## Description / theoretical background

Two independent FastMCP servers — one for the Cop, one for the Thief — each
exposing the same tool contract but scoped to their own agent's permissions
(e.g. only the Cop's server allows a barrier-placement tool call). The LLM
never runs inside these servers; they are a thin, auditable boundary between
an agent's orchestrator (Client) and the shared game engine.

## Requirements, inputs/outputs

- **Tools exposed by each server** (documented fully in `docs/API.md` once
  implemented):
  - `read_message()` — returns the latest NL message from the opponent.
  - `send_message(text: str)` — relays an NL message to the opponent's
    server.
  - `report_location()` — internal/scoring-only; never exposes the
    opponent's exact position to the calling agent.
  - `choose_action(action: dict)` — move or (Cop-only) place_barrier;
    validated against the engine and applied.
- **Auth:** every tool call requires a bearer token (`config.yaml: mcp.*`,
  actual secret in `.env`); invalid/revoked tokens are rejected with a clear
  error.

## Algorithm / flow

Client → LLM (decides tool + args) → Client calls MCP tool over HTTPS →
server validates token → server validates the action against engine state →
server applies it / rejects it → server returns a structured result → Client
feeds the result back to the LLM for the next decision.

## Constraints and limitations, alternatives considered

- **Constraint:** the two servers must not directly call each other's
  internal engine state — message relay must go through each Client, so the
  NL channel is the only coupling, preserving the partial-observability
  requirement.
- **Alternative considered:** a single shared MCP server for both agents —
  rejected, since the assignment explicitly requires two independent
  servers (this also lets each be deployed/secured/revoked separately).

## Edge cases

- Opponent's server is unreachable mid-sub-game → counts as a technical
  loss for that sub-game (re-run, per requirements §11).
- Token revoked mid-series → all subsequent tool calls fail cleanly with an
  auth error, not a silent state corruption.
- Malformed `choose_action` payload (e.g. invalid direction string) →
  rejected with a descriptive error, not a crash.

## Success criteria / test scenarios

- Local ping/echo tool call succeeds between both servers before any game
  logic is wired in.
- A revoked token is provably rejected (test asserts 401/error response).
- End-to-end pipeline sanity check on the 1×2 grid: a dummy message travels
  Client → tool call → server → response, and is logged correctly.
