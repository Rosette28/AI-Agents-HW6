"""Client-side orchestrator: drives the Cop and Thief MCP servers through a
full sub-game / series, via the documented tool contract only.

Phase 2 wired the mechanical chain (decision -> tool call -> MCP server ->
engine update -> result back) with a fixed-template message. Phase 4 added
the real loop: read the opponent's message, observe it directly if within
visibility radius, update a belief, decide via the existing strategy module
against a belief-board proxy (never the true opponent position), then
generate a free-NL message with the LLM.

Phase 5 removed the last piece of shared state between the two servers:
each MCP server now owns its own independent `AgentSession` (own position,
own barrier set, own inbox) with nothing shared between them — required so
the two servers are genuinely independently deployable, including against
a totally separate partner group's server for the Phase 7 bonus. This
orchestrator is now the *only* thing that ever sees both agents' true
positions: it keeps its own ground-truth `Board` mirror (updated from each
server's *own* validated response, never read from server-side state
directly), and is responsible for everything that needs both positions —
capture detection, visibility checks, message relay, and barrier
synchronization — since the servers can no longer do any of that
themselves.

Passing `llm_client=None` (the default) keeps the exact Phase 2/3 behavior
for callers that don't need it (e.g. existing sanity-progression
scripts/tests).
"""

import random

from fastmcp import Client

from src.agents.belief import Belief, make_belief_board, update_belief
from src.agents.dialogue import choose_deception_level, generate_nl_message
from src.agents.policy_stub import compose_message
from src.engine.board import Board
from src.mcp_servers.cop_server import build_cop_server
from src.mcp_servers.session import AgentSession
from src.mcp_servers.thief_server import build_thief_server
from src.strategy.heuristic import heuristic_candidate_actions


def _snapshot(board: Board, move_number: int, beliefs: dict, last_messages: dict) -> dict:
    """Plain-dict state snapshot for an optional `on_turn` callback (e.g. the
    GUI state writer) — orchestrator never imports src.gui itself, per the
    module-dependency rules in docs/PROMPTS.md.
    """
    return {
        "rows": board.rows, "cols": board.cols,
        "cop_pos": list(board.cop_pos), "thief_pos": list(board.thief_pos),
        "barriers": [list(b) for b in board.barriers],
        "barriers_placed": board.barriers_placed,
        "move_number": move_number,
        "beliefs": {
            agent: {"estimate": list(b.estimate) if b.estimate else None,
                    "confidence": b.confidence, "note": b.note}
            for agent, b in beliefs.items()
        },
        "last_messages": dict(last_messages),
    }


async def _act(client: Client, true_board: Board, agent: str, barriers_remaining: int,
                rng: random.Random, policy_fn, llm_client=None, beliefs: dict | None = None,
                grid_size: tuple | None = None, max_barriers: int = 0, max_moves: int = 0,
                visibility_radius: int = 2) -> dict:
    """Try candidate actions via `choose_action` until one is accepted.

    `true_board` is the orchestrator's own ground-truth mirror — the only
    place both agents' true positions exist. On an accepted action, this
    applies it to `true_board` itself (the corresponding server has already
    validated/applied the same action against its own independent session,
    so re-applying it to the mirror is safe — both started from, and stay
    in, the same state by construction).
    """
    belief = None
    own_pos = true_board.cop_pos if agent == "cop" else true_board.thief_pos
    opponent_pos = true_board.thief_pos if agent == "cop" else true_board.cop_pos
    board_for_policy = true_board

    if llm_client is not None:
        opponent_message = (await client.call_tool("read_message")).data
        direct_observation = (
            await client.call_tool("observe_opponent", {"opponent_position": list(opponent_pos)})
        ).data
        belief = update_belief(agent, opponent_message, direct_observation, llm_client)
        beliefs[agent] = belief
        board_for_policy = make_belief_board(true_board, agent, belief)

    for action in policy_fn(agent, board_for_policy, barriers_remaining, rng):
        result = await client.call_tool("choose_action", {"action": action})
        if result.data.get("accepted"):
            captured = False
            if action["type"] == "move":
                captured = true_board.move(agent, action["direction"]).get("captured", False)
            elif action["type"] == "place_barrier":
                true_board.place_barrier()

            if llm_client is not None:
                deception_level = choose_deception_level(agent, rng)
                text = generate_nl_message(
                    agent, belief, action, deception_level, llm_client, grid_size,
                    barriers_remaining, max_barriers, max_moves, visibility_radius,
                )
            else:
                text = compose_message(agent, action)
            await client.call_tool("send_message", {"text": text})
            turn = {"agent": agent, "action": action, "result": result.data, "message": text,
                    "captured": captured}
            if belief is not None:
                turn["belief"] = {"estimate": belief.estimate, "confidence": belief.confidence,
                                   "note": belief.note}
            return turn
    return {"agent": agent, "action": None, "result": {"accepted": False, "reason": "no_legal_action"},
            "captured": False}


