"""Assembles the Internal Game JSON (hw06_requirements.md S11.1) from a
completed series result. This module is the only place that knows the
exact report schema — src.agents and src.engine stay agnostic of it, per
docs/PROMPTS.md's separation-of-concerns rule.
"""

# Fields kept per sub-game in the emailed report. The official example
# (hw06_requirements.md S11.1) shows "sub_games": [] with no per-entry
# schema given, and the only stated content requirement is that the email
# body is *just* the JSON, not free text — there's no requirement to embed
# the full per-turn NL transcript in the email itself. Full transcripts
# are still produced and kept as evidence (results/transcripts/*.txt,
# linked from the README per S11's documentation requirements); the email
# carries only the summary fields below, so it stays a reasonable size
# regardless of how many turns a sub-game took.
_SUB_GAME_SUMMARY_FIELDS = (
    "winner", "moves_taken", "final_cop_pos", "final_thief_pos",
    "barriers_placed", "cop_points", "thief_points",
)


def summarize_sub_game(sub_game: dict) -> dict:
    return {field: sub_game[field] for field in _SUB_GAME_SUMMARY_FIELDS if field in sub_game}


def build_internal_game_json(series_result: dict, config: dict) -> dict:
    """`series_result` is the dict returned by
    `src.agents.orchestrator.run_series_via_mcp` (or
    `src.engine.game.run_game_series`): `{"totals": ..., "sub_games": [...]}`.
    `config` is the loaded `config/config.yaml` dict — group metadata lives
    under `config["group"]`, deployed URLs under `config["mcp"]`.

    Each `sub_games` entry is trimmed to summary fields only (see
    `_SUB_GAME_SUMMARY_FIELDS`) — the full per-turn transcript (`"action"`,
    `"message"`, `"belief"`, etc. for every move) is dropped from the
    *emailed* payload, since it isn't part of the official schema and
    makes the email impractically long on a real run.
    """
    group = config.get("group", {})
    mcp = config["mcp"]
    return {
        "group_name": group.get("group_name", ""),
        "students": group.get("students", []),
        "github_repo": group.get("github_repo", ""),
        "cop_mcp_url": mcp.get("cop_mcp_url", ""),
        "thief_mcp_url": mcp.get("thief_mcp_url", ""),
        "timezone": config.get("timezone", "Asia/Jerusalem"),
        "sub_games": [summarize_sub_game(sg) for sg in series_result["sub_games"]],
        "totals": series_result["totals"],
    }
