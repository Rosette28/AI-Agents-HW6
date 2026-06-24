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


def save_transcript_log(
    result: dict,
    grid_size: tuple[int, int],
    subgame_index: int,
    transcripts_dir: Path | str | None = None,
) -> Path:
    """Render a Phase 4 sub-game's transcript (belief/message-carrying turns
    from `src.agents.orchestrator.run_subgame_via_mcp`) as a human-readable
    `.txt` file — this is the primary grading evidence for autonomous NL
    operation, per docs/prd/nl-dialogue.md success criteria.
    """
    out_dir = Path(transcripts_dir) if transcripts_dir is not None else _DEFAULT_RESULTS_DIR / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows, cols = grid_size
    filename = f"subgame_{rows}x{cols}_{subgame_index:02d}_{result['winner']}.txt"
    out_path = out_dir / filename

    lines = [f"Sub-game {subgame_index} on a {rows}x{cols} grid — winner: {result['winner']}", ""]
    for turn_number, turn in enumerate(result["transcript"], start=1):
        lines.append(f"--- Turn {turn_number}: {turn['agent'].upper()} ---")
        if "belief" in turn:
            belief = turn["belief"]
            lines.append(f"Belief: {belief['note']} (confidence: {belief['confidence']})")
        lines.append(f"Message: {turn.get('message', '')}")
        lines.append(f"Action: {turn.get('action')}")
        lines.append(f"Result: {turn.get('result')}")
        lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path
