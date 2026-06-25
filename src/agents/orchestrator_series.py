"""Series-level control flow on top of `src.agents.orchestrator`: scoring a
sub-game's winner, voiding and retrying a sub-game on technical failure,
and accumulating totals across a full series.

Re-exported from `orchestrator` so `run_series_via_mcp` keeps the same
import path; calls `orchestrator.run_subgame_via_mcp` via the module
object (not a direct function import, and imported lazily inside the
function rather than at module level — `orchestrator.py` re-exports
*this* module's `run_series_via_mcp` at its own bottom, so a top-level
`from src.agents import orchestrator` here would be a real circular
import whenever something imports `orchestrator_series` directly, e.g.
`src.agents.bonus_peer_half`) so that tests which monkeypatch
`orchestrator.run_subgame_via_mcp` are honored here too.
"""

import random

from src.strategy.heuristic import heuristic_candidate_actions


def score_subgame(winner: str, scoring: dict) -> tuple[int, int]:
    if winner == "cop":
        return scoring["cop_win"], scoring["thief_loss"]
    return scoring["cop_loss"], scoring["thief_win"]


async def _run_subgame_with_technical_loss_retry(
    grid_size, max_moves, max_barriers, cop_pos, thief_pos, rng, policy_fn, llm_client,
    visibility_radius, on_turn, max_retries: int, technical_losses: list, subgame_index: int,
    cop_endpoint: dict | None = None, thief_endpoint: dict | None = None,
) -> dict:
    """Per docs/prd/email-reporting.md's Technical Loss handling: any
    exception out of `run_subgame_via_mcp` (MCP server unreachable,
    malformed tool response, etc. — a normal game outcome never raises,
    see `orchestrator_actions.act`'s structured "no_legal_action" return)
    voids that attempt and retries the *same* sub-game, up to `max_retries`
    times, so the series still ends with exactly `num_games` valid
    sub-games.
    """
    from src.agents import orchestrator  # local import — see module docstring

    for attempt in range(1, max_retries + 2):
        try:
            return await orchestrator.run_subgame_via_mcp(
                grid_size, max_moves, max_barriers, cop_pos, thief_pos,
                rng, policy_fn, llm_client, visibility_radius, on_turn,
                cop_endpoint, thief_endpoint,
            )
        except Exception as exc:
            technical_losses.append({"sub_game_index": subgame_index, "attempt": attempt, "reason": str(exc)})
            if attempt > max_retries:
                raise RuntimeError(
                    f"sub-game {subgame_index} hit a technical failure {attempt} times in a row — giving up"
                ) from exc


async def run_series_via_mcp(grid_size: tuple, max_moves: int, num_games: int, max_barriers: int,
                              scoring: dict, start_positions_fn, seed: int | None = None,
                              policy_fn=heuristic_candidate_actions, llm_client=None,
                              visibility_radius: int = 2, on_turn=None,
                              max_technical_retries: int = 2,
                              cop_endpoint: dict | None = None,
                              thief_endpoint: dict | None = None) -> dict:
    """Run a full series of `num_games` sub-games through the MCP chain and
    accumulate totals, mirroring src/engine/game.run_game_series. A
    technical failure mid-sub-game is voided and retried in place (see
    `_run_subgame_with_technical_loss_retry`) rather than corrupting or
    truncating the series; `technical_losses` in the return value logs any
    such retries for grading evidence. `cop_endpoint`/`thief_endpoint`
    (see `run_subgame_via_mcp`) default to `None` (local in-process
    servers); pass `{"url": ..., "token": ...}` for either to run the
    whole series against an already-deployed remote server instead.
    """
    rng = random.Random(seed)
    cop_total = thief_total = 0
    sub_games = []
    technical_losses: list[dict] = []
    for index in range(1, num_games + 1):
        cop_pos, thief_pos = start_positions_fn(grid_size)
        result = await _run_subgame_with_technical_loss_retry(
            grid_size, max_moves, max_barriers, cop_pos, thief_pos, rng, policy_fn, llm_client,
            visibility_radius, on_turn, max_technical_retries, technical_losses, index,
            cop_endpoint, thief_endpoint,
        )
        cop_points, thief_points = score_subgame(result["winner"], scoring)
        result["cop_points"], result["thief_points"] = cop_points, thief_points
        cop_total += cop_points
        thief_total += thief_points
        sub_games.append(result)
    return {
        "totals": {"cop": cop_total, "thief": thief_total},
        "sub_games": sub_games,
        "technical_losses": technical_losses,
    }
