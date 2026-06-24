"""Dialogue tests: deception-level distribution sanity check, and message
generation (LLM mocked — no real API calls).
"""

import random
from unittest.mock import MagicMock

from src.agents.belief import Belief
from src.agents.dialogue import choose_deception_level, generate_nl_message


def test_thief_bluffs_more_often_than_cop():
    rng = random.Random(42)
    cop_levels = [choose_deception_level("cop", rng) for _ in range(2000)]
    thief_levels = [choose_deception_level("thief", rng) for _ in range(2000)]
    cop_mislead_rate = cop_levels.count("mislead") / len(cop_levels)
    thief_mislead_rate = thief_levels.count("mislead") / len(thief_levels)
    assert thief_mislead_rate > cop_mislead_rate


def test_choose_deception_level_only_returns_known_levels():
    rng = random.Random(1)
    for _ in range(50):
        assert choose_deception_level("cop", rng) in {"truthful", "vague", "mislead"}
        assert choose_deception_level("thief", rng) in {"truthful", "vague", "mislead"}


def test_generate_nl_message_returns_llm_text():
    llm_client = MagicMock()
    llm_client.generate_text.return_value = "I'm staying close to the wall."
    belief = Belief(estimate=None, confidence="none", note="no information yet")
    action = {"type": "move", "direction": "N"}

    message = generate_nl_message(
        "cop", belief, action, "vague", llm_client,
        grid_size=(5, 5), barriers_remaining=3, max_barriers=5, max_moves=25,
        visibility_radius=2,
    )
    assert message == "I'm staying close to the wall."
    llm_client.generate_text.assert_called_once()


def test_generate_nl_message_falls_back_on_llm_failure():
    llm_client = MagicMock()
    llm_client.generate_text.return_value = None
    belief = Belief(estimate=None, confidence="none", note="no information yet")
    action = {"type": "place_barrier"}

    message = generate_nl_message(
        "cop", belief, action, "truthful", llm_client,
        grid_size=(5, 5), barriers_remaining=3, max_barriers=5, max_moves=25,
        visibility_radius=2,
    )
    assert message == "cop placed a barrier."
