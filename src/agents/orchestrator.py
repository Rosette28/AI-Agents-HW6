"""Client-side orchestrator: drives the Cop and Thief MCP servers through a
full sub-game / series, via the documented tool contract only.

Each MCP server owns its own independent `AgentSession` (own position, own
barrier set, own inbox) with nothing shared between them — required so the
two servers are genuinely independently deployable, including against a
totally separate partner group's server for the Phase 7 bonus. This
orchestrator is the *only* thing that ever sees both agents' true
positions: it keeps its own ground-truth `Board` mirror (updated from each
server's *own* validated response, never read from server-side state
directly), and is responsible for everything that needs both positions —
capture detection, visibility checks, message relay, and barrier
synchronization — since the servers can no longer do any of that
themselves.

Passing `llm_client=None` (the default) keeps the fixed-template behavior
for callers that don't need it (e.g. existing sanity-progression
scripts/tests).

`cop_endpoint`/`thief_endpoint` (default `None`) let this same orchestrator
drive either local in-process servers or an already-deployed remote
server — see `orchestrator_actions.build_agent_client`. A real graded
cloud run needs the remote form; everything else in this module is
identical either way.

Per-turn mechanics (building agent clients, driving one agent's turn,
relaying messages, snapshotting state) live in `src.agents.orchestrator_actions`.
Series-level control flow (scoring, technical-loss retry, totals) lives in
`src.agents.orchestrator_series`; `run_series_via_mcp` is re-exported below
so it keeps the same import path.
"""

import random

from src.agents.belief import Belief
from src.agents.orchestrator_actions import act, build_agent_client, relay_turn, snapshot
from src.engine.board import Board
from src.strategy.heuristic import heuristic_candidate_actions


async def run_subgame_via_mcp(grid_size: tuple, max_moves: int, max_barriers: int,
                               cop_pos: tuple, thief_pos: tuple, rng: random.Random,
                               policy_fn=heuristic_candidate_actions, llm_client=None,
                               visibility_radius: int = 2, on_turn=None,
                               cop_endpoint: dict | None = None,
                               thief_endpoint: dict | None = None) -> dict:
    """Run one full sub-game end to end through the MCP tool-call chain.

    `policy_fn(agent, board, barriers_remaining, rng) -> list[action]`
    defaults to the Phase 3 heuristic; pass `src.strategy.policy
    .build_mcp_candidate_actions("q_learning", q_agents)` to use trained
    Q-tables instead. `llm_client` (an `src.agents.llm_client.LLMClient`)
    enables the belief-update + LLM-authored NL message pipeline; `None`
    keeps the fixed-template behavior. `on_turn(snapshot)`, if given, is
    called after every turn with a plain-dict state snapshot (used by the
    GUI state writer). `cop_endpoint`/`thief_endpoint` default to `None`
    (local in-process servers); pass `{"url": ..., "token": ...}` for
    either to play against an already-deployed remote server instead.
    """
    true_board = Board(grid_size, max_barriers)
    true_board.set_start_positions(cop_pos, thief_pos)

    cop_client_cm = build_agent_client("cop", grid_size, max_moves, max_barriers,
                                        visibility_radius, cop_endpoint)
    thief_client_cm = build_agent_client("thief", grid_size, max_moves, 0,
                                          visibility_radius, thief_endpoint)

    beliefs: dict[str, Belief] = {}
    last_messages: dict[str, str] = {}
    transcript = []
    moves_taken = max_moves
    async with cop_client_cm as cop_client, thief_client_cm as thief_client:
        await cop_client.call_tool("start_subgame", {"position": list(cop_pos)})
        await thief_client.call_tool("start_subgame", {"position": list(thief_pos)})
        for round_number in range(1, max_moves + 1):
            thief_turn = await act(thief_client, true_board, "thief", 0, rng, policy_fn,
                                    llm_client, beliefs, grid_size, max_barriers, max_moves,
                                    visibility_radius)
            transcript.append(thief_turn)
            last_messages["thief"] = thief_turn.get("message", "")
            await relay_turn(cop_client, "thief", thief_turn)
            if on_turn:
                on_turn(snapshot(true_board, round_number, beliefs, last_messages))
            if thief_turn.get("captured"):
                moves_taken = round_number
                break

            barriers_remaining = max_barriers - true_board.barriers_placed
            cop_turn = await act(cop_client, true_board, "cop", barriers_remaining, rng, policy_fn,
                                  llm_client, beliefs, grid_size, max_barriers, max_moves,
                                  visibility_radius)
            transcript.append(cop_turn)
            last_messages["cop"] = cop_turn.get("message", "")
            await relay_turn(thief_client, "cop", cop_turn)
            if cop_turn.get("action", {}) and cop_turn["action"].get("type") == "place_barrier" \
                    and cop_turn["result"].get("accepted"):
                await thief_client.call_tool("sync_barriers", {"barriers": [list(b) for b in true_board.barriers]})
            if on_turn:
                on_turn(snapshot(true_board, round_number, beliefs, last_messages))
            if cop_turn.get("captured"):
                moves_taken = round_number
                break

    winner = "cop" if true_board.is_captured() else "thief"
    return {
        "winner": winner,
        "moves_taken": moves_taken,
        "final_cop_pos": true_board.cop_pos,
        "final_thief_pos": true_board.thief_pos,
        "barriers_placed": true_board.barriers_placed,
        "transcript": transcript,
    }


from src.agents.orchestrator_series import run_series_via_mcp  # noqa: E402
