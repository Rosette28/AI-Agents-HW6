"""Placeholder decision/message logic for the Phase 2 pipeline sanity check.

This stands in for two things that arrive in later phases:
  - the LLM tool-call decision (Phase 3 adds real strategy: heuristics /
    Q-learning; Phase 4 lets the LLM itself choose the tool call)
  - free natural-language message generation (Phase 4 replaces the fixed
    template below with LLM-authored text)

Keeping this isolated in one small module makes both swaps a one-file
change in `src/agents/orchestrator.py` later, instead of a rewrite.
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
