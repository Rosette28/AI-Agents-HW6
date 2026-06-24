"""Writes the orchestrator's plain-dict turn snapshots to a JSON file the
Streamlit app (`src/gui/app.py`) polls. Decouples `src/agents/` from
`src/gui/` — the orchestrator never imports this module; callers (e.g.
`scripts/run_llm_demo.py`) wire `on_turn=lambda snap: write_live_state(path, snap)`.
"""

import json
from pathlib import Path

DEFAULT_STATE_PATH = Path(__file__).resolve().parents[2] / "results" / "live_state.json"


def write_live_state(snapshot: dict, path: Path | str = DEFAULT_STATE_PATH) -> None:
    """Overwrite the live-state file with the latest turn snapshot."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)


def read_live_state(path: Path | str = DEFAULT_STATE_PATH) -> dict | None:
    """Read the latest snapshot, or None if no run has written one yet."""
    in_path = Path(path)
    if not in_path.exists():
        return None
    with open(in_path, encoding="utf-8") as f:
        return json.load(f)
