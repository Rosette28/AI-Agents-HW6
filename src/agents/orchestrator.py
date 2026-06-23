"""Client-side orchestrator: drives the Cop and Thief MCP servers through a
full sub-game / series, via the documented tool contract only.

This is the Phase 2 "wire up the full chain" piece: orchestrator -> decision
-> tool call -> MCP server -> engine update -> result back. Phase 3 plugs in
the real decision step (`src/strategy/`, heuristic by default); the message
text is still a fixed template — Phase 4 swaps in LLM-authored NL messages
and belief updates, on top of this same turn loop.
"""

import random

from fastmcp import Client

from src.agents.policy_stub import compose_message
from src.mcp_servers.cop_server import build_cop_server
from src.mcp_servers.session import GameSession
from src.mcp_servers.thief_server import build_thief_server
from src.strategy.heuristic import heuristic_candidate_actions


async def _act(client: Client, session: GameSession, agent: str, barriers_remaining: int,
                rng: random.Random, policy_fn) -> dict:
    """Try candidate actions via `choose_action` until one is accepted."""
    for action in policy_fn(agent, session.board, barriers_remaining, rng):
        result = await client.call_tool("choose_action", {"action": action})
        if result.data.get("accepted"):
            await client.call_tool("send_message", {"text": compose_message(agent, action)})
            return {"agent": agent, "action": action, "result": result.data}
    return {"agent": agent, "action": None, "result": {"accepted": False, "reason": "no_legal_action"}}


async def run_subgame_via_mcp(grid_size: tuple, max_moves: int, max_barriers: int,
                               cop_pos: tuple, thief_pos: tuple, rng: random.Random,
                               policy_fn=heuristic_candidate_actions) -> dict:
    """Run one full sub-game end to end through the MCP tool-call chain.

    `policy_fn(agent, board, barriers_remaining, rng) -> list[action]`
    defaults to the Phase 3 heuristic; pass `src.strategy.policy
    .build_mcp_candidate_actions("q_learning", q_agents)` to use trained
    Q-tables instead.
    """
    session = GameSession(grid_size, max_moves, max_barriers)
    session.start(cop_pos, thief_pos)
    cop_server = build_cop_server(session)
    thief_server = build_thief_server(session)

    transcript = []
    moves_taken = max_moves
    async with Client(cop_server) as cop_client, Client(thief_server) as thief_client:
        for round_number in range(1, max_moves + 1):
            thief_turn = await _act(thief_client, session, "thief", 0, rng, policy_fn)
            transcript.append(thief_turn)
            if thief_turn["result"].get("captured"):
                moves_taken = round_number
                break

            barriers_remaining = max_barriers - session.board.barriers_placed
            cop_turn = await _act(cop_client, session, "cop", barriers_remaining, rng, policy_fn)
            transcript.append(cop_turn)
            session.advance_round()
            if cop_turn["result"].get("captured"):
                moves_taken = round_number
                break

    winner = "cop" if session.board.is_captured() else "thief"
    return {
        "winner": winner,
        "moves_taken": moves_taken,
        "final_cop_pos": session.board.cop_pos,
        "final_thief_pos": session.board.thief_pos,
        "barriers_placed": session.board.barriers_placed,
        "transcript": transcript,
    }


def _score_subgame(winner: str, scoring: dict) -> tuple[int, int]:
    if winner == "cop":
        return scoring["cop_win"], scoring["thief_loss"]
    return scoring["cop_loss"], scoring["thief_win"]


async def run_series_via_mcp(grid_size: tuple, max_moves: int, num_games: int, max_barriers: int,
                              scoring: dict, start_positions_fn, seed: int | None = None,
                              policy_fn=heuristic_candidate_actions) -> dict:
    """Run a full series of `num_games` sub-games through the MCP chain and
    accumulate totals, mirroring src/engine/game.run_game_series."""
    rng = random.Random(seed)
    cop_total = thief_total = 0
    sub_games = []
    for _ in range(num_games):
        cop_pos, thief_pos = start_positions_fn(grid_size)
        result = await run_subgame_via_mcp(grid_size, max_moves, max_barriers, cop_pos, thief_pos, rng, policy_fn)
        cop_points, thief_points = _score_subgame(result["winner"], scoring)
        result["cop_points"], result["thief_points"] = cop_points, thief_points
        cop_total += cop_points
        thief_total += thief_points
        sub_games.append(result)
    return {"totals": {"cop": cop_total, "thief": thief_total}, "sub_games": sub_games}
