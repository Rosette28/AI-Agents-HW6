"""Tests for random start-position generation."""

import pytest

from src.engine.start_positions import random_start_positions


def test_positions_are_distinct_and_in_bounds():
    cop_pos, thief_pos = random_start_positions((3, 4))
    assert cop_pos != thief_pos
    assert 0 <= cop_pos[0] < 3 and 0 <= cop_pos[1] < 4
    assert 0 <= thief_pos[0] < 3 and 0 <= thief_pos[1] < 4


def test_raises_on_grid_too_small():
    with pytest.raises(ValueError):
        random_start_positions((1, 1))
