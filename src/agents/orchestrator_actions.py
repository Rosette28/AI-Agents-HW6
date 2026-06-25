"""Per-turn mechanics for the MCP orchestrator: building agent clients,
driving one agent's turn (`_act`), relaying its message to the other
agent's own inbox, and snapshotting state for an `on_turn` callback.

Split out of `src.agents.orchestrator` to keep that module focused on the
sub-game/series control flow; see that module's docstring for the
Phase 2-5 history behind this shape.
"""

import random

from fastmcp import Client

from src.agents.belief import make_belief_board, update_belief
from src.agents.dialogue import choose_deception_level, generate_nl_message
from src.agents.policy_stub import compose_message
from src.engine.board import Board
from src.mcp_servers.cop_server import build_cop_server
from src.mcp_servers.session import AgentSession
from src.mcp_servers.thief_server import build_thief_server


def snapshot(board: Board, move_number: int, beliefs: dict, last_messages: dict) -> dict:
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


async def act(client: Client, true_board: Board, agent: str, barriers_remaining: int,
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
        board_for_policy = make_belief_board(true_board, agent, belief, rng=rng)

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


async def relay_turn(client: Client, agent: str, turn: dict) -> None:
    """Deliver `turn`'s message into the *other* agent's own server inbox —
    the orchestrator's job now that servers never call each other directly.
    """
    text = turn.get("message")
    if text:
        await client.call_tool("receive_message", {"from_agent": agent, "text": text})


def build_agent_client(role: str, grid_size: tuple, max_moves: int, max_barriers: int,
                        visibility_radius: int, endpoint: dict | None) -> Client:
    """`endpoint=None` (default) builds a local, in-process server for this
    sub-game — what every test and the local/dev demo use. Pass
    `endpoint={"url": ..., "token": ...}` to instead connect to an
    already-deployed remote server (e.g. a real cloud-deployed Cop/Thief
    service) — required for a real graded cloud run, since the
    orchestrator itself still runs locally but the servers it drives don't
    have to. Either way, the caller must call `start_subgame` right after
    connecting to (re)initialize that server's session for this sub-game.
    """
    if endpoint:
        return Client(endpoint["url"], auth=endpoint.get("token"))
    session = AgentSession(role, grid_size, max_moves, max_barriers, visibility_radius)
    server = (build_cop_server if role == "cop" else build_thief_server)(session)
    return Client(server)
