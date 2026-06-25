"""Assembles the Inter-Group Bonus Game JSON (hw06_requirements.md S11.2)
from two swapped-role halves of a bonus series.

Phase 7 (bonus inter-group competition) only — not part of the mandatory
submission; `scripts/run_bonus_series.py` is the one caller. Reuses
`src.reporting.game_report`'s per-sub-game summary trim (same reasoning:
the official schema example shows an empty `sub_games` list and the
report's stated purpose is automated grading intake, not a transcript
dump — see `docs/PLAN.md` ADR-7).
"""

from src.reporting.game_report import summarize_sub_game


def _half_totals_by_team(half_result: dict, cop_team: str, thief_team: str) -> dict[str, int]:
    totals = half_result["totals"]
    return {cop_team: totals["cop"], thief_team: totals["thief"]}


def build_bonus_game_json(
    our_team: dict, partner_team: dict,
    half_1_result: dict, half_2_result: dict,
    our_role_in_half_1: str, timezone: str,
) -> dict:
    """`our_team`/`partner_team`: `{"name", "students", "github_repo",
    "cop_mcp_url", "thief_mcp_url"}` for each side. `half_1_result`/
    `half_2_result` are `run_series_via_mcp`-shaped results (3 sub-games
    each): half 1 has `our_role_in_half_1` ("cop" or "thief") played by
    our team, half 2 has the roles swapped. Team order in the output
    (`group_1` = our team, `group_2` = partner) is fixed for readability;
    it carries no scoring meaning since `totals_by_group`/`bonus_claim`
    are keyed by team name, not by group slot.
    """
    our_role_2 = "thief" if our_role_in_half_1 == "cop" else "cop"

    if our_role_in_half_1 == "cop":
        half_1_teams = (our_team["name"], partner_team["name"])  # (cop, thief)
        half_2_teams = (partner_team["name"], our_team["name"])  # (cop, thief)
    else:
        half_1_teams = (partner_team["name"], our_team["name"])
        half_2_teams = (our_team["name"], partner_team["name"])

    totals_1 = _half_totals_by_team(half_1_result, *half_1_teams)
    totals_2 = _half_totals_by_team(half_2_result, *half_2_teams)
    totals_by_group = {
        our_team["name"]: totals_1[our_team["name"]] + totals_2[our_team["name"]],
        partner_team["name"]: totals_1[partner_team["name"]] + totals_2[partner_team["name"]],
    }

    sub_games = [summarize_sub_game(sg) for sg in half_1_result["sub_games"]]
    sub_games += [summarize_sub_game(sg) for sg in half_2_result["sub_games"]]

    return {
        "report_type": "bonus_game",
        "groups": {"group_1": our_team["name"], "group_2": partner_team["name"]},
        "github_repo_group_1": our_team["github_repo"],
        "github_repo_group_2": partner_team["github_repo"],
        "mcp_url_group_1_cop": our_team["cop_mcp_url"],
        "mcp_url_group_1_thief": our_team["thief_mcp_url"],
        "mcp_url_group_2_cop": partner_team["cop_mcp_url"],
        "mcp_url_group_2_thief": partner_team["thief_mcp_url"],
        "timezone": timezone,
        "students_group_1": our_team["students"],
        "students_group_2": partner_team["students"],
        "sub_games": sub_games,
        "totals_by_group": totals_by_group,
        # bonus_claim/mutual_agreement are filled in by the caller
        # (scripts/run_bonus_series.py) once both sides have confirmed the
        # totals match — this builder only assembles the game data.
        "bonus_claim": {},
        "mutual_agreement": False,
    }
