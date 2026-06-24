"""Schema validation for the Internal Game JSON (hw06_requirements.md
S11.1) — the email body's only content, so a malformed payload must fail
loudly before anything is sent.
"""

import pytest

from src.reporting.schema import SchemaError, validate_internal_game_json


def _valid_payload() -> dict:
    return {
        "group_name": "Team-Alpha",
        "students": ["Jane Doe"],
        "github_repo": "https://github.com/team-alpha/marl-copthief",
        "cop_mcp_url": "https://cop-mcp-alpha.example.com",
        "thief_mcp_url": "https://thief-mcp-alpha.example.com",
        "timezone": "Asia/Jerusalem",
        "sub_games": [{"winner": "cop"}],
        "totals": {"cop": 90, "thief": 40},
    }


def test_well_formed_payload_passes():
    validate_internal_game_json(_valid_payload())  # raises on failure


def test_missing_required_key_is_rejected():
    payload = _valid_payload()
    del payload["github_repo"]
    with pytest.raises(SchemaError, match="github_repo"):
        validate_internal_game_json(payload)


def test_wrong_type_for_a_required_key_is_rejected():
    payload = _valid_payload()
    payload["students"] = "not-a-list"
    with pytest.raises(SchemaError, match="students"):
        validate_internal_game_json(payload)


def test_totals_missing_a_side_is_rejected():
    payload = _valid_payload()
    del payload["totals"]["thief"]
    with pytest.raises(SchemaError, match="thief"):
        validate_internal_game_json(payload)


def test_totals_with_non_int_value_is_rejected():
    payload = _valid_payload()
    payload["totals"]["cop"] = "90"
    with pytest.raises(SchemaError, match="cop"):
        validate_internal_game_json(payload)
