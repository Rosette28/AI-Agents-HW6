"""Phase 7 bonus scoring rules (hw06_requirements.md S12.2): win=10,
lose=7, exact tie=5 each, averaged across multiple partner series.
"""

import pytest

from src.reporting.bonus_scoring import average_bonus_score, compute_bonus_claim, is_draw


def test_is_draw_true_on_exact_tie():
    assert is_draw({"Team-Alpha": 75, "Team-Beta": 75}) is True


def test_is_draw_false_when_totals_differ():
    assert is_draw({"Team-Alpha": 90, "Team-Beta": 60}) is False


def test_higher_total_wins_ten_lower_loses_seven():
    claim = compute_bonus_claim({"Team-Alpha": 90, "Team-Beta": 60})
    assert claim == {"Team-Alpha": 10, "Team-Beta": 7}


def test_exact_tie_gives_five_each():
    claim = compute_bonus_claim({"Team-Alpha": 75, "Team-Beta": 75})
    assert claim == {"Team-Alpha": 5, "Team-Beta": 5}


def test_rejects_anything_other_than_exactly_two_teams():
    with pytest.raises(ValueError):
        compute_bonus_claim({"Team-Alpha": 90})


def test_average_bonus_score_across_multiple_partner_series():
    claims = [{"Team-Alpha": 10, "Team-Beta": 7}, {"Team-Alpha": 7, "Team-Gamma": 10}]
    assert average_bonus_score("Team-Alpha", claims) == pytest.approx(8.5)


def test_average_bonus_score_requires_at_least_one_valid_series():
    with pytest.raises(ValueError):
        average_bonus_score("Team-Alpha", [])
