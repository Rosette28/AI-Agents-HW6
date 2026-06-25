"""Validates a payload against the Inter-Group Bonus Game JSON schema
(hw06_requirements.md S11.2, S12) before it is ever sent.

Phase 7 (bonus inter-group competition) only — not part of the mandatory
submission. Mirrors `src.reporting.schema`'s structure/strictness for the
single-group report, for the bonus report's different (team-keyed) shape.
"""

_REQUIRED_FIELDS: dict[str, type] = {
    "report_type": str,
    "groups": dict,
    "github_repo_group_1": str,
    "github_repo_group_2": str,
    "mcp_url_group_1_cop": str,
    "mcp_url_group_1_thief": str,
    "mcp_url_group_2_cop": str,
    "mcp_url_group_2_thief": str,
    "timezone": str,
    "students_group_1": list,
    "students_group_2": list,
    "sub_games": list,
    "totals_by_group": dict,
    "bonus_claim": dict,
    "mutual_agreement": bool,
}


class BonusSchemaError(ValueError):
    """Raised when a payload doesn't match the Inter-Group Bonus Game JSON schema."""


def validate_bonus_game_json(payload: dict) -> None:
    """Raise `BonusSchemaError` if `payload` is missing a required key, has
    the wrong type for one, or has a malformed team-keyed block. Returns
    None (valid) otherwise.
    """
    for key, expected_type in _REQUIRED_FIELDS.items():
        if key not in payload:
            raise BonusSchemaError(f"missing required key: {key!r}")
        if not isinstance(payload[key], expected_type):
            raise BonusSchemaError(
                f"{key!r} must be {expected_type.__name__}, got {type(payload[key]).__name__}"
            )

    if payload["report_type"] != "bonus_game":
        raise BonusSchemaError(f"report_type must be 'bonus_game', got {payload['report_type']!r}")

    groups = payload["groups"]
    for side in ("group_1", "group_2"):
        if side not in groups:
            raise BonusSchemaError(f"groups is missing {side!r}")

    team_names = set(groups.values())
    for block_name in ("totals_by_group", "bonus_claim"):
        block = payload[block_name]
        if set(block.keys()) != team_names:
            raise BonusSchemaError(
                f"{block_name} keys {set(block.keys())!r} must exactly match team names {team_names!r}"
            )
        for team, value in block.items():
            if not isinstance(value, int) or isinstance(value, bool):
                raise BonusSchemaError(f"{block_name}[{team!r}] must be an int, got {type(value).__name__}")
