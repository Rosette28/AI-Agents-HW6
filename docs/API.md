# API — MCP Tool Contracts

Both the Cop and Thief MCP servers expose the same tool names; behavior
differs only where the rules differ (e.g. only the Cop server accepts a
`place_barrier` action). This file is the contract reference — implement
exactly this in `src/mcp_servers/`, and update this file if the contract
changes.

**Each server owns its own independent session — nothing is shared between
the Cop and Thief servers, including in-process.** That's deliberate: it's
what makes the two servers genuinely independently deployable, including
against a totally separate partner group's server for the Phase 7 bonus.
The orchestrator (`src/agents/orchestrator.py`) is the only thing that
talks to both servers, and is responsible for everything that needs both
agents' true positions — capture detection, visibility checks, relaying
messages between the two servers, and syncing barrier placements — since
neither server can see the other's state on its own.

## Common

All tool calls require an `Authorization: Bearer <token>` header, validated
against the server's configured token (`.env`). Invalid/revoked tokens
return a 401-equivalent MCP error. Revocation is checked fresh on every
request from the on-disk list at `REVOKED_TOKENS_PATH`
(`src/mcp_servers/auth.py:revoke_token`) — no server restart needed for a
revocation to take effect.

## `read_message() -> Message | null`

Returns the most recent natural-language message addressed to this agent,
or `null` if none has arrived yet.

```json
{ "from": "thief", "text": "...", "turn": 4 }
```

## `send_message(text: str) -> Ack`

Records this agent's own outgoing message. **Does not deliver it to the
opponent** — two independently-deployed servers never call each other
directly. Delivery happens when the orchestrator separately calls
`receive_message` on the opponent's own server.

```json
{ "ok": true }
```

## `receive_message(from_agent: str, text: str) -> Ack`

Orchestrator-relayed delivery of the opponent's message into this agent's
own inbox (so a later `read_message` call returns it).

```json
{ "ok": true, "turn": 4 }
```

## `report_location() -> LocationInternal`

Internal/scoring-only — returns the calling agent's own exact position.
**Must never be used to leak the opponent's position.** Only the
orchestrator calls this (on either server) for its own bookkeeping.

```json
{ "agent": "cop", "position": [2, 3] }
```

## `observe_opponent(opponent_position: [int, int] | null = null) -> Observation`

Partial observation (Phase 4): whether `opponent_position` is within
`visibility_radius` (Manhattan distance) of the caller's own position.
**`opponent_position` is supplied by the caller** (the orchestrator, in
real use — it's the only party with legitimate access to both agents' true
positions) since this server has no way to know the opponent's position on
its own. Outside the radius (or with no position supplied) the agent gets
no direct signal and must rely on the NL channel (`read_message`) and its
own belief update.

```json
// within radius
{ "visible": true, "position": [2, 3] }
// outside radius, or opponent_position omitted
{ "visible": false, "position": null }
```

## `sync_barriers(barriers: [[int, int], ...]) -> Ack`

Full, idempotent overwrite of this server's local barrier set. Barriers
block both agents, but only the Cop's own server learns about a new one
directly (from `place_barrier`) — the orchestrator calls this on the
Thief's server right after every successful barrier placement, so the
Thief's own move validation stays correct without any shared memory.

```json
{ "ok": true, "barrier_count": 1 }
```

## `choose_action(action: Action) -> ActionResult`

Move or (Cop-only) place a barrier. Validated against this agent's own
session only.

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
  "barriers_remaining": 4,
  "moves_remaining": 18
}
```

Note there is no `captured` field — this server cannot know the opponent's
position, so it cannot determine capture. Only the orchestrator's own
ground-truth mirror decides that, immediately after this call returns.

Rejected actions return `"accepted": false` with a `"reason"` string (e.g.
`"out_of_bounds"`, `"blocked_by_barrier"`, `"no_barriers_remaining"`,
`"illegal_action_for_agent"`).

## Error format

```json
{ "error": "invalid_token", "message": "..." }
```
