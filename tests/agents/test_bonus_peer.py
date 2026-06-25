"""Phase 7 bonus peer protocol tests: two genuinely separate in-process
MCP servers, with TWO concurrent `run_subgame_as_peer` calls each driving
only one side — exactly mirroring how two real groups would each run
their own process simultaneously (mirrors how
`tests/mcp_servers/test_pipeline.py` tests the base game, just doubled,
since there's no single shared orchestrator here anymore). A test that
only drove one side would hang forever waiting for a move nobody ever
submits — that was the bug this whole redesign exists to fix.
"""

import asyncio
import random
from unittest.mock import MagicMock

import pytest

from src.agents import bonus_peer
from src.agents.bonus_peer import wait_for_opponent_move
from src.agents.bonus_peer_half import run_bonus_half_as_peer
from src.agents.bonus_peer_subgame import run_subgame_as_peer
from src.mcp_servers.cop_server import build_cop_server
from src.mcp_servers.session import AgentSession
from src.mcp_servers.thief_server import build_thief_server

_GRID = (3, 3)


@pytest.fixture(autouse=True)
def _fast_polling(monkeypatch):
    """Both sides run concurrently in the same event loop here (no real
    network), so the real 2s poll interval would make these tests
    needlessly slow — shrink it for speed only.
    """
    monkeypatch.setattr(bonus_peer, "POLL_INTERVAL_SECONDS", 0.01)
    monkeypatch.setattr(bonus_peer, "MAX_WAIT_SECONDS", 5.0)


def _fake_llm_client():
    client = MagicMock()
    client.generate_text.return_value = "Sticking to my plan."
    client.generate_json.return_value = {"row": None, "col": None, "confidence": "none", "note": "nothing reliable"}
    return client


def _server_endpoint(role: str, max_barriers: int = 0):
    session = AgentSession(role, _GRID, max_moves=25, max_barriers=max_barriers, visibility_radius=5)
    server = (build_cop_server if role == "cop" else build_thief_server)(session)
    return {"url": server, "token": None}


def test_subgame_as_peer_terminates_with_a_winner_for_both_sides_in_lockstep():
    cop_endpoint = _server_endpoint("cop", max_barriers=5)
    thief_endpoint = _server_endpoint("thief")

    async def _run_both():
        return await asyncio.gather(
            run_subgame_as_peer("cop", cop_endpoint, thief_endpoint, _fake_llm_client(),
                                 _GRID, max_moves=25, max_barriers=5, visibility_radius=5,
                                 my_start_pos=(0, 0), rng=random.Random(2)),
            run_subgame_as_peer("thief", thief_endpoint, cop_endpoint, _fake_llm_client(),
                                 _GRID, max_moves=25, max_barriers=5, visibility_radius=5,
                                 my_start_pos=(2, 2), rng=random.Random(1)),
        )

    cop_view, thief_view = asyncio.run(_run_both())

    assert cop_view["winner"] in {"cop", "thief"}
    # Both sides observed the same shared reality, so they must agree.
    assert cop_view["winner"] == thief_view["winner"]
    assert cop_view["moves_taken"] == thief_view["moves_taken"]
    assert cop_view["transcript"] and thief_view["transcript"]


def test_bonus_half_as_peer_accumulates_points_across_sub_games():
    cop_endpoint = _server_endpoint("cop", max_barriers=5)
    thief_endpoint = _server_endpoint("thief")
    scoring = {"cop_win": 20, "thief_win": 10, "cop_loss": 5, "thief_loss": 5}

    async def _run_both_halves():
        return await asyncio.gather(
            run_bonus_half_as_peer("cop", cop_endpoint, thief_endpoint, _fake_llm_client(),
                                    _GRID, max_moves=25, max_barriers=5, scoring=scoring, visibility_radius=5,
                                    num_sub_games=2, series_seed="test-seed", half_index=1),
            run_bonus_half_as_peer("thief", thief_endpoint, cop_endpoint, _fake_llm_client(),
                                    _GRID, max_moves=25, max_barriers=5, scoring=scoring, visibility_radius=5,
                                    num_sub_games=2, series_seed="test-seed", half_index=1),
        )

    cop_half, thief_half = asyncio.run(_run_both_halves())

    assert len(cop_half["sub_games"]) == 2
    assert cop_half["totals"] == thief_half["totals"], "both sides observed the same shared games"
    expected_cop = sum(g["cop_points"] for g in cop_half["sub_games"])
    expected_thief = sum(g["thief_points"] for g in cop_half["sub_games"])
    assert cop_half["totals"] == {"cop": expected_cop, "thief": expected_thief}


def test_wait_for_opponent_move_returns_once_a_new_message_arrives():
    class _FakeClient:
        def __init__(self):
            self.calls = 0

        async def call_tool(self, name):
            self.calls += 1
            response = MagicMock()
            response.data = {"from": "cop", "text": "hi", "turn": 0} if self.calls >= 2 else None
            return response

    result = asyncio.run(wait_for_opponent_move(_FakeClient(), last_seen=None))
    assert result == {"from": "cop", "text": "hi", "turn": 0}
