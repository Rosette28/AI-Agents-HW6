"""Tests that sub-game results are persisted as tagged, valid JSON."""

import json

from src.engine.results import save_subgame_result, save_transcript_log


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


def test_save_transcript_log_writes_readable_text(tmp_path):
    result = {
        "winner": "thief",
        "transcript": [
            {"agent": "thief", "action": {"type": "move", "direction": "N"},
             "result": {"accepted": True}, "message": "Moving away cautiously.",
             "belief": {"estimate": None, "confidence": "none", "note": "no information yet"}},
            {"agent": "cop", "action": {"type": "move", "direction": "S"},
             "result": {"accepted": True}, "message": "Closing in."},
        ],
    }

    out_path = save_transcript_log(result, grid_size=(3, 3), subgame_index=1, transcripts_dir=tmp_path)

    assert out_path.exists()
    text = out_path.read_text(encoding="utf-8")
    assert "winner: thief" in text
    assert "THIEF" in text and "COP" in text
    assert "Moving away cautiously." in text
    assert "no information yet" in text
