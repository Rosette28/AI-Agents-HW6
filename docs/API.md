# API — MCP Tool Contracts

Both the Cop and Thief MCP servers expose the same tool names; behavior
differs only where the rules differ (e.g. only the Cop server accepts a
`place_barrier` action). This file is the contract reference — implement
exactly this in `src/mcp_servers/` during Phase 2, and update this file if
the contract changes.

## Common

All tool calls require an `Authorization: Bearer <token>` header, validated
against the server's configured token (`.env`). Invalid/revoked tokens
return a 401-equivalent MCP error.

## `read_message() -> Message`

Returns the most recent natural-language message sent by the opponent.

```json
{ "from": "thief", "text": "...", "turn": 4 }
```

## `send_message(text: str) -> Ack`

Relays a natural-language message to the opponent's server.

```json
{ "ok": true, "turn": 4 }
```

## `report_location() -> LocationInternal`

Internal/scoring-only — returns the calling agent's own exact position.
**Must never be used to leak the opponent's position.**

```json
{ "agent": "cop", "position": [2, 3] }
```

## `choose_action(action: Action) -> ActionResult`

Move or (Cop-only) place a barrier. Validated against the game engine.

```json
// request
{ "type": "move", "direction": "NE" }
// or, Cop only:
{ "type": "place_barrier" }
```

```json
// response
{
  "accepted": true,
  "new_position": [3, 3],
  "captured": false,
  "barriers_remaining": 4,
  "moves_remaining": 18
}
```

Rejected actions return `"accepted": false` with a `"reason"` string (e.g.
`"out_of_bounds"`, `"blocked_by_barrier"`, `"no_barriers_remaining"`).

## Error format

```json
{ "error": "invalid_token", "message": "..." }
```
