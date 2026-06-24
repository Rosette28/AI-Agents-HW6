"""Client-side orchestrator: drives the Cop and Thief MCP servers through a
full sub-game / series, via the documented tool contract only.

Phase 2 wired the mechanical chain (decision -> tool call -> MCP server ->
engine update -> result back) with a fixed-template message. Phase 4 adds
the real loop: read the opponent's message, observe it directly if within
visibility radius, update a belief, decide via the existing strategy module
against a belief-board proxy (never the true opponent position), then
generate a free-NL message with the LLM. Passing `llm_client=None` (the
default) keeps the exact Phase 2/3 behavior for callers that don't need it
(e.g. existing sanity-progression scripts/tests).
"""

import random

from fastmcp import Client

from src.agents.belief import Belief, make_belief_board, update_belief
from src.agents.dialogue import choose_deception_level, generate_nl_message
from src.agents.policy_stub import compose_message
from src.mcp_servers.cop_server import build_cop_server
from src.mcp_servers.session import GameSession
from src.mcp_servers.thief_server import build_thief_server
from src.strategy.heuristic import heuristic_candidate_actions


def _snapshot(session: GameSession, beliefs: dict, last_messages: dict) -> dict:
    """Plain-dict state snapshot for an optional `on_turn` callback (e.g. the
    GUI state writer) — orchestrator never imports src.gui itself, per the
    module-dependency rules in docs/PROMPTS.md.
    """
    board = session.board
    return {
        "rows": board.rows, "cols": board.cols,
        "cop_pos": list(board.cop_pos), "thief_pos": list(board.thief_pos),
        "barriers": [list(b) for b in board.barriers],
        "barriers_placed": board.barriers_placed,
        "move_number": session.move_number,
        "beliefs": {
            agent: {"estimate": list(b.estimate) if b.estimate else None,
                    "confidence": b.confidence, "note": b.note}
            for agent, b in beliefs.items()
        },
        "last_messages": dict(last_messages),
    }


async def _act(client: Client, session: GameSession, agent: str, barriers_remaining: int,
                rng: random.Random, policy_fn, llm_client=None, beliefs: dict | None = None,
                grid_size: tuple | None = None, max_barriers: int = 0, max_moves: int = 0,
                visibility_radius: int = 2) -> dict:
    """Try candidate actions via `choose_action` until one is accepted."""
    belief = None
    board_for_policy = session.board

    if llm_client is not None:
        opponent_message = (await client.call_tool("read_message")).data
        direct_observation = (await client.call_tool("observe_opponent")).data
        belief = update_belief(agent, opponent_message, direct_observation, llm_client)
        beliefs[agent] = belief
        board_for_policy = make_belief_board(session.board, agent, belief)

    for action in policy_fn(agent, board_for_policy, barriers_remaining, rng):
        result = await client.call_tool("choose_action", {"action": action})
        if result.data.get("accepted"):
            if llm_client is not None:
                deception_level = choose_deception_level(agent, rng)
                text = generate_nl_message(
                    agent, belief, action, deception_level, llm_client, grid_size,
                    barriers_remaining, max_barriers, max_moves, visibility_radius,
                )
            else:
                text = compose_message(agent, action)
            await client.call_tool("send_message", {"text": text})
            turn = {"agent": agent, "action": action, "result": result.data, "message": text}
            if belief is not None:
                turn["belief"] = {"estimate": belief.estimate, "confidence": belief.confidence,
                                   "note": belief.note}
            return turn
    return {"agent": agent, "action": None, "result": {"accepted": False, "reason": "no_legal_action"}}


async def run_subgame_via_mcp(grid_size: tuple, max_moves: int, max_barriers: int,
                               cop_pos: tuple, thief_pos: tuple, rng: random.Random,
                               policy_fn=heuristic_candidate_actions, llm_client=None,
                               visibility_radius: int = 2, on_turn=None) -> dict:
    """Run one full sub-game end to end through the MCP tool-call chain.

    `policy_fn(agent, board, barriers_remaining, rng) -> list[action]`
    defaults to the Phase 3 heuristic; pass `src.strategy.policy
    .build_mcp_candidate_actions("q_learning", q_agents)` to use trained
    Q-tables instead. `llm_client` (an `src.agents.llm_client.LLMClient`)
    enables the Phase 4 belief-update + LLM-authored NL message pipeline;
    `None` keeps the Phase 2/3 fixed-template behavior. `on_turn(snapshot)`,
    if given, is called after every turn with a plain-dict state snapshot
    (used by the GUI state writer).
    """
    session = GameSession(grid_size, max_moves, max_barriers, visibility_radius)
    session.start(cop_pos, thief_pos)
    cop_server = build_cop_server(session)
    thief_server = build_thief_server(session)

    beliefs: dict[str, Belief] = {}
    last_messages: dict[str, str] = {}
    transcript = []
    moves_taken = max_moves
    async with Client(cop_server) as cop_client, Client(thief_server) as thief_client:
        for round_number in range(1, max_moves + 1):
            thief_turn = await _act(thief_client, session, "thief", 0, rng, policy_fn,
                                     llm_client, beliefs, grid_size, max_barriers, max_moves,
                                     visibility_radius)
            transcript.append(thief_turn)
            last_messages["thief"] = thief_turn.get("message", "")
            if on_turn:
                on_turn(_snapshot(session, beliefs, last_messages))
            if thief_turn["result"].get("captured"):
                moves_taken = round_number
                break

            barriers_remaining = max_barriers - session.board.barriers_placed
            cop_turn = await _act(cop_client, session, "cop", barriers_remaining, rng, policy_fn,
                                   llm_client, beliefs, grid_size, max_barriers, max_moves,
                                   visibility_radius)
            transcript.append(cop_turn)
            last_messages["cop"] = cop_turn.get("message", "")
            session.advance_round()
            if on_turn:
                on_turn(_snapshot(session, beliefs, last_messages))
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
                              policy_fn=heuristic_candidate_actions, llm_client=None,
                              visibility_radius: int = 2, on_turn=None) -> dict:
    """Run a full series of `num_games` sub-games through the MCP chain and
    accumulate totals, mirroring src/engine/game.run_game_series."""
    rng = random.Random(seed)
    cop_total = thief_total = 0
    sub_games = []
    for _ in range(num_games):
        cop_pos, thief_pos = start_positions_fn(grid_size)
        result = await run_subgame_via_mcp(grid_size, max_moves, max_barriers, cop_pos, thief_pos,
                                            rng, policy_fn, llm_client, visibility_radius, on_turn)
        cop_points, thief_points = _score_subgame(result["winner"], scoring)
        result["cop_points"], result["thief_points"] = cop_points, thief_points
        cop_total += cop_points
        thief_total += thief_points
        sub_games.append(result)
    return {"totals": {"cop": cop_total, "thief": thief_total}, "sub_games": sub_games}
