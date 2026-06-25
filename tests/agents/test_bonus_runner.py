"""Phase 7 bonus runner test: one attempt plays two swapped-role halves
(mocking `run_bonus_half_as_peer` so no real network/LLM calls happen) and
the resulting payload rolls points up to team names correctly. Each half
is now played by our own independent peer process (see
`src.agents.bonus_peer`'s module docstring) rather than a single shared
orchestrator driving both sides — this test mocks at that boundary.
"""

import asyncio
from unittest.mock import AsyncMock, patch

from src.agents.bonus_runner import run_one_bonus_attempt


def _config() -> dict:
    return {
        "board": {"grid_size": [5, 5]}, "game": {"max_moves": 25, "max_barriers": 5},
        "scoring": {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5},
        "observation": {"visibility_radius": 2},
        "llm": {"provider": "anthropic", "model": "claude-haiku-4-5-20251001"},
        "mcp": {"cop_mcp_url": "https://our-cop.example.com", "thief_mcp_url": "https://our-thief.example.com"},
        "bonus": {"sub_games_per_half": 3},
        "timezone": "Asia/Jerusalem",
    }


def _team(name: str) -> dict:
    return {
        "name": name, "students": [], "github_repo": f"https://github.com/{name}/repo",
        "cop_mcp_url": f"https://cop-{name}.example.com", "thief_mcp_url": f"https://thief-{name}.example.com",
    }


def test_one_attempt_rolls_points_up_to_team_names():
    half_results = [
        {"totals": {"cop": 60, "thief": 15}, "sub_games": []},  # half 1: we=cop
        {"totals": {"cop": 40, "thief": 30}, "sub_games": []},  # half 2: partner=cop, we=thief
    ]
    mock_half = AsyncMock(side_effect=half_results)

    with patch("src.agents.bonus_runner.run_bonus_half_as_peer", mock_half):
        payload = asyncio.run(run_one_bonus_attempt(
            "cop", "https://partner-cop.example.com", "partner-cop-token",
            "https://partner-thief.example.com", "partner-thief-token",
            _team("OurTeam"), _team("PartnerTeam"), _config(), series_seed="agreed-seed",
        ))

    assert mock_half.call_count == 2
    assert payload["totals_by_group"] == {"OurTeam": 90, "PartnerTeam": 55}
    assert payload["bonus_claim"] == {"OurTeam": 10, "PartnerTeam": 7}
    assert "mutual_agreement" not in payload or payload["mutual_agreement"] is False


def test_role_swap_uses_partner_endpoint_for_half_1_when_we_start_as_thief():
    half_results = [
        {"totals": {"cop": 20, "thief": 5}, "sub_games": []},
        {"totals": {"cop": 5, "thief": 20}, "sub_games": []},
    ]
    mock_half = AsyncMock(side_effect=half_results)

    with patch("src.agents.bonus_runner.run_bonus_half_as_peer", mock_half):
        asyncio.run(run_one_bonus_attempt(
            "thief", "https://partner-cop.example.com", "partner-cop-token",
            "https://partner-thief.example.com", "partner-thief-token",
            _team("OurTeam"), _team("PartnerTeam"), _config(), series_seed="agreed-seed",
        ))

    first_call_args = mock_half.call_args_list[0].args
    # run_bonus_half_as_peer(my_role, my_endpoint, partner_endpoint, ...)
    assert first_call_args[0] == "thief"
    assert first_call_args[1]["url"] == "https://our-thief.example.com"
    assert first_call_args[2]["url"] == "https://partner-cop.example.com"
