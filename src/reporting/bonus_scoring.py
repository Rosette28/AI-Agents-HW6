"""Bonus-series scoring (hw06_requirements.md S12.2): win = 10 points,
lose = 7, exact tie = 5 each; final bonus = average across all valid
series if playing multiple partner groups.

Phase 7 (bonus inter-group competition) only — not part of the mandatory
submission.
"""

WIN_POINTS = 10
LOSE_POINTS = 7
TIE_POINTS = 5


def is_draw(totals_by_group: dict[str, int]) -> bool:
    """True when every team's total is equal — the lose-lose 5/5 outcome
    `scripts/run_bonus_series.py` retries the whole series for (up to
    `config.yaml: bonus.max_draw_retries` times), since neither side gains
    anything from a tie.
    """
    return len(set(totals_by_group.values())) == 1


def compute_bonus_claim(totals_by_group: dict[str, int]) -> dict[str, int]:
    """`totals_by_group` maps each team name to its accumulated points
    across the full 6-sub-game bonus series (both swapped-role halves).
    Returns the bonus-points claim per team — exactly two teams expected.
    """
    if len(totals_by_group) != 2:
        raise ValueError(f"expected exactly 2 teams, got {len(totals_by_group)}: {totals_by_group!r}")

    (team_a, score_a), (team_b, score_b) = totals_by_group.items()
    if score_a == score_b:
        return {team_a: TIE_POINTS, team_b: TIE_POINTS}
    if score_a > score_b:
        return {team_a: WIN_POINTS, team_b: LOSE_POINTS}
    return {team_a: LOSE_POINTS, team_b: WIN_POINTS}


def average_bonus_score(team_name: str, claims: list[dict[str, int]]) -> float:
    """Final bonus score for `team_name`: the mean of its claim across
    every valid series played (one `compute_bonus_claim` result per
    partner group). A series with a result mismatch between the two
    groups' reports is disqualified (0 points for that series, per
    S12.2) and should not be included in `claims` at all — exclude it
    before calling this, rather than passing a 0 to be averaged in.
    """
    if not claims:
        raise ValueError("no valid series to average — at least one is required")
    scores = [claim[team_name] for claim in claims]
    return sum(scores) / len(scores)
