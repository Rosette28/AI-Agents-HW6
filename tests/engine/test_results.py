"""Tests that sub-game results are persisted as tagged, valid JSON."""

import json

from src.engine.results import save_subgame_result


def test_save_subgame_result_writes_tagged_json(tmp_path):
    result = {
        "winner": "cop",
        "moves_taken": 3,
        "final_cop_pos": (0, 1),
        "final_thief_pos": (0, 1),
        "barriers_placed": 0,
        "transcript": [],
    }

    out_path = save_subgame_result(result, grid_size=(1, 3), subgame_index=2, results_dir=tmp_path)

    assert out_path.exists()
    with open(out_path, encoding="utf-8") as f:
        record = json.load(f)

    assert record["grid_size"] == [1, 3]
    assert record["subgame_index"] == 2
    assert record["winner"] == "cop"
    assert "recorded_at" in record
