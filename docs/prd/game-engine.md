# Mini-PRD — Game Engine

## Description / theoretical background

The engine is the authoritative state machine for the board: positions of
Cop and Thief, the set of barrier cells, move count, and turn order. It is
the single source of truth that both MCP servers call into when they
validate and apply a tool-invoked action. It implements no LLM logic and no
networking — pure deterministic game rules, testable in isolation before any
agent or MCP wiring exists (Phase 1, before Phase 2).

## Requirements, inputs/outputs

- **Inputs:** `config.yaml` (`board.grid_size`, `game.max_moves`,
  `game.max_barriers`), and per-turn actions: `move(agent, direction)` where
  direction ∈ {N, S, E, W, NE, NW, SE, SW}, or `place_barrier(cop)`.
- **Outputs:** updated state (positions, barriers, move count), a
  win/loss/ongoing signal, and a rejection reason for illegal actions
  (off-board, into a barrier, exceeding `max_barriers`).
- **Turn order:** Thief moves first, then Cop, repeating until terminal.

## Algorithm

1. On `move`: compute target cell from current position + direction;
   reject if out of bounds or occupied by a barrier; otherwise update
   position.
2. On `place_barrier` (Cop only): mark the Cop's current cell as a barrier
   if `barriers_placed < max_barriers`; otherwise reject.
3. After every Cop move: if Cop's position == Thief's position → Cop wins
   (capture).
4. After `max_moves` turns with no capture → Thief wins (survival).
5. Accumulate score per sub-game per the scoring table; repeat for
   `num_games` sub-games; sum totals.

## Edge cases

- Both agents starting adjacent or on the same cell (should not be
  generated as a start state — validate start-position generation).
- Cop attempts to place a barrier on a cell already containing the Thief —
  decide and document: allowed (barrier coexists, Thief must move next turn
  before barrier "locks" in) or disallowed; pick one and keep it consistent
  with win-condition timing.
- Cop barrier placed on its own current cell — must not trap the Cop itself
  on a 1-D or tiny grid (e.g. 1×2) where it could have no legal moves left;
  define a no-legal-moves fallback (skip turn) and test it explicitly on the
  1×2 sanity-check grid.
- Grid sizes where `visibility_radius` ≥ board diagonal — observation
  becomes effectively full; should still function, just less interesting.

## Success criteria / test scenarios

- Unit tests pass for: legal/illegal movement in all 8 directions, barrier
  blocking for the Thief and the Cop, capture detection, survival detection
  at exactly `max_moves`, barrier cap enforcement, score accumulation across
  6 sub-games matching the scoring table exactly.
- 1×2 grid sanity check produces a deterministic, correct result without
  crashing.
