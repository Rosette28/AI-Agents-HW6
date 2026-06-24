"""build_internal_game_json assembles a series result + config into the
exact Internal Game JSON shape (hw06_requirements.md S11.1) — and the
result must pass schema validation, since that's what actually gets sent.
"""

from src.reporting.game_report import build_internal_game_json
from src.reporting.schema import validate_internal_game_json


def _series_result() -> dict:
    return {
        "totals": {"cop": 90, "thief": 40},
        "sub_games": [{"winner": "cop", "moves_taken": 5}],
        "technical_losses": [],
    }


def _config() -> dict:
    return {
        "group": {
            "group_name": "Team-Alpha",
            "students": ["Jane Doe"],
            "github_repo": "https://github.com/team-alpha/marl-copthief",
        },
        "mcp": {
            "cop_mcp_url": "https://cop-mcp-alpha.example.com",
            "thief_mcp_url": "https://thief-mcp-alpha.example.com",
        },
        "timezone": "Asia/Jerusalem",
    }


def test_build_internal_game_json_matches_schema_and_source_data():
    payload = build_internal_game_json(_series_result(), _config())

    validate_internal_game_json(payload)  # raises on failure
    assert payload["group_name"] == "Team-Alpha"
    assert payload["students"] == ["Jane Doe"]
    assert payload["github_repo"] == "https://github.com/team-alpha/marl-copthief"
    assert payload["cop_mcp_url"] == "https://cop-mcp-alpha.example.com"
    assert payload["thief_mcp_url"] == "https://thief-mcp-alpha.example.com"
    assert payload["timezone"] == "Asia/Jerusalem"
    assert payload["sub_games"] == _series_result()["sub_games"]
    assert payload["totals"] == {"cop": 90, "thief": 40}


def test_missing_group_section_defaults_to_blank_values_not_a_crash():
    payload = build_internal_game_json(_series_result(), {"mcp": {}, "timezone": "UTC"})

    assert payload["group_name"] == ""
    assert payload["students"] == []
    assert payload["github_repo"] == ""
    assert payload["cop_mcp_url"] == ""
    assert payload["thief_mcp_url"] == ""
