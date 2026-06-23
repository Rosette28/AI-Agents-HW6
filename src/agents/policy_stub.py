"""Placeholder decision/message logic from the Phase 2 pipeline sanity check.

`candidate_actions` is no longer the orchestrator's default (Phase 3
replaced it with `src/strategy/heuristic.py`'s heuristic_candidate_actions
as the default `policy_fn`) but stays here as a uniformly-random baseline —
useful for A/B comparison against the heuristic/Q-learning policies, e.g.
in the Phase 3 sanity-progression notes.

`compose_message` is still the live placeholder for the NL message; Phase 4
replaces it with LLM-authored text.
"""

import random

Action = dict

_DIRECTIONS = ["N", "S", "E", "W", "NE", "NW", "SE", "SW"]


def candidate_actions(agent: str, barriers_remaining: int, rng: random.Random) -> list[Action]:
    """Shuffled list of actions to try via `choose_action`, in order, until
    one is accepted by the engine.

    The orchestrator has no tool for discovering legal moves up front (the
    documented contract in docs/API.md only validates after the fact), so
    this placeholder policy tries directions in random order and lets the
    MCP server's `accepted: false` responses prune illegal ones.
    """
    moves = [{"type": "move", "direction": d} for d in _DIRECTIONS]
    rng.shuffle(moves)
    if agent == "cop" and barriers_remaining > 0 and rng.random() < 0.1:
        moves.insert(0, {"type": "place_barrier"})
    return moves


def compose_message(agent: str, action: Action) -> str:
    """Fixed-template placeholder for the NL message Phase 4 will generate."""
    if action["type"] == "place_barrier":
        return f"{agent} placed a barrier."
    return f"{agent} moved {action['direction']}."
