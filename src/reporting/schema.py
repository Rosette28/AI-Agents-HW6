"""Validates a payload against the Internal Game JSON schema
(hw06_requirements.md S11.1) before it is ever sent — this is the entire
email body, so a malformed payload here means a malformed submission.
"""

_REQUIRED_FIELDS: dict[str, type] = {
    "group_name": str,
    "students": list,
    "github_repo": str,
    "cop_mcp_url": str,
    "thief_mcp_url": str,
    "timezone": str,
    "sub_games": list,
    "totals": dict,
}


class SchemaError(ValueError):
    """Raised when a payload doesn't match the Internal Game JSON schema."""


def validate_internal_game_json(payload: dict) -> None:
    """Raise `SchemaError` if `payload` is missing a required key, has the
    wrong type for one, or has a malformed `totals` block. Returns None
    (valid) otherwise.
    """
    for key, expected_type in _REQUIRED_FIELDS.items():
        if key not in payload:
            raise SchemaError(f"missing required key: {key!r}")
        if not isinstance(payload[key], expected_type):
            raise SchemaError(
                f"{key!r} must be {expected_type.__name__}, got {type(payload[key]).__name__}"
            )

    totals = payload["totals"]
    for side in ("cop", "thief"):
        if side not in totals:
            raise SchemaError(f"totals is missing {side!r}")
        if not isinstance(totals[side], int) or isinstance(totals[side], bool):
            raise SchemaError(f"totals[{side!r}] must be an int, got {type(totals[side]).__name__}")
