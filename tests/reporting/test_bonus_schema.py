"""Phase 7 bonus schema validation (hw06_requirements.md S11.2): each
specific corruption must be individually rejected, proving the check is
meaningful rather than a rubber stamp.
"""

import pytest

from src.reporting.bonus_schema import BonusSchemaError, validate_bonus_game_json


def _valid_payload() -> dict:
    return {
        "report_type": "bonus_game",
        "groups": {"group_1": "Team-Alpha", "group_2": "Team-Beta"},
        "github_repo_group_1": "https://github.com/team-alpha/marl-copthief",
        "github_repo_group_2": "https://github.com/team-beta/marl-copthief",
        "mcp_url_group_1_cop": "https://cop-mcp-alpha.example.com",
        "mcp_url_group_1_thief": "https://thief-mcp-alpha.example.com",
        "mcp_url_group_2_cop": "https://cop-mcp-beta.example.com",
        "mcp_url_group_2_thief": "https://thief-mcp-beta.example.com",
        "timezone": "Asia/Jerusalem",
        "students_group_1": ["Jane Doe"],
        "students_group_2": ["John Roe"],
        "sub_games": [{"winner": "cop", "moves_taken": 5}],
        "totals_by_group": {"Team-Alpha": 60, "Team-Beta": 80},
        "bonus_claim": {"Team-Alpha": 7, "Team-Beta": 10},
        "mutual_agreement": True,
    }


def test_well_formed_payload_passes():
    validate_bonus_game_json(_valid_payload())  # raises on failure


def test_missing_key_rejected():
    payload = _valid_payload()
    del payload["mutual_agreement"]
    with pytest.raises(BonusSchemaError):
        validate_bonus_game_json(payload)


def test_wrong_report_type_rejected():
    payload = _valid_payload()
    payload["report_type"] = "internal_game"
    with pytest.raises(BonusSchemaError):
        validate_bonus_game_json(payload)


def test_totals_by_group_keys_must_match_team_names():
    payload = _valid_payload()
    payload["totals_by_group"] = {"Team-Alpha": 60, "Some-Other-Team": 80}
    with pytest.raises(BonusSchemaError):
        validate_bonus_game_json(payload)


def test_bonus_claim_non_int_value_rejected():
    payload = _valid_payload()
    payload["bonus_claim"] = {"Team-Alpha": 7, "Team-Beta": "10"}
    with pytest.raises(BonusSchemaError):
        validate_bonus_game_json(payload)


def test_mutual_agreement_wrong_type_rejected():
    payload = _valid_payload()
    payload["mutual_agreement"] = "true"
    with pytest.raises(BonusSchemaError):
        validate_bonus_game_json(payload)
