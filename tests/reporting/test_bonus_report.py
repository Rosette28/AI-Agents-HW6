"""Phase 7 bonus report assembly: two swapped-role halves merge into one
Inter-Group Bonus Game JSON, with points correctly rolled up to *team*
names rather than just "cop"/"thief" (since roles swap between halves).
"""

from src.reporting.bonus_report import build_bonus_game_json
from src.reporting.bonus_schema import validate_bonus_game_json


def _team(name: str) -> dict:
    return {
        "name": name, "students": [f"{name} Student"],
        "github_repo": f"https://github.com/{name}/repo",
        "cop_mcp_url": f"https://cop-{name}.example.com", "thief_mcp_url": f"https://thief-{name}.example.com",
    }


def _half_result(cop_points: int, thief_points: int) -> dict:
    return {
        "totals": {"cop": cop_points, "thief": thief_points},
        "sub_games": [{
            "winner": "cop" if cop_points > thief_points else "thief", "moves_taken": 5,
            "final_cop_pos": (0, 0), "final_thief_pos": (0, 0), "barriers_placed": 0,
            "cop_points": cop_points, "thief_points": thief_points,
            "transcript": [{"agent": "thief", "action": {}, "message": "hi"}],
        }],
    }


def test_points_roll_up_to_team_names_across_swapped_roles():
    our_team, partner_team = _team("OurTeam"), _team("PartnerTeam")
    # Half 1: we play Cop (60 pts), partner plays Thief (15 pts).
    half_1 = _half_result(cop_points=60, thief_points=15)
    # Half 2 (roles swapped): partner plays Cop (40 pts), we play Thief (30 pts).
    half_2 = _half_result(cop_points=40, thief_points=30)

    payload = build_bonus_game_json(our_team, partner_team, half_1, half_2, "cop", "Asia/Jerusalem")

    # Our total: 60 (half 1, as Cop) + 30 (half 2, as Thief) = 90.
    # Partner total: 15 (half 1, as Thief) + 40 (half 2, as Cop) = 55.
    assert payload["totals_by_group"] == {"OurTeam": 90, "PartnerTeam": 55}


def test_sub_games_are_trimmed_summaries_not_full_transcripts():
    our_team, partner_team = _team("OurTeam"), _team("PartnerTeam")
    half_1 = _half_result(20, 5)
    half_2 = _half_result(5, 20)
    payload = build_bonus_game_json(our_team, partner_team, half_1, half_2, "cop", "Asia/Jerusalem")

    assert len(payload["sub_games"]) == 2
    for sub_game in payload["sub_games"]:
        assert "transcript" not in sub_game


def test_output_matches_schema_once_bonus_claim_and_agreement_are_filled():
    our_team, partner_team = _team("OurTeam"), _team("PartnerTeam")
    half_1 = _half_result(20, 5)
    half_2 = _half_result(5, 20)
    payload = build_bonus_game_json(our_team, partner_team, half_1, half_2, "thief", "Asia/Jerusalem")

    payload["bonus_claim"] = {"OurTeam": 5, "PartnerTeam": 5}
    payload["mutual_agreement"] = True
    validate_bonus_game_json(payload)  # raises on failure


def test_group_metadata_assigned_to_correct_slots():
    our_team, partner_team = _team("OurTeam"), _team("PartnerTeam")
    half_1 = _half_result(20, 5)
    half_2 = _half_result(5, 20)
    payload = build_bonus_game_json(our_team, partner_team, half_1, half_2, "cop", "Asia/Jerusalem")

    assert payload["groups"] == {"group_1": "OurTeam", "group_2": "PartnerTeam"}
    assert payload["github_repo_group_1"] == our_team["github_repo"]
    assert payload["github_repo_group_2"] == partner_team["github_repo"]
    assert payload["mcp_url_group_1_cop"] == our_team["cop_mcp_url"]
    assert payload["mcp_url_group_2_thief"] == partner_team["thief_mcp_url"]
