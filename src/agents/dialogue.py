"""Natural-language message generation (Phase 4) — replaces the fixed
template in `src/agents/policy_stub.py:compose_message`.

System prompts are the ones drafted in `docs/PROMPTS.md` §2.1/§2.2,
formatted with live config values (grid size, barriers remaining,
visibility radius) — never hardcoded.
"""

import random

from src.agents.belief import Belief
from src.agents.policy_stub import compose_message

Action = dict

_COP_SYSTEM_PROMPT = """You are the COP in a pursuit game on a {grid_size} grid. Your goal is to
land exactly on the THIEF's cell to win. You may move in 8 directions
(N, S, E, W, NE, NW, SE, SW) or place a barrier on your current cell
(you have {barriers_remaining} of {max_barriers} barriers left this
sub-game). A barrier blocks both you and the THIEF from entering that cell
for the rest of this sub-game.

You can only see the THIEF's exact position if it is within
{visibility_radius} cells of you. Otherwise you must infer its location
from what it tells you in natural language — which may be vague, evasive,
or an outright bluff. You may also choose how much to reveal about your
own position and intentions when you message the THIEF; you are not
required to be truthful.

This turn your instructed posture is: {deception_level}.

Never output raw coordinates to the THIEF. Respond with a single short
natural-language message to send the THIEF, and nothing else."""

_THIEF_SYSTEM_PROMPT = """You are the THIEF in a pursuit game on a {grid_size} grid. Your goal is to
survive {max_moves} moves without the COP ever landing exactly on your
cell. You may move in 8 directions (N, S, E, W, NE, NW, SE, SW). You cannot
place barriers, but you must avoid cells the COP has barricaded.

You can only see the COP's exact position if it is within
{visibility_radius} cells of you. Otherwise you must infer its location
from what it tells you in natural language — which may be vague or a
bluff. You may also mislead the COP about your own position or intentions
when you message it.

This turn your instructed posture is: {deception_level}.

Never output raw coordinates to the COP. Respond with a single short
natural-language message to send the COP, and nothing else."""

# Thief bluffs/is vague more often than Cop — an evading party benefits more
# from misdirection than a pursuer does, and gives the assignment's optional
# "deception" requirement a concrete, documented rule instead of a coin flip.
_DECEPTION_WEIGHTS = {
    "cop": [("truthful", 0.65), ("vague", 0.20), ("mislead", 0.15)],
    "thief": [("truthful", 0.30), ("vague", 0.30), ("mislead", 0.40)],
}


def choose_deception_level(agent: str, rng: random.Random) -> str:
    """Weighted pick of "truthful" | "vague" | "mislead" for this turn."""
    levels, weights = zip(*_DECEPTION_WEIGHTS[agent])
    return rng.choices(levels, weights=weights, k=1)[0]


def _system_prompt(agent: str, grid_size: tuple[int, int], barriers_remaining: int,
                    max_barriers: int, max_moves: int, visibility_radius: int,
                    deception_level: str) -> str:
    template = _COP_SYSTEM_PROMPT if agent == "cop" else _THIEF_SYSTEM_PROMPT
    return template.format(
        grid_size=f"{grid_size[0]}x{grid_size[1]}",
        barriers_remaining=barriers_remaining,
        max_barriers=max_barriers,
        max_moves=max_moves,
        visibility_radius=visibility_radius,
        deception_level=deception_level,
    )


def _user_prompt(belief: Belief, intended_action: Action) -> str:
    if intended_action.get("type") == "place_barrier":
        action_desc = "you intend to place a barrier on your current cell"
    else:
        action_desc = f"you intend to move {intended_action.get('direction')}"
    belief_desc = (
        f"your current belief about the opponent: {belief.note} "
        f"(confidence: {belief.confidence})"
    )
    return f"Your situation this turn: {action_desc}. {belief_desc}."


def generate_nl_message(agent: str, belief: Belief, intended_action: Action,
                         deception_level: str, llm_client, grid_size: tuple[int, int],
                         barriers_remaining: int, max_barriers: int, max_moves: int,
                         visibility_radius: int) -> str:
    """Generate the NL message sent to the opponent this turn. Falls back to
    the Phase 2 fixed-template message on any LLM failure — the turn loop
    must never stall waiting on a flaky API call.
    """
    system_prompt = _system_prompt(agent, grid_size, barriers_remaining, max_barriers,
                                    max_moves, visibility_radius, deception_level)
    user_prompt = _user_prompt(belief, intended_action)
    text = llm_client.generate_text(system_prompt, user_prompt)
    if not text:
        return compose_message(agent, intended_action)
    return text