async def _relay_turn(client: Client, agent: str, turn: dict) -> None:
    """Deliver `turn`'s message into the *other* agent's own server inbox —
    the orchestrator's job now that servers never call each other directly.
    """
    text = turn.get("message")
    if text:
        await client.call_tool("receive_message", {"from_agent": agent, "text": text})


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
    true_board = Board(grid_size, max_barriers)
    true_board.set_start_positions(cop_pos, thief_pos)

    cop_session = AgentSession("cop", grid_size, max_moves, max_barriers, visibility_radius)
    cop_session.start(cop_pos)
    thief_session = AgentSession("thief", grid_size, max_moves, 0, visibility_radius)
    thief_session.start(thief_pos)

    cop_server = build_cop_server(cop_session)
    thief_server = build_thief_server(thief_session)

    beliefs: dict[str, Belief] = {}
    last_messages: dict[str, str] = {}
    transcript = []
    moves_taken = max_moves
    async with Client(cop_server) as cop_client, Client(thief_server) as thief_client:
        for round_number in range(1, max_moves + 1):
            thief_turn = await _act(thief_client, true_board, "thief", 0, rng, policy_fn,
                                     llm_client, beliefs, grid_size, max_barriers, max_moves,
                                     visibility_radius)
            transcript.append(thief_turn)
            last_messages["thief"] = thief_turn.get("message", "")
            await _relay_turn(cop_client, "thief", thief_turn)
            if on_turn:
                on_turn(_snapshot(true_board, round_number, beliefs, last_messages))
            if thief_turn.get("captured"):
                moves_taken = round_number
                break

            barriers_remaining = max_barriers - true_board.barriers_placed
            cop_turn = await _act(cop_client, true_board, "cop", barriers_remaining, rng, policy_fn,
                                   llm_client, beliefs, grid_size, max_barriers, max_moves,
                                   visibility_radius)
            transcript.append(cop_turn)
            last_messages["cop"] = cop_turn.get("message", "")
            await _relay_turn(thief_client, "cop", cop_turn)
            if cop_turn.get("action", {}) and cop_turn["action"].get("type") == "place_barrier" \
                    and cop_turn["result"].get("accepted"):
                await thief_client.call_tool("sync_barriers", {"barriers": [list(b) for b in true_board.barriers]})
            if on_turn:
                on_turn(_snapshot(true_board, round_number, beliefs, last_messages))
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


def _score_subgame(winner: str, scoring: dict) -> tuple[int, int]:
    if winner == "cop":
        return scoring["cop_win"], scoring["thief_loss"]
    return scoring["cop_loss"], scoring["thief_win"]


async def _run_subgame_with_technical_loss_retry(
    grid_size, max_moves, max_barriers, cop_pos, thief_pos, rng, policy_fn, llm_client,
    visibility_radius, on_turn, max_retries: int, technical_losses: list, subgame_index: int,
) -> dict:
    """Per docs/prd/email-reporting.md's Technical Loss handling: any
    exception out of `run_subgame_via_mcp` (MCP server unreachable,
    malformed tool response, etc. — a normal game outcome never raises,
    see `_act`'s structured "no_legal_action" return) voids that attempt
    and retries the *same* sub-game, up to `max_retries` times, so the
    series still ends with exactly `num_games` valid sub-games.
    """
    for attempt in range(1, max_retries + 2):
        try:
            return await run_subgame_via_mcp(grid_size, max_moves, max_barriers, cop_pos, thief_pos,
                                              rng, policy_fn, llm_client, visibility_radius, on_turn)
        except Exception as exc:
            technical_losses.append({"sub_game_index": subgame_index, "attempt": attempt, "reason": str(exc)})
            if attempt > max_retries:
                raise RuntimeError(
                    f"sub-game {subgame_index} hit a technical failure {attempt} times in a row — giving up"
                ) from exc


async def run_series_via_mcp(grid_size: tuple, max_moves: int, num_games: int, max_barriers: int,
                              scoring: dict, start_positions_fn, seed: int | None = None,
                              policy_fn=heuristic_candidate_actions, llm_client=None,
                              visibility_radius: int = 2, on_turn=None,
                              max_technical_retries: int = 2) -> dict:
    """Run a full series of `num_games` sub-games through the MCP chain and
    accumulate totals, mirroring src/engine/game.run_game_series. A
    technical failure mid-sub-game is voided and retried in place (see
    `_run_subgame_with_technical_loss_retry`) rather than corrupting or
    truncating the series; `technical_losses` in the return value logs any
    such retries for grading evidence.
    """
    rng = random.Random(seed)
    cop_total = thief_total = 0
    sub_games = []
    technical_losses: list[dict] = []
    for index in range(1, num_games + 1):
        cop_pos, thief_pos = start_positions_fn(grid_size)
        result = await _run_subgame_with_technical_loss_retry(
            grid_size, max_moves, max_barriers, cop_pos, thief_pos, rng, policy_fn, llm_client,
            visibility_radius, on_turn, max_technical_retries, technical_losses, index,
        )
        cop_points, thief_points = _score_subgame(result["winner"], scoring)
        result["cop_points"], result["thief_points"] = cop_points, thief_points
        cop_total += cop_points
        thief_total += thief_points
        sub_games.append(result)
    return {
        "totals": {"cop": cop_total, "thief": thief_total},
        "sub_games": sub_games,
        "technical_losses": technical_losses,
    }
