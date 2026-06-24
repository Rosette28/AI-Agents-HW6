"""state_writer round-trip: write a snapshot, read it back unchanged."""

from src.gui.state_writer import read_live_state, write_live_state


def test_write_then_read_round_trips(tmp_path):
    path = tmp_path / "live_state.json"
    snapshot = {"rows": 3, "cols": 3, "cop_pos": [0, 0], "thief_pos": [2, 2],
                "barriers": [[1, 1]], "barriers_placed": 1, "move_number": 4,
                "beliefs": {"cop": {"estimate": [2, 2], "confidence": "high", "note": "visible"}},
                "last_messages": {"cop": "closing in"}}

    write_live_state(snapshot, path=path)
    loaded = read_live_state(path=path)

    assert loaded == snapshot


def test_read_returns_none_when_no_file_exists(tmp_path):
    assert read_live_state(path=tmp_path / "missing.json") is None
