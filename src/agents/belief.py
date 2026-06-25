"""Belief update under partial observability (Phase 4).

Direct observation (via the `observe_opponent` MCP tool, within
`visibility_radius`) always overrides whatever the opponent's natural-
language message implied — bluffing is only detectable because of this
priority order. Outside the visibility radius, the only signal is an LLM
parse of the opponent's free-text message, with "no reliable information"
as an explicit, valid outcome (docs/prd/nl-dialogue.md).
"""

from dataclasses import dataclass

from src.engine.board import Board

Position = tuple[int, int]


@dataclass
class Belief:
    """One agent's current estimate of the opponent's position.

    `estimate` is None when there is genuinely no information yet (game
    start, no message received, never in visibility radius).
    """

    estimate: Position | None
    confidence: str  # "high" | "low" | "none"
    note: str


def _parse_nl_belief(agent: str, opponent_message: dict | None, llm_client) -> dict | None:
    """Ask the LLM to extract a positional/intent signal from the
    opponent's latest message. Returns None on API failure or malformed
    output — both degrade to "no new information" for the caller.
    """
    if opponent_message is None:
        return None
    system_prompt = (
        f"You are the {agent.upper()}'s belief-tracking assistant in a pursuit "
        "game. Extract any signal about the opponent's likely position or "
        "intentions from its message. Respond with JSON only: "
        '{"row": int or null, "col": int or null, "confidence": "high"|"low"|"none", '
        '"note": "short reasoning"}. Use null row/col and confidence "none" if the '
        "message gives no reliable information — do not guess."
    )
    user_prompt = f'Opponent\'s latest message: "{opponent_message["text"]}"'
    return llm_client.generate_json(system_prompt, user_prompt)


def _chebyshev_distance(a: Position, b: Position) -> int:
    """Max single-step reach per move is 1 cell (8-directional movement),
    so Chebyshev (not Manhattan) distance is the right "how far could they
    plausibly have gotten" measure.
    """
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def update_belief(agent: str, opponent_message: dict | None,
                   direct_observation: dict, llm_client,
                   previous_belief: "Belief | None" = None,
                   moves_elapsed: int = 1) -> Belief:
    """Merge the NL-derived estimate with the direct observation.

    `direct_observation` is the raw `observe_opponent` tool response:
    `{"visible": bool, "position": [r, c] | None}`.

    `previous_belief`/`moves_elapsed` add a physical-plausibility check on
    the NL-parsed estimate: the opponent can move at most one cell per turn
    (8-directional), so a new estimate that's farther than `moves_elapsed`
    cells from the last known estimate is physically impossible — either
    the LLM misparsed the message, or the opponent is lying. Either way,
    that claim shouldn't be trusted at face value; its confidence is capped
    at "low" with a flagged note, rather than rejected outright (it might
    still carry a *direction* worth weighting) or accepted as "high" (which
    would let a bluffing opponent dictate the believer's confidence).
    """
    if direct_observation.get("visible"):
        pos = direct_observation["position"]
        return Belief(estimate=(pos[0], pos[1]), confidence="high",
                      note="direct observation within visibility radius")

    parsed = _parse_nl_belief(agent, opponent_message, llm_client)
    if not parsed or parsed.get("row") is None or parsed.get("col") is None:
        note = "no reliable information from message or observation"
        return Belief(estimate=None, confidence="none", note=note)

    estimate = (parsed["row"], parsed["col"])
    confidence = parsed.get("confidence", "low")
    note = parsed.get("note", "")

    if previous_belief is not None and previous_belief.estimate is not None:
        reach = _chebyshev_distance(previous_belief.estimate, estimate)
        if reach > moves_elapsed:
            confidence = "low"
            note = (f"flagged implausible: claims a move of {reach} cells in "
                     f"{moves_elapsed} turn(s) since the last estimate "
                     f"{previous_belief.estimate} — trusting the claim less, "
                     f"not discarding it. ({note})" if note else
                     f"flagged implausible: claims a move of {reach} cells in "
                     f"{moves_elapsed} turn(s) since the last estimate "
                     f"{previous_belief.estimate}.")

    return Belief(estimate=estimate, confidence=confidence, note=note)


def make_belief_board(true_board: Board, agent: str, belief: Belief, rng=None) -> Board:
    """Build a proxy `Board` for the existing strategy modules: own position
    and barriers are real (always known to oneself), the opponent's position
    is the believed estimate rather than the true one.

    With no estimate yet, falls back to a "no information" guess rather
    than leaking the true position. If `rng` is given, that guess is a
    fresh random cell each call — re-rolled every turn there's no real
    signal, so a distance-maximizing/minimizing strategy reading this board
    doesn't lock onto one fixed point. (A *fixed* fallback, e.g. always the
    grid center, makes a "maximize distance from the fallback" strategy
    degenerate into oscillating between the same one or two farthest cells
    every time — a predictable pattern an opponent could learn to exploit.)
    Without `rng` (e.g. callers that don't have one), keeps the original
    deterministic grid-center fallback.
    """
    proxy = Board((true_board.rows, true_board.cols), true_board.max_barriers)
    proxy.barriers = true_board.barriers
    proxy.barriers_placed = true_board.barriers_placed

    own_pos = true_board.cop_pos if agent == "cop" else true_board.thief_pos

    if belief.estimate is not None:
        opponent_pos = belief.estimate
    elif rng is not None:
        opponent_pos = (rng.randrange(true_board.rows), rng.randrange(true_board.cols))
    else:
        opponent_pos = (true_board.rows // 2, true_board.cols // 2)

    if agent == "cop":
        proxy.cop_pos, proxy.thief_pos = own_pos, opponent_pos
    else:
        proxy.thief_pos, proxy.cop_pos = own_pos, opponent_pos
    return proxy
