"""Persists raw sub-game results to results/*.json. Output here is
evidence for grading — never hand-edit files this module writes.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"


def save_subgame_result(
    result: dict,
    grid_size: tuple[int, int],
    subgame_index: int,
    results_dir: Path | str | None = None,
) -> Path:
    """Write one sub-game's result as a tagged JSON file.

    Tags the record with grid size, sub-game index, and winner so raw
    results stay traceable to the scenario that produced them.
    """
    out_dir = Path(results_dir) if results_dir is not None else _DEFAULT_RESULTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    record = {
        "grid_size": list(grid_size),
        "subgame_index": subgame_index,
        "winner": result["winner"],
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        **result,
    }

    rows, cols = grid_size
    filename = f"subgame_{rows}x{cols}_{subgame_index:02d}_{result['winner']}.json"
    out_path = out_dir / filename
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, default=list)
    return out_path
