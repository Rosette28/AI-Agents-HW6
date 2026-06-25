"""Phase 7 bonus inter-group competition ONLY — not part of the mandatory
submission. Replaces the earlier (flawed) design where one side's
orchestrator drove BOTH agents' decisions, which never actually exercised
the partner group's own strategy/LLM at all — see
`docs/prd/bonus-inter-group.md` for the full story.

Here, **each group runs its own copy of this module**, each one deciding
only its own agent's moves (its own strategy, its own LLM) and submitting
them only to its own server. The two independent processes stay in sync
via tools every compliant server already exposes: `report_location`
(learn the opponent's true position — legitimate here, since this is the
scoring/coordination layer, not a leak into the NL channel) and the
existing message relay (a new message arriving is this design's "the
opponent just moved" signal, since every turn sends one).

Both sides independently observe the same shared reality (the real
network calls hitting both real servers), so both arrive at the same
result on their own — no result needs to be "shared" for either side to
trust it, only compared before either one is sent.

Low-level helpers shared with `src.agents.bonus_peer_subgame` (split out
purely to stay under the 150-line file limit — both modules are one
logical unit).
"""

import asyncio
import random

from fastmcp import Client

from src.agents.belief import make_belief_board, update_belief
from src.agents.dialogue import choose_deception_level, generate_nl_message
from src.engine.board import Board
from src.strategy.heuristic import heuristic_candidate_actions, manhattan_distance

POLL_INTERVAL_SECONDS = 2.0
MAX_WAIT_SECONDS = 300.0


def client(endpoint: dict) -> Client:
    return Client(endpoint["url"], auth=endpoint.get("token"))


async def wait_for_opponent_move(mcp_client: Client, last_seen: dict | None) -> dict:
    """Poll `read_message` until a message different from `last_seen`
    arrives — every turn sends one, so a new one is the signal the
    opponent has moved this round. Raises on timeout; the caller treats
    that as a technical loss for this sub-game, same spirit as
    `docs/prd/email-reporting.md`'s Technical Loss handling.
    """
    waited = 0.0
    while waited < MAX_WAIT_SECONDS:
        message = (await mcp_client.call_tool("read_message")).data
        if message and message != last_seen:
            return message
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
        waited += POLL_INTERVAL_SECONDS
    raise RuntimeError("Timed out waiting for the opponent's move (Phase 7 bonus peer protocol) "
                        "— check the partner's server is reachable and running its own side of this.")


async def positions(my_client: Client, partner_client: Client) -> tuple[tuple, tuple]:
    my_pos = tuple((await my_client.call_tool("report_location")).data["position"])
    partner_pos = tuple((await partner_client.call_tool("report_location")).data["position"])
    return my_pos, partner_pos


async def act(my_role: str, my_client: Client, partner_client: Client, llm_client,
               grid_size: tuple, max_moves: int, max_barriers: int, visibility_radius: int,
               belief, last_opponent_message: dict | None, barriers_remaining: int,
               my_barriers: list, rng: random.Random):
    """Decide and submit our own move/message for this turn. Returns
    (accepted_action, message_text, updated_my_barriers, updated_belief)."""
    my_pos, partner_pos = await positions(my_client, partner_client)
    visible = manhattan_distance(my_pos, partner_pos) <= visibility_radius
    direct_observation = {"visible": visible, "position": list(partner_pos) if visible else None}
    opponent_message = {"text": last_opponent_message["text"]} if last_opponent_message else None
    belief = update_belief(my_role, opponent_message, direct_observation, llm_client,
                            previous_belief=belief, moves_elapsed=1)

    true_board = Board(grid_size, max_barriers)
    true_board.cop_pos = my_pos if my_role == "cop" else partner_pos
    true_board.thief_pos = partner_pos if my_role == "cop" else my_pos
    true_board.barriers = {tuple(b) for b in my_barriers}
    board_for_policy = make_belief_board(true_board, my_role, belief)

    action, result = None, None
    for candidate in heuristic_candidate_actions(my_role, board_for_policy, barriers_remaining, rng):
        result = (await my_client.call_tool("choose_action", {"action": candidate})).data
        if result.get("accepted"):
            action = candidate
            break
    if action is None:
        raise RuntimeError(f"{my_role} has no legal action this turn (Phase 7 bonus peer protocol)")

    if action["type"] == "place_barrier":
        my_barriers = my_barriers + [list(my_pos)]
        await partner_client.call_tool("sync_barriers", {"barriers": my_barriers})

    deception = choose_deception_level(my_role, rng)
    text = generate_nl_message(my_role, belief, action, deception, llm_client, grid_size,
                                barriers_remaining, max_barriers, max_moves, visibility_radius)
    await my_client.call_tool("send_message", {"text": text})
    await partner_client.call_tool("receive_message", {"from_agent": my_role, "text": text})
    return action, text, my_barriers, belief
