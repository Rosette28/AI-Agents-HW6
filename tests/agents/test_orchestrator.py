"""Phase 4 orchestrator tests: the LLM-driven pipeline (belief update +
NL message generation) terminates with a winner and produces transcript
entries carrying belief/message fields. The LLM client is always mocked —
no real API calls.
"""

import asyncio
import random
from unittest.mock import MagicMock

import pytest

from src.agents import orchestrator
from src.engine.start_positions import random_start_positions
from src.agents.orchestrator import run_series_via_mcp, run_subgame_via_mcp


def _fake_llm_client():
    client = MagicMock()
    client.generate_text.return_value = "Sticking to my plan."
    client.generate_json.return_value = {"row": None, "col": None, "confidence": "none", "note": "nothing reliable"}
    return client


def test_llm_driven_subgame_terminates_with_a_winner_and_logs_belief_and_message():
    llm_client = _fake_llm_client()
    result = asyncio.run(
        run_subgame_via_mcp((3, 3), max_moves=25, max_barriers=5, cop_pos=(0, 0), thief_pos=(2, 2),
                             rng=random.Random(3), llm_client=llm_client, visibility_radius=2)
    )
    assert result["winner"] in {"cop", "thief"}
    first_turn = result["transcript"][0]
    assert first_turn["message"] == "Sticking to my plan."
    assert "belief" in first_turn
    assert first_turn["belief"]["confidence"] in {"high", "low", "none"}


def test_on_turn_callback_receives_a_snapshot_each_turn():
    llm_client = _fake_llm_client()
    snapshots = []
    asyncio.run(
        run_subgame_via_mcp((1, 2), max_moves=5, max_barriers=5, cop_pos=(0, 0), thief_pos=(0, 1),
                             rng=random.Random(7), llm_client=llm_client, visibility_radius=2,
                             on_turn=snapshots.append)
    )
    assert snapshots, "expected at least one snapshot"
    snap = snapshots[0]
    assert {"rows", "cols", "cop_pos", "thief_pos", "barriers", "beliefs", "last_messages"} <= snap.keys()


def test_legacy_path_without_llm_client_keeps_fixed_template_message():
    result = asyncio.run(
        run_subgame_via_mcp((1, 2), max_moves=25, max_barriers=5, cop_pos=(0, 0), thief_pos=(0, 1),
                             rng=random.Random(7))
    )
    first_turn = result["transcript"][0]
    assert "belief" not in first_turn
    assert first_turn["message"] in {"thief moved N.", "thief moved S.", "thief moved E.", "thief moved W.",
                                      "thief moved NE.", "thief moved NW.", "thief moved SE.", "thief moved SW."}


_SCORING = {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5}


def test_technical_loss_is_voided_and_retried_without_corrupting_the_series(monkeypatch):
    """Phase 5: a sub-game that fails technically (MCP unreachable, etc.)
    must be voided and re-run in place — the series still ends with
    exactly `num_games` valid sub-games, not a duplicate or a gap."""
    calls = {"count": 0}

    async def flaky_run_subgame(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise ConnectionError("mcp server unreachable")
        return {"winner": "cop", "moves_taken": 1, "transcript": []}

    monkeypatch.setattr(orchestrator, "run_subgame_via_mcp", flaky_run_subgame)

    series = asyncio.run(run_series_via_mcp(
        grid_size=(3, 3), max_moves=5, num_games=2, max_barriers=5,
        scoring=_SCORING, start_positions_fn=random_start_positions, seed=1,
    ))

    assert len(series["sub_games"]) == 2
    assert len(series["technical_losses"]) == 1
    assert series["technical_losses"][0]["sub_game_index"] == 1
    assert calls["count"] == 3  # 1 failed attempt on sub-game 1 + 2 successful sub-games


def test_persistent_technical_failure_gives_up_after_max_retries(monkeypatch):
    async def always_fails(*args, **kwargs):
        raise ConnectionError("mcp server unreachable")

    monkeypatch.setattr(orchestrator, "run_subgame_via_mcp", always_fails)

    with pytest.raises(RuntimeError, match="technical failure"):
        asyncio.run(run_series_via_mcp(
            grid_size=(3, 3), max_moves=5, num_games=1, max_barriers=5,
            scoring=_SCORING, start_positions_fn=random_start_positions, seed=1,
            max_technical_retries=2,
        ))
