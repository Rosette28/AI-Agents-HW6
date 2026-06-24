"""Assembles the Internal Game JSON (hw06_requirements.md S11.1) from a
completed series result. This module is the only place that knows the
exact report schema — src.agents and src.engine stay agnostic of it, per
docs/PROMPTS.md's separation-of-concerns rule.
"""


def build_internal_game_json(series_result: dict, config: dict) -> dict:
    """`series_result` is the dict returned by
    `src.agents.orchestrator.run_series_via_mcp` (or
    `src.engine.game.run_game_series`): `{"totals": ..., "sub_games": [...]}`.
    `config` is the loaded `config/config.yaml` dict — group metadata lives
    under `config["group"]`, deployed URLs under `config["mcp"]`.
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
        "sub_games": series_result["sub_games"],
        "totals": series_result["totals"],
    }
